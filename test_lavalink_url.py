#!/usr/bin/env python3
"""
Quick test to check Lavalink connectivity and URL search behavior.
Run: python test_lavalink_url.py
"""

import asyncio
import socket
import sys


def check_lavalink_port() -> None:
    print("=" * 50)
    print("TEST 1: Lavalink Connectivity Check")
    print("=" * 50)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        result = s.connect_ex(("127.0.0.1", 12333))
    if result == 0:
        print("[OK] Lavalink is listening on port 12333")
    else:
        print(f"[FAIL] Lavalink NOT listening (error code: {result})")
        print("  Start Lavalink with: java -jar Lavalink.jar")


def import_wavelink():
    print("\n" + "=" * 50)
    print("TEST 2: Wavelink Import Check")
    print("=" * 50)

    try:
        import wavelink
    except ImportError as e:
        print(f"[FAIL] Failed to import wavelink: {e}")
        sys.exit(1)

    print(f"[OK] wavelink imported successfully (version: {wavelink.__version__})")
    return wavelink

async def test_url_search():
    # Import project modules
    from bot.config import load_config
    from bot.music.search import search_tracks, is_url
    from bot.music.lavalink.client import LavalinkClient
    
    # Setup Lavalink connection for the test
    config = load_config()
    
    try:
        print("\nConnecting to Lavalink for search tests...")
        import discord
        # Use a basic client
        client = discord.Client(intents=discord.Intents.default())
        
        # Use the bot's own LavalinkClient for consistency
        lavalink = LavalinkClient(client)
        await lavalink.setup(config)
        
        # Wait for the node to actually connect
        node = wavelink.Pool.get_node()
        connected = False
        for i in range(15):
            if node and node.status == wavelink.NodeStatus.CONNECTED:
                connected = True
                break
            await asyncio.sleep(1)
        
        if connected:
            print("[OK] Connected to Lavalink")
        else:
            status = node.status if node else "No node found"
            print(f"[FAIL] Timed out waiting for Lavalink connection. Status: {status}")
            return
    except Exception as e:
        print(f"[FAIL] Could not connect to Lavalink for tests: {e}")
        return

    test_urls = [
        "https://www.youtube.com/watch?v=dQwEw6eMDQo",  # Classic YouTube video
        "https://youtube.com/watch?v=K0y5f2jhYvk",     # Another test video
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        print(f"  is_url() returns: {is_url(url)}")
        try:
            tracks = await search_tracks(url, source=None, fallbacks=True)
            if tracks:
                if isinstance(tracks, wavelink.Playlist):
                    print(f"  [OK] Got playlist with {len(tracks)} tracks: {tracks.name}")
                else:
                    first = tracks[0]
                    print(f"  [OK] Got track: {first.title} by {first.author}")
            else:
                print("  [FAIL] No tracks returned (empty result)")
        except wavelink.LavalinkLoadException as e:
            print(f"  [FAIL] LavalinkLoadException:")
            print(f"      error: {e.error}")
            print(f"      severity: {e.severity}")
            print(f"      cause: {e.cause}")
        except wavelink.NodeException as e:
            print(f"  [FAIL] NodeException: {e} (status: {e.status})")
        except Exception as e:
            print(f"  [FAIL] Unexpected exception: {type(e).__name__}: {e}")

async def cleanup(wavelink_module) -> None:
    await wavelink_module.Pool.close()


def main() -> None:
    check_lavalink_port()
    wavelink_module = import_wavelink()

    print("\n" + "=" * 50)
    print("TEST 3: search_tracks(URL) Behavior Test")
    print("=" * 50)

    asyncio.run(test_url_search())
    asyncio.run(cleanup(wavelink_module))

    print("\n" + "=" * 50)
    print("TEST COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    main()
