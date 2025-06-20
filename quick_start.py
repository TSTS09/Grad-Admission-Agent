#!/usr/bin/env python3
"""
Quick start script for STEM Graduate Admissions Assistant
Tests the system and verifies everything is working
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.append(str(Path(__file__).parent))

async def test_system():
    """Test the system components"""
    print("🎓 STEM Graduate Admissions Assistant - Quick Start Test")
    print("=" * 60)
    
    # Test 1: Check environment variables
    print("\n1. Checking Environment Variables...")
    
    required_keys = ["OPENAI_API_KEY", "TAVILY_API_KEY"]
    missing_keys = []
    
    for key in required_keys:
        value = os.getenv(key)
        if value and value != f"your-{key.lower().replace('_', '-')}-here":
            print(f"   ✅ {key}: Set")
        else:
            print(f"   ❌ {key}: Missing or not configured")
            missing_keys.append(key)
    
    if missing_keys:
        print(f"\n⚠️  Please set these environment variables in your .env file:")
        for key in missing_keys:
            print(f"   {key}=your-actual-api-key")
        print("\nThen run this script again.")
        return False
    
    # Test 2: Import modules
    print("\n2. Testing Module Imports...")
    
    try:
        from app.agents.realtime_agents import RealTimeDataOrchestrator
        print("   ✅ Real-time agents imported successfully")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    try:
        from app.core.config import settings
        print("   ✅ Configuration loaded successfully")
    except ImportError as e:
        print(f"   ❌ Config error: {e}")
        return False
    
    # Test 3: Initialize orchestrator
    print("\n3. Initializing AI Orchestrator...")
    
    try:
        orchestrator = RealTimeDataOrchestrator()
        print("   ✅ Orchestrator initialized")
    except Exception as e:
        print(f"   ❌ Orchestrator error: {e}")
        return False
    
    # Test 4: Test a real query
    print("\n4. Testing Real Query...")
    
    try:
        test_query = "Find machine learning professors at Stanford"
        print(f"   Query: '{test_query}'")
        
        response = await orchestrator.process_query(test_query)
        
        faculty_count = len(response.get("faculty_matches", []))
        program_count = len(response.get("program_matches", []))
        confidence = response.get("confidence_score", 0)
        
        print(f"   ✅ Response generated successfully")
        print(f"   📊 Faculty found: {faculty_count}")
        print(f"   📊 Programs found: {program_count}")
        print(f"   📊 Confidence: {confidence:.2f}")
        print(f"   💬 Response: {response.get('response', 'No response')[:100]}...")
        
    except Exception as e:
        print(f"   ❌ Query test error: {e}")
        return False
    
    # Test 5: Web scraping test
    print("\n5. Testing Web Scraping...")
    
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://cs.stanford.edu", timeout=10) as resp:
                if resp.status == 200:
                    print("   ✅ Web scraping connection successful")
                else:
                    print(f"   ⚠️  Web scraping returned status {resp.status}")
    except Exception as e:
        print(f"   ⚠️  Web scraping test failed: {e}")
        print("   (This might be due to network restrictions)")
    
    print("\n" + "=" * 60)
    print("🎉 System Test Complete!")
    print("\nNext steps:")
    print("1. Run: python -m uvicorn app.main:app --reload")
    print("2. Open: http://localhost:8000")
    print("3. Test chat: http://localhost:8000/chat")
    print("4. Try query: 'Find CS professors at MIT hiring for 2026'")
    
    return True

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking Dependencies...")
    
    # Package name vs import name mapping
    packages_to_check = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"), 
        ("openai", "openai"),
        ("aiohttp", "aiohttp"),
        ("beautifulsoup4", "bs4"),  # Package vs import name
        ("tavily-python", "tavily"),  # Package vs import name
        ("pydantic", "pydantic")
    ]
    
    missing_packages = []
    
    for package_name, import_name in packages_to_check:
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name}")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages. Install with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def create_env_file():
    """Create .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        print("📝 Creating .env file...")
        
        env_content = """# STEM Graduate Admissions Assistant Configuration

# API Keys (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here
TAVILY_API_KEY=your-tavily-api-key-here

# Optional APIs
REDDIT_CLIENT_ID=your-reddit-client-id
REDDIT_CLIENT_SECRET=your-reddit-client-secret

# Application Settings
ENVIRONMENT=development
SECRET_KEY=dev-secret-key-change-in-production
LOG_LEVEL=INFO

# Server
HOST=0.0.0.0
PORT=8000
"""
        
        with open(".env", "w") as f:
            f.write(env_content)
        
        print("   ✅ .env file created")
        print("   ⚠️  Please edit .env and add your actual API keys")
        return False
    
    return True

async def main():
    """Main function"""
    print("🚀 STEM Graduate Admissions Assistant - Quick Start")
    print("This script will test your installation and configuration\n")
    
    # Step 1: Check if .env exists
    if not create_env_file():
        return
    
    # Step 2: Check dependencies
    if not check_dependencies():
        return
    
    # Step 3: Test the system
    success = await test_system()
    
    if success:
        print("\n🎉 Everything looks good! Your system is ready.")
        
        # Ask if user wants to start the server
        try:
            start_server = input("\nWould you like to start the server now? (y/n): ").lower().strip()
            if start_server in ['y', 'yes']:
                print("\nStarting server...")
                os.system("python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
    else:
        print("\n❌ Some issues found. Please fix them and run again.")

if __name__ == "__main__":
    asyncio.run(main())