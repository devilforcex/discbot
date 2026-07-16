#!/bin/bash
# Lavalink Linux/macOS Start Script
cd "$(dirname "$0")/lavalink"
java -Xms256m -Xmx1g -XX:+UseG1GC -jar Lavalink.jar
