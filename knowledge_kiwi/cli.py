#!/usr/bin/env python3
"""
Knowledge Kiwi CLI Entry Point

Handles MCP server startup in stdio mode.
"""

import asyncio
import sys
from pathlib import Path

from knowledge_kiwi.server import KnowledgeKiwiMCP


def main():
    """Entry point for the CLI"""
    server = KnowledgeKiwiMCP()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

