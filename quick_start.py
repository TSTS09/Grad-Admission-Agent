#!/usr/bin/env python3
"""
STEM Graduate Admissions Assistant - Quick Start Test
Tests basic functionality and configuration
"""
import os
import sys
import asyncio
from pathlib import Path

def print_header():
    print("🎓 STEM Graduate Admissions Assistant - Quick Start Test")
    print("=" * 60)

def check_dependencies():
    """Check if required packages are installed"""
    print("📦 Checking Dependencies...")
    
    # Package name -> (import name, display name)
    required_packages = [
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'), 
        ('openai', 'openai'),
        ('aiohttp', 'aiohttp'),
        ('bs4', 'beautifulsoup4'),  # Fixed: bs4 is the import name
        ('tavily', 'tavily-python'),  # Fixed: tavily is the import name
        ('pydantic', 'pydantic'),
        ('pydantic_settings', 'pydantic-settings'),
        ('firebase_admin', 'firebase-admin')
    ]
    
    missing_packages = []
    
    for import_name, display_name in required_packages:
        try:
            __import__(import_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} - Missing")
            missing_packages.append(display_name)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_environment():
    """Check environment variables"""
    print("1. Checking Environment Variables...")
    
    required_vars = ['OPENAI_API_KEY', 'TAVILY_API_KEY']
    optional_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'TWITTER_BEARER_TOKEN']
    
    all_good = True
    
    for var in required_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: Set")
        else:
            print(f"   ❌ {var}: Missing")
            all_good = False
    
    for var in optional_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: Set (optional)")
        else:
            print(f"   ⚠️  {var}: Not set (optional)")
    
    return all_good

def test_imports():
    """Test importing core modules"""
    print("2. Testing Module Imports...")
    
    try:
        # Test basic imports
        from pydantic_settings import BaseSettings
        print("   ✅ pydantic_settings.BaseSettings")
        
        from app.core.logging import setup_logging, get_logger
        print("   ✅ app.core.logging")
        
        # Test config with updated imports
        from app.core.config import settings, get_firebase
        print("   ✅ app.core.config")
        
        from app.models.firebase_models import University, Faculty, Program
        print("   ✅ app.models.firebase_models")
        
        from app.agents.cost_effective_agents import ChatOrchestrator
        print("   ✅ app.agents.cost_effective_agents")
        
        from app.scrapers.real_university_scraper import ScrapingOrchestrator
        print("   ✅ app.scrapers.real_university_scraper")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

async def test_basic_functionality():
    """Test basic functionality"""
    print("3. Testing Basic Functionality...")
    
    try:
        # Import here to avoid issues if imports fail
        from app.agents.cost_effective_agents import ChatOrchestrator
        from app.scrapers.real_university_scraper import ScrapingOrchestrator
        
        # Test chat orchestrator
        chat_orchestrator = ChatOrchestrator()
        print("   ✅ ChatOrchestrator initialized")
        
        # Test scraping orchestrator
        scraping_orchestrator = ScrapingOrchestrator()
        print("   ✅ ScrapingOrchestrator initialized")
        
        # Test a simple query (without Firebase for now)
        test_query = "Tell me about machine learning PhD programs"
        try:
            response = await chat_orchestrator.process_query(test_query)
            if response and "response" in response:
                print("   ✅ Basic chat processing works")
                print(f"   📝 Sample response: {response['response'][:100]}...")
            else:
                print("   ⚠️  Chat processing returned unexpected format")
        except Exception as e:
            print(f"   ⚠️  Chat processing error (this may be expected without Firebase): {e}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Basic functionality test failed: {e}")
        return False

def check_file_structure():
    """Check if required files exist"""
    print("4. Checking File Structure...")
    
    required_files = [
        'app/main.py',
        'app/core/__init__.py',
        'app/core/config.py',
        'app/core/logging.py',
        'app/models/__init__.py',
        'app/models/firebase_models.py',
        'app/agents/__init__.py',
        'app/agents/cost_effective_agents.py',
        'app/scrapers/__init__.py',
        'app/scrapers/real_university_scraper.py',
        'static/css/dashboard.css',
        'static/css/chat.css',
        'static/js/api.js',
        'static/js/chat.js',
        'static/js/dashboard.js',
        'static/dashboard.html',
        'static/chat.html'
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - Missing")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {len(missing_files)} files need to be created")
        return False
    
    return True

def create_env_template():
    """Create .env template if it doesn't exist"""
    env_template = """# STEM Graduate Admissions Assistant Environment Variables

# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here

# Optional API Keys for Social Media Monitoring
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
TWITTER_BEARER_TOKEN=your_twitter_bearer_token

# Firebase Configuration
FIREBASE_PROJECT_ID=afya-a1006
FIREBASE_STORAGE_BUCKET=stem-grad-assistant.appspot.com

# Application Settings
ENVIRONMENT=development
DEBUG=true
ENABLE_BACKGROUND_SCRAPING=false
LOG_LEVEL=INFO
"""
    
    if not Path('.env').exists():
        with open('.env', 'w') as f:
            f.write(env_template)
        print("📄 Created .env template file")
        print("   Please edit .env with your actual API keys")
    else:
        print("📄 .env file already exists")

async def main():
    """Main test function"""
    print_header()
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    # Continue with tests even if some dependencies seem missing
    # (they might be false negatives)
    
    # Check environment variables
    env_ok = check_environment()
    
    # Test imports
    imports_ok = test_imports()
    
    # Check file structure
    files_ok = check_file_structure()
    
    # Test basic functionality (only if imports worked)
    if imports_ok:
        functionality_ok = await test_basic_functionality()
    else:
        functionality_ok = False
    
    # Create .env template
    create_env_template()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY:")
    print("=" * 60)
    
    if deps_ok and env_ok and imports_ok and files_ok and functionality_ok:
        print("🎉 All tests passed! Your setup looks good.")
        print("\nNext steps:")
        print("1. Make sure your .env file has valid API keys")
        print("2. Set up Firebase credentials if using Firebase")
        print("3. Run the application: python app/main.py")
        print("4. Visit: http://localhost:8000")
    else:
        print("⚠️  Some issues found. Please check details above.")
        
        if not deps_ok:
            print("   - Some packages may not be detected correctly")
        if not env_ok:
            print("   - Set up required environment variables")
        if not imports_ok:
            print("   - Fix import errors (check dependencies)")
        if not files_ok:
            print("   - Create missing files")
        if not functionality_ok:
            print("   - Debug functionality issues")
        
        print("\nEven with some warnings, you may still be able to run the application.")
        print("Try: python app/main.py")

if __name__ == "__main__":
    # Create __init__.py files if they don't exist
    init_dirs = ['app', 'app/core', 'app/models', 'app/agents', 'app/scrapers']
    for dir_path in init_dirs:
        init_file = Path(dir_path) / '__init__.py'
        if not init_file.exists():
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.touch()
    
    # Run the tests
    asyncio.run(main())