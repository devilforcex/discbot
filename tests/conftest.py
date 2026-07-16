#/
# Pytest configuration for DiscBot tests
#/

import pytest
from typing import Any

# Add the bot directory to the Python path
import sys
import os

# Add the root directory to the path so we can import bot modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test configuration
@pytest.fixture
def mock_config():
    """Fixture for mock Discord configuration."""
    config = MagicMock()
    config.discord_bot_token = "test_token"
    config.guild_id = 0
    config.music_channel_id = 0
    config.music_voice_channel_id = 0
    config.owner_id = 0
    config.lavalink_host = "127.0.0.1"
    config.lavalink_port = 12333
    config.lavalink_password = "youshallnotpass"
    config.lavalink_secure = False
    config.youtube_cookies_enabled = True
    config.spotify_client_id = None
    config.spotify_client_secret = None
    config.database_path = ":memory:"
    config.database_url = None
    config.log_level = "INFO"
    config.dashboard_enabled = False
    config.dashboard_host = "0.0.0.0"
    config.dashboard_port = 18080
    config.dashboard_secret_key = "test_secret_key"
    config.support_server_url = None
    config.discord_invite_url = None
    config.bot_invite_url = None
    config.website_url = None
    config.made_by_text = "Made with ❤️ by Test"
    config.ai_enabled = True
    config.ai_provider = "openai"
    config.omniroute_base_url = "http://localhost:20128/v1"
    config.omniroute_api_key = "test-key"
    config.ai_default_model = "gpt-4o-mini"
    config.ai_system_prompt = "Test assistant"
    config.ai_max_history = 10
    config.ai_temperature = 0.7

    return config

# Custom markers for different test categories
@pytest.mark.unit("Unit tests")
def test_unit_marker():
    """Marker for unit tests."""
    pass

@pytest.mark.integration("Integration tests")
def test_integration_marker():
    """Marker for integration tests."""
    pass

@pytest.mark.ai("AI service tests")
def test_ai_marker():
    """Marker for AI service tests."""
    pass

@pytest.mark.discord("Discord-related tests")
def test_discord_marker():
    """Marker for Discord-related tests."""
    pass

# Performance markers
@pytest.mark.slow("Slow tests requiring external services")
def test_slow_marker():
    """Marker for slow tests."""
    pass

# Error handling markers
@pytest.mark.error("Tests that verify error handling")
def test_error_marker():
    """Marker for error handling tests."""
    pass

# Socket markers for distributed systems
@pytest.mark.asyncio("Async tests")
def test_asyncio_marker():
    """Marker for async tests."""
    pass

# Test collection hooks
from _pytest.config import Config as PytestConfig
from _pytest.config.argparsing import Parser

def pytest_configure(config: PytestConfig):
    """Configure pytest."""
    # Add custom markers
    config.addinivalue_line(
        "markers",
        "unit: Mark test as a unit test",
    )
    config.addinivalue_line(
        "markers",
        "integration: Mark test as an integration test",
    )
    config.addinivalue_line(
        "markers",
        "ai: Mark test as an AI service test",
    )
    config.addinivalue_line(
        "markers",
        "discord: Mark test as a Discord-related test",
    )
    config.addinivalue_line(
        "markers",
        "slow: Mark test as a slow test requiring external services",
    )
    config.addinivalue_line(
        "markers",
        "error: Mark test as a test that verifies error handling",
    )


def pytest_collection_modifyitems(items):
    """Modify test collection to apply markers."""
    for item in items:
        # Apply unit marker to test files in tests/unit
        if "tests/unit" in str(item.fspath):
            item.add_marker("unit")

        # Apply integration marker to test files in tests/integration
        if "tests/integration" in str(item.fspath):
            item.add_marker("integration")

        # Apply AI marker to test files with AI in name
        if "ai" in str(item.fspath).lower():
            item.add_marker("ai")

        # Apply discord marker to test files with discord in name
        if "discord" in str(item.fspath).lower():
            item.add_marker("discord")


# Test session start hook
def pytest_sessionstart(session, config):
    """Called after the `Session` object is created and before performing collection."""
    print("\n" + "="*70)
    print("🧪 Pytest configured for DiscBot")
    print("="*70)


# Test session finish hook
def pytest_sessionfinish(session, exitstatus):
    """Called after all tests have been run."""
    print("\n" + "="*70)
    print(f"✅ Test session completed (exit status: {exitstatus})")
    print("="*70)


# Test report hook
def pytest_runtestloop(session):
    """Main loop of the test runner."""
    print("\n" + "-"*70)
    print(f"🧪 Running {len(session.items)} tests")
    print("-"*70)


# Test progress hook
def pytest_runtestlogoutput(item):
    """Output of each test as it is being collected."""
    if "test_" in str(item.name):
        print(f"  Test: {item.name}")


# Custom pytest configuration
def pytest_addoption(parser: Parser):
    """Add pytest options."""
    parser.addoption(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose output",
    )
    parser.addoption(
        "-x", "--exitfirst",
        action="store_true",
        default=False,
        help="Exit on first failure",
    )
    parser.addoption(
        "-s", "--tb-style",
        choices=["auto", "short", "line", "no", "native"],
        default="short",
        help="Override default traceback print mode",
    )


def pytest_collection_modifyitems(items):
    """Modify test collection to apply default markers."""
    for item in items:
        # Apply unit marker to all tests unless they're integration
        if "integration" not in str(item.fspath):
            item.add_marker("unit")


# Environment markers
@pytest.fixture(autouse=True)
def check_environment():
    """Check test environment before running tests."""
    # Ensure no test interferes with production environment
    import os

    if os.getenv("DISCORD_BOT_TOKEN") is None:
        print("⚠️ Warning: DISCORD_BOT_TOKEN not set - tests may fail")
    if os.getenv("DATABASE_URL") is None:
        print("⚠️ Warning: DATABASE_URL not set - tests will use SQLite")

    yield

    # Cleanup after tests
    print("✅ Test environment checked and cleaned up")


# Import MagicMock for fixtures
from unittest.mock import MagicMock

# Test result verification
class TestResultSummary:
    """Summarize test results."""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def update(self, report):
        """Update test result counts."""
        if report.when == "call":
            if report.outcome == "passed":
                self.passed += 1
            elif report.outcome == "failed":
                self.failed += 1
            elif report.outcome == "skipped":
                self.skipped += 1

    def print_summary(self):
        """Print test result summary."""
        total = self.passed + self.failed + self.skipped
        if total > 0:
            print(f"\n📊 Test Summary:")
            print(f"   Passed:   {self.passed:4d}/{total:4d} ({(self.passed/total*100):5.1f}%)")
            print(f"   Failed:   {self.failed:4d}/{total:4d} ({(self.failed/total*100):5.1f}%)")
            print(f"   Skipped:  {self.skipped:4d}/{total:4d} ({(self.skipped/total*100):5.1f}%)")


# Global test result summary
test_summary = TestResultSummary()


# Test result hooks
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test results."""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call":
        test_summary.update(rep)


def pytest_sessionfinish(session, exitstatus):
    """Print test summary at the end."""
    test_summary.print_summary()