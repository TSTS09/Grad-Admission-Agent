#!/usr/bin/env python3
"""
Setup script for Intelligent Grad Admissions Scraper with Google Gemini
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    print("🎓 Intelligent Grad Admissions Scraper Setup")
    print("=" * 55)
    print("🤖 Powered by Google Gemini AI")
    print("✅ AI-powered web scraping")
    print("✅ Real information extraction")
    print("✅ Source link compilation")
    print("✅ More cost-effective than OpenAI")
    print("=" * 55)

def check_python():
    """Check Python version"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}")
    return True

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    
    directories = ["app", "app/core", "app/agents", "static"]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        if directory.startswith("app"):
            (Path(directory) / "__init__.py").touch()
    
    print("✅ Directories created")

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("Try: pip install fastapi uvicorn google-generativeai aiohttp beautifulsoup4")
        return False

def create_env_file():
    """Create .env file for Gemini API key"""
    print("\n🔑 Setting up environment...")
    
    env_content = """# Intelligent Grad Admissions Scraper with Gemini
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000

# To get your Gemini API key:
# 1. Go to https://makersuite.google.com/app/apikey
# 2. Create a new API key
# 3. Replace 'your_gemini_api_key_here' with your actual key
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("⚠️  Please add your Google Gemini API key to .env file")
        print("   Get your key at: https://makersuite.google.com/app/apikey")
    else:
        print("✅ .env file already exists")
    
    return True

def create_core_files():
    """Create core application files"""
    print("\n📄 Creating core files...")
    
    # Create __init__.py files
    for path in ["app/__init__.py", "app/core/__init__.py", "app/agents/__init__.py"]:
        Path(path).touch()
    
    # Create config.py
    config_content = '''# app/core/config.py
import os

class Settings:
    APP_NAME = "Intelligent Grad Admissions Assistant"
    VERSION = "1.0.0"
    HOST = "0.0.0.0"
    PORT = int(os.getenv("PORT", 8000))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    DATABASE_PATH = "admissions_search.db"

settings = Settings()
'''
    
    with open("app/core/config.py", "w") as f:
        f.write(config_content)
    
    # Create logging.py
    logging_content = '''# app/core/logging.py
import logging
import sys

def setup_logging(level="INFO"):
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)

def get_logger(name: str):
    return logging.getLogger(name)

setup_logging()
'''
    
    with open("app/core/logging.py", "w") as f:
        f.write(logging_content)
    
    print("✅ Core files created")

def initialize_database():
    """Initialize SQLite database"""
    print("\n🗄️  Initializing database...")
    
    try:
        conn = sqlite3.connect("admissions_search.db")
        conn.execute('''
            CREATE TABLE IF NOT EXISTS search_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT NOT NULL,
                search_intent TEXT,
                websites_found TEXT,
                information_extracted TEXT,
                source_links TEXT,
                search_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                confidence_score REAL
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database initialized")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def create_run_script():
    """Create run script"""
    print("\n🚀 Creating run script...")
    
    run_content = '''#!/usr/bin/env python3
"""Run the Intelligent Grad Admissions Scraper with Gemini"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check for API key
if not os.getenv("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY") == "your_gemini_api_key_here":
    print("❌ Please set your Google Gemini API key in the .env file")
    print("Edit .env and add: GEMINI_API_KEY=your_actual_api_key")
    print("Get your key at: https://makersuite.google.com/app/apikey")
    sys.exit(1)

import uvicorn

if __name__ == "__main__":
    print("🎓 Starting Intelligent Grad Admissions Scraper...")
    print("🤖 Powered by Google Gemini AI")
    print("🌐 Dashboard: http://localhost:8000")
    print("🛑 Stop with Ctrl+C")
    print()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
'''
    
    with open("run.py", "w") as f:
        f.write(run_content)
    
    if os.name != 'nt':
        os.chmod("run.py", 0o755)
    
    print("✅ Run script created")

def test_setup():
    """Test the setup"""
    print("\n🧪 Testing setup...")
    
    try:
        # Test core imports
        sys.path.append(str(Path.cwd()))
        from app.core.logging import get_logger
        from app.core.config import settings
        
        # Test database
        conn = sqlite3.connect("admissions_search.db")
        conn.execute("SELECT 1")
        conn.close()
        
        # Test Gemini import
        try:
            import google.generativeai as genai
            print("✅ Google Gemini SDK available")
        except ImportError:
            print("⚠️  Google Gemini SDK not installed properly")
        
        print("✅ Setup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def show_gemini_api_instructions():
    """Show instructions for getting Gemini API key"""
    print("\n🔑 Getting Your Google Gemini API Key:")
    print("=" * 50)
    print("1. Go to: https://makersuite.google.com/app/apikey")
    print("2. Sign in with your Google account")
    print("3. Click 'Create API Key'")
    print("4. Copy the generated API key")
    print("5. Edit the .env file and replace 'your_gemini_api_key_here' with your key")
    print()
    print("💰 Gemini Pricing Benefits:")
    print("• Free tier: 15 requests per minute")
    print("• Very cost-effective compared to OpenAI")
    print("• Great performance for academic queries")

def show_next_steps():
    """Show next steps"""
    print("\n" + "=" * 55)
    print("🎉 SETUP COMPLETE!")
    print("=" * 55)
    
    print("\n📋 Next Steps:")
    print("1. Get your Google Gemini API key:")
    print("   https://makersuite.google.com/app/apikey")
    
    print("\n2. Add your API key to .env file:")
    print("   GEMINI_API_KEY=your_actual_api_key_here")
    
    print("\n3. Start the application:")
    print("   python run.py")
    
    print("\n4. Open browser:")
    print("   http://localhost:8000")
    
    print("\n5. Try queries like:")
    print("   • 'Stanford PhD computer science requirements'")
    print("   • 'MIT master in AI application deadlines'")
    print("   • 'Berkeley EECS graduate funding opportunities'")
    print("   • 'How to apply for PhD in machine learning'")
    
    print("\n🤖 Gemini AI Features:")
    print("✅ Intelligent query understanding")
    print("✅ Dynamic website discovery")
    print("✅ Real information synthesis")
    print("✅ Source link compilation")
    print("✅ Cost-effective AI processing")
    
    print("\n💡 Why Gemini?")
    print("• More affordable than OpenAI")
    print("• Excellent for academic content")
    print("• Fast response times")
    print("• Google's latest AI technology")

def main():
    """Main setup function"""
    print_header()
    
    if not check_python():
        sys.exit(1)
    
    create_directories()
    
    if not install_dependencies():
        print("⚠️  Dependencies had issues, but continuing...")
    
    create_env_file()
    create_core_files()
    
    if not initialize_database():
        print("⚠️  Database issues, but continuing...")
    
    create_run_script()
    
    if test_setup():
        show_gemini_api_instructions()
        show_next_steps()
        print("\n🎉 Ready to use with Gemini AI!")
    else:
        print("\n⚠️  Setup completed with some issues")

if __name__ == "__main__":
    main()