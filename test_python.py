#!/usr/bin/env python3
"""
Test if Python is working
"""
import sys
import os

print("🐍 Python version:", sys.version)
print("📁 Current directory:", os.getcwd())
print("📂 Files in directory:", os.listdir('.'))
print("🌍 Environment variables:")
for key in ['PORT', 'PYTHON_VERSION']:
    print(f"  {key}: {os.getenv(key, 'Not set')}")

print("✅ Python is working!")

# Try importing FastAPI
try:
    from fastapi import FastAPI
    print("✅ FastAPI import successful")
except ImportError as e:
    print(f"❌ FastAPI import failed: {e}")

# Try importing uvicorn
try:
    import uvicorn
    print("✅ Uvicorn import successful")
except ImportError as e:
    print(f"❌ Uvicorn import failed: {e}")

print("🏁 Test complete")
