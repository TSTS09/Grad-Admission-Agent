#!/usr/bin/env python3
"""
Setup script for Intelligent Grad Admissions Scraper
"""

import os
import sys
import subprocess
import sqlite3
from pathlib import Path

def print_header():
    print("🎓 Intelligent Grad Admissions Scraper Setup")
    print("=" * 50)
    print("✅ AI-powered web scraping")
    print("✅ Real information extraction")
    print("✅ Source link compilation")
    print("✅ Uses OpenAI API")
    print("=" * 50)

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
        print("Try: pip install fastapi uvicorn openai aiohttp beautifulsoup4")
        return False

def create_env_file():
    """Create .env file for API key"""
    print("\n🔑 Setting up environment...")
    
    env_content = """# Intelligent Grad Admissions Scraper Environment
OPENAI_API_KEY=your_openai_api_key_here
PORT=8000
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file")
        print("⚠️  Please add your OpenAI API key to .env file")
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
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
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
"""Run the Intelligent Grad Admissions Scraper"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Check for API key
if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
    print("❌ Please set your OpenAI API key in the .env file")
    print("Edit .env and add: OPENAI_API_KEY=your_actual_api_key")
    sys.exit(1)

import uvicorn

if __name__ == "__main__":
    print("🎓 Starting Intelligent Grad Admissions Scraper...")
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
        
        print("✅ Setup test passed")
        return True
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def show_next_steps():
    """Show next steps"""
    print("\n" + "=" * 50)
    print("🎉 SETUP COMPLETE!")
    print("=" * 50)
    
    print("\n📋 Next Steps:")
    print("1. Add your OpenAI API key to .env file:")
    print("   OPENAI_API_KEY=your_actual_api_key_here")
    
    print("\n2. Start the application:")
    print("   python run.py")
    
    print("\n3. Open browser:")
    print("   http://localhost:8000")
    
    print("\n4. Try queries like:")
    print("   • 'Stanford PhD computer science requirements'")
    print("   • 'MIT master in AI application deadlines'")
    print("   • 'Berkeley EECS graduate funding opportunities'")
    
    print("\n🔍 Features:")
    print("✅ Intelligent web scraping")
    print("✅ AI-powered information synthesis")
    print("✅ Real source links")
    print("✅ Search history tracking")

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
        show_next_steps()
        print("\n🎉 Ready to use!")
    else:
        print("\n⚠️  Setup completed with some issues")

if __name__ == "__main__":
    main()