"""
Standalone landing page server for DiscBot Steel.
Serves the static landing page on port 3000.
No external dependencies required — uses Python's built-in http.server.

Usage:
    python bot/landing/server.py
    # Then open http://localhost:3000
"""
import http.server
import os
import socketserver
import sys

PORT = 3000
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


class LandingHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that serves from the static directory."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def log_message(self, format, *args):
        """Override to add a cleaner log format."""
        sys.stderr.write(f"[LandingPage] {args[0]} {args[1]} {args[2]}\n")


def main():
    """Start the landing page server."""
    if not os.path.isdir(STATIC_DIR):
        sys.stderr.write(f"ERROR: Static directory not found: {STATIC_DIR}\n")
        sys.exit(1)

    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.isfile(index_path):
        sys.stderr.write(f"ERROR: index.html not found in {STATIC_DIR}\n")
        sys.exit(1)

    with socketserver.TCPServer(("", PORT), LandingHandler) as httpd:
        print(f"+{'-'*46}+")
        print(f"|  DiscBot Steel - Landing Page               |")
        print(f"|  Serving at http://localhost:{PORT}            |")
        print(f"|  Press Ctrl+C to stop                       |")
        print(f"+{'-'*46}+")
        print(f"\nStatic directory: {STATIC_DIR}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down landing page server...")


if __name__ == "__main__":
    main()