#!/usr/bin/env python3
"""
DiscBot Modern Installer
Installs and configures everything except tokens/credentials (interactive step included).
Run: python setup.py
"""

from __future__ import annotations

import asyncio
import platform
import shutil
import subprocess
import sys
import urllib.request
from argparse import ArgumentParser
from pathlib import Path
from typing import Optional

# Check if we're in an interactive terminal
IS_INTERACTIVE = sys.stdin.isatty()

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

ROOT = Path(__file__).parent
VENV_DIR = ROOT / ".venv"
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
LAVALINK_DIR = ROOT / "lavalink"
LAVALINK_JAR = LAVALINK_DIR / "Lavalink.jar"
LAVALINK_YML = LAVALINK_DIR / "application.yml"
LAVALINK_PLUGINS = LAVALINK_DIR / "plugins"

LAVALINK_URL = "https://github.com/lavalink-devs/Lavalink/releases/download/4.0.8/Lavalink.jar"
LAVALINK_YML_URL = "https://raw.githubusercontent.com/lavalink-devs/Lavalink/4.0.8/LavalinkServer/application.yml.example"

CONSOLE = Console() if RICH_AVAILABLE else None


def print_header(text: str) -> None:
    if RICH_AVAILABLE:
        CONSOLE.print(Panel.fit(f"[bold cyan]{text}[/bold cyan]", border_style="cyan"))
    else:
        print(f"\n{'=' * 60}\n{text}\n{'=' * 60}")


def print_info(text: str) -> None:
    if RICH_AVAILABLE:
        CONSOLE.print(f"[cyan][i][/cyan] {text}")
    else:
        print(f"[INFO] {text}")


def print_success(text: str) -> None:
    if RICH_AVAILABLE:
        CONSOLE.print(f"[green][OK][/green] {text}")
    else:
        print(f"[OK] {text}")


def print_warning(text: str) -> None:
    if RICH_AVAILABLE:
        CONSOLE.print(f"[yellow][WARN][/yellow] {text}")
    else:
        print(f"[WARN] {text}")


def print_error(text: str) -> None:
    if RICH_AVAILABLE:
        CONSOLE.print(f"[red][ERR][/red] {text}")
    else:
        print(f"[ERROR] {text}")


def run_cmd(cmd: list[str], cwd: Optional[Path] = None, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=capture, text=True)


def check_python_version() -> bool:
    print_header("Checking Python Version")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} [OK]")
        return True
    print_error(f"Python 3.11+ required, found {version.major}.{version.minor}.{version.micro}")
    return False


def check_ffmpeg() -> bool:
    print_header("Checking FFmpeg")
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        result = run_cmd(["ffmpeg", "-version"], capture=True)
        version_line = result.stdout.split("\n")[0]
        print_success(f"FFmpeg found: {version_line}")
        return True
    print_warning("FFmpeg not found in PATH")
    print_info("Install: winget install Gyan.FFmpeg (Windows) | brew install ffmpeg (macOS) | apt install ffmpeg (Linux)")
    if not IS_INTERACTIVE:
        print_warning("Non-interactive mode: continuing without FFmpeg (music playback will fail)")
        return True
    if RICH_AVAILABLE:
        try:
            return Confirm.ask("Continue without FFmpeg? (music playback will fail)", default=False)
        except EOFError:
            print_warning("EOF received, continuing without FFmpeg")
            return True
    try:
        return input("Continue without FFmpeg? (y/N): ").lower() == 'y'
    except EOFError:
        print_warning("EOF received, continuing without FFmpeg")
        return True


def check_java() -> bool:
    print_header("Checking Java (for Lavalink)")
    java = shutil.which("java")
    if java:
        result = run_cmd(["java", "-version"], capture=True)
        version_line = result.stderr.split("\n")[0]
        if "17" in version_line or "21" in version_line:
            print_success(f"Java found: {version_line}")
            return True
        print_warning(f"Java found but not version 17/21: {version_line}")
    else:
        print_warning("Java not found in PATH")
    print_info("Install: winget install EclipseAdoptium.Temurin.17.JDK (Windows) | brew install openjdk@17 (macOS) | apt install openjdk-17-jre (Linux)")
    if not IS_INTERACTIVE:
        print_warning("Non-interactive mode: continuing without Java (Lavalink won't start)")
        return True
    if RICH_AVAILABLE:
        return Confirm.ask("Continue without Java? (Lavalink won't start)", default=True)
    return input("Continue without Java? (Y/n): ").lower() != 'n'


def check_git() -> bool:
    print_header("Checking Git")
    git = shutil.which("git")
    if git:
        print_success("Git found")
        return True
    print_warning("Git not found - some features may not work")
    if not IS_INTERACTIVE:
        return True
    return True


