#!/usr/bin/env python3
"""
Test the fixed configuration
"""

def test_config_fix():
    """Test that the config loads without validation errors"""
    
    print("🔧 Testing Fixed Configuration")
    print("=" * 40)
    
    try:
        # Test logging import first
        from app.core.logging import setup_logging, get_logger
        print("✅ app.core.logging imported successfully")
        
        # Test config import
        from app.core.config import settings, get_firebase
        print("✅ app.core.config imported successfully")
        
        # Test settings access
        print(f"✅ Settings loaded: {settings.APP_NAME}")
        print(f"✅ Environment: {settings.ENVIRONMENT}")
        print(f"✅ Debug mode: {settings.DEBUG}")
        
        # Check if API keys are set
        if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY != "your_openai_api_key_here":
            print("✅ OpenAI API key is configured")
        else:
            print("⚠️  OpenAI API key needs to be set in .env")
        
        if hasattr(settings, 'TAVILY_API_KEY') and settings.TAVILY_API_KEY != "your_tavily_api_key_here":
            print("✅ Tavily API key is configured")
        else:
            print("⚠️  Tavily API key needs to be set in .env")
        
        # Test logger creation
        logger = get_logger("test")
        print("✅ Logger created successfully")
        
        print("\n🎉 Configuration fix successful!")
        print("All validation errors resolved.")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    
    print("🚀 Configuration Fix Test")
    print("=" * 40)
    
    # Test the fix
    success = test_config_fix()
    
    if success:
        print("\n✅ SUCCESS: Configuration is now working!")
        print("\nNext steps:")
        print("1. Make sure your .env file has valid API keys")
        print("2. Run: python app/main.py")
        print("3. Visit: http://localhost:8000")
    else:
        print("\n❌ Configuration still has issues.")
        print("Check the error messages above.")

if __name__ == "__main__":
    main()