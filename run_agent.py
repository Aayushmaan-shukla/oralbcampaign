#!/usr/bin/env python3
"""
Simple runner script for the Agno Agent
Run this script to start scraping all URLs from the Oral B iO3.json file
"""

import asyncio
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

from agno_agent import main

if __name__ == "__main__":
    print("Starting Oral B iO3 Product Scraping Agent...")
    print("This will visit each URL and extract pricing, offers, and stock information")
    print("Press Ctrl+C to stop the scraping process\n")
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScraping interrupted by user")
    except Exception as e:
        print(f"Error running the agent: {e}")
        sys.exit(1)