def create_venv() -> bool:
    print_header("Creating Virtual Environment")
    if VENV_DIR.exists():
        print_info("Virtual environment already exists")
        return True
    try:
        run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
        print_success("Virtual environment created")
        return True
    except Exception as e:
        print_error(f"Failed to create venv: {e}")
        return False


def get_pip() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def get_python() -> Path:
    if platform.system() == "Windows":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def install_dependencies() -> bool:
    print_header("Installing Python Dependencies")
    pip = get_pip()
    try:
        print_info("Upgrading pip...")
        result = run_cmd([str(pip), "install", "--upgrade", "pip"], capture=True)
        if result.returncode != 0:
            print_warning(f"pip upgrade failed (continuing): {result.stderr}")
        print_info("Installing from requirements.txt...")
        result = run_cmd([str(pip), "install", "-r", "requirements.txt"], capture=True)
        if result.returncode != 0:
            print_error(f"pip install failed:\n{result.stderr}")
            return False
        print_success("Dependencies installed")
        return True
    except Exception as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def download_lavalink() -> bool:
    print_header("Downloading Lavalink")
    LAVALINK_DIR.mkdir(parents=True, exist_ok=True)
    LAVALINK_PLUGINS.mkdir(parents=True, exist_ok=True)

    if LAVALINK_JAR.exists():
        print_info("Lavalink.jar already exists")
        return True

    try:
        print_info("Downloading Lavalink.jar...")
        urllib.request.urlretrieve(LAVALINK_URL, LAVALINK_JAR)
        print_info("Downloading application.yml...")
        urllib.request.urlretrieve(LAVALINK_YML_URL, LAVALINK_YML)
        print_success("Lavalink downloaded")
        return True
    except Exception as e:
        print_error(f"Failed to download Lavalink: {e}")
        return False


def interactive_env_setup() -> bool:
    print_header("Interactive Configuration (.env)")
    
    if not IS_INTERACTIVE:
        print_info("Non-interactive mode: creating .env with defaults")
        if ENV_EXAMPLE.exists():
            shutil.copy2(ENV_EXAMPLE, ENV_FILE)
            print_success(".env file created from defaults")
        return True

    print_info("Press Enter to keep default value (shown in brackets)")

    if not ENV_EXAMPLE.exists():
        print_error(".env.example not found!")
        return False

    env_content = ENV_EXAMPLE.read_text(encoding="utf-8")
    lines = env_content.strip().split("\n")
    new_lines = []

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            new_lines.append(line)
            continue

        if "=" not in line:
            new_lines.append(line)
            continue

        key, default = line.split("=", 1)
        key = key.strip()
        default = default.strip()

        is_secret = "SECRET" in key.upper() or "TOKEN" in key.upper() or "PASSWORD" in key.upper()
        
        if RICH_AVAILABLE:
            prompt_text = f"[cyan]{key}[/cyan]"
            if default:
                prompt_text += f" [dim](default: {default})[/dim]"
            value = Prompt.ask(prompt_text, default=default, password=is_secret)
        else:
            prompt = f"{key}"
            if default:
                prompt += f" (default: {default})"
            prompt += ": "
            value = input(prompt) or default

        new_lines.append(f"{key}={value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print_success(".env file created")
    return True


def create_start_scripts() -> bool:
    print_header("Creating Start Scripts")

    # Windows batch
    bat_content = """@echo off
REM DiscBot Windows Start Script
cd /d "%~dp0"
call .venv\\Scripts\\activate.bat
python -m bot.main
pause
"""
    (ROOT / "start_bot.bat").write_text(bat_content, encoding="utf-8")

    # Linux/Mac shell
    sh_content = """#!/bin/bash
# DiscBot Linux/macOS Start Script
cd "$(dirname "$0")"
source .venv/bin/activate
python -m bot.main
"""
    sh_path = ROOT / "start_bot.sh"
    sh_path.write_text(sh_content, encoding="utf-8")
    sh_path.chmod(0o755)

    # Lavalink start script
    lavalink_bat = """@echo off
REM Lavalink Windows Start Script
cd /d "%~dp0\\lavalink"
java -Xms256m -Xmx1g -XX:+UseG1GC -jar Lavalink.jar
pause
"""
    (ROOT / "start_lavalink.bat").write_text(lavalink_bat, encoding="utf-8")

    lavalink_sh = """#!/bin/bash
# Lavalink Linux/macOS Start Script
cd "$(dirname "$0")/lavalink"
java -Xms256m -Xmx1g -XX:+UseG1GC -jar Lavalink.jar
"""
    lavalink_sh_path = ROOT / "start_lavalink.sh"
    lavalink_sh_path.write_text(lavalink_sh, encoding="utf-8")
    lavalink_sh_path.chmod(0o755)

    # Dashboard start script
    dash_bat = """@echo off
REM Dashboard Windows Start Script
cd /d "%~dp0"
call .venv\\Scripts\\activate.bat
python -m bot.dashboard.dashboard
pause
"""
    (ROOT / "start_dashboard.bat").write_text(dash_bat, encoding="utf-8")

    dash_sh = """#!/bin/bash
# Dashboard Linux/macOS Start Script
cd "$(dirname "$0")"
source .venv/bin/activate
python -m bot.dashboard.dashboard
"""
    dash_sh_path = ROOT / "start_dashboard.sh"
    dash_sh_path.write_text(dash_sh, encoding="utf-8")
    dash_sh_path.chmod(0o755)

    print_success("Start scripts created:")
    print_info("  Bot:        start_bot.bat / start_bot.sh")
    print_info("  Lavalink:   start_lavalink.bat / start_lavalink.sh")
    print_info("  Dashboard:  start_dashboard.bat / start_dashboard.sh")
    return True


def run_tests() -> bool:
    print_header("Running Tests")
    python = get_python()
    result = run_cmd([str(python), "-m", "pytest", "tests/", "-v"], capture=True)
    if result.returncode == 0:
        print_success("All tests passed")
        return True
    print_warning("Some tests failed (check output)")
    if RICH_AVAILABLE:
        CONSOLE.print(result.stdout)
        CONSOLE.print(result.stderr, style="red")
    else:
        print(result.stdout)
        print(result.stderr)
    return False


def print_summary() -> None:
    print_header("Setup Complete!")
    if RICH_AVAILABLE:
        table = Table(title="Next Steps", show_header=True, header_style="bold cyan")
        table.add_column("Step", style="yellow")
        table.add_column("Command", style="green")
        table.add_row("1. Start Lavalink (terminal 1)", "start_lavalink.bat / ./start_lavalink.sh")
        table.add_row("2. Start Bot (terminal 2)", "start_bot.bat / ./start_bot.sh")
        table.add_row("3. Start Dashboard (optional, terminal 3)", "start_dashboard.bat / ./start_dashboard.sh")
        table.add_row("4. Open Dashboard", "http://localhost:18080")
        CONSOLE.print(table)
    else:
        print("\nNext Steps:")
        print("  1. Start Lavalink:  start_lavalink.bat / ./start_lavalink.sh")
        print("  2. Start Bot:       start_bot.bat / ./start_bot.sh")
        print("  3. Start Dashboard: start_dashboard.bat / ./start_dashboard.sh (optional)")
        print("  4. Open Dashboard:  http://localhost:18080")

    print("\nConfiguration file: .env (edit anytime)")
    print("Logs: logs/bot.log")


async def main() -> int:
    parser = ArgumentParser(description="DiscBot Installer")
    parser.add_argument("--non-interactive", "--auto", action="store_true",
                        help="Run in non-interactive mode (use defaults, skip prompts)")
    parser.add_argument("--skip-tests", action="store_true", help="Skip running tests")
    args = parser.parse_args()

    global IS_INTERACTIVE
    if args.non_interactive:
        IS_INTERACTIVE = False

    if RICH_AVAILABLE:
        CONSOLE.print(Panel.fit(
            "[bold magenta]DiscBot Installer[/bold magenta]\n"
            "[dim]Modern setup with interactive configuration[/dim]",
            border_style="magenta"
        ))

    # Phase 1: Prerequisites
    if not check_python_version():
        return 1
    if not check_ffmpeg():
        return 1
    check_java()
    check_git()

    # Phase 2: Environment
    if not create_venv():
        return 1
    if not install_dependencies():
        return 1

    # Phase 3: Lavalink
    if not download_lavalink():
        return 1

    # Phase 4: Configuration
    if not interactive_env_setup():
        return 1

    # Phase 5: Start scripts
    if not create_start_scripts():
        return 1

    # Phase 6: Tests (optional)
    run_tests_flag = False
    if not IS_INTERACTIVE:
        print_info("Non-interactive mode: skipping tests (run 'pytest tests/' manually)")
    elif RICH_AVAILABLE:
        try:
            run_tests_flag = Confirm.ask("Run tests to verify installation?", default=True)
        except EOFError:
            print_warning("EOF received, skipping tests")
    else:
        try:
            run_tests_flag = input("Run tests? (Y/n): ").lower() != 'n'
        except EOFError:
            print_warning("EOF received, skipping tests")
    
    if run_tests_flag:
        run_tests()

    print_summary()
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)