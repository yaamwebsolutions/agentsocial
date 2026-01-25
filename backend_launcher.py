#!/usr/bin/env python3
"""
Backend launcher for Agent Twitter
This script will be started on deployment
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and run the main app
from backend.main import app
import uvicorn

if __name__ == "__main__":
    print("🚀 Starting Agent Twitter Backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
