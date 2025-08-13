"""
Setup script for AI Voice-to-Voice Mock Interview System
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file template"""
    env_content = """# OpenAI API Key for Whisper speech recognition
OPENAI_API_KEY=your_openai_api_key_here

# Google Gemini API Key for AI interview logic
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional: ElevenLabs API Key for premium TTS voices
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# Application Settings
INTERVIEW_QUESTIONS=5
AUDIO_SAMPLE_RATE=16000
AUDIO_CHUNK_SIZE=1024
"""
    
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(env_content)
        print("✅ Created .env file template")
        print("📝 Please edit .env file with your API keys")
        return True
    else:
        print("ℹ️ .env file already exists")
        return True

def create_directories():
    """Create necessary directories"""
    directories = ["temp_audio", "reports"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"ℹ️ Directory already exists: {directory}")

def check_audio_system():
    """Check audio system compatibility"""
    print("🎤 Checking audio system...")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print(f"✅ Audio devices found: {len(devices)}")
        
        # Check for microphone
        input_devices = [d for d in devices if d['max_inputs'] > 0]
        if input_devices:
            print(f"✅ Microphone devices found: {len(input_devices)}")
            for device in input_devices[:3]:  # Show first 3
                print(f"  - {device['name']}")
        else:
            print("⚠️ No microphone devices found")
            
    except ImportError:
        print("❌ sounddevice not installed")
    except Exception as e:
        print(f"❌ Audio system check failed: {e}")

def get_api_keys_info():
    """Display information about required API keys"""
    print("\n🔑 API Keys Required:")
    print("=" * 30)
    print("1. OpenAI API Key:")
    print("   - Used for speech recognition (Whisper)")
    print("   - Get it from: https://platform.openai.com/api-keys")
    print("   - Cost: ~$0.006 per minute of audio")
    print()
    print("2. Google Gemini API Key:")
    print("   - Used for AI interview questions and evaluation")
    print("   - Get it from: https://makersuite.google.com/app/apikey")
    print("   - Cost: Free tier available")
    print()
    print("3. ElevenLabs API Key (Optional):")
    print("   - Used for premium text-to-speech voices")
    print("   - Get it from: https://elevenlabs.io/")
    print("   - Alternative: Free gTTS will be used")

def run_tests():
    """Run basic tests"""
    print("\n🧪 Running basic tests...")
    
    try:
        # Test imports
        import openai
        import google.generativeai
        import librosa
        import webrtcvad
        import sounddevice
        import gtts
        import streamlit
        import reportlab
        import plotly
        
        print("✅ All core modules imported successfully")
        
        # Test configuration
        from config import INTERVIEW_TYPES, DEFAULT_QUESTIONS
        print(f"✅ Configuration loaded: {len(INTERVIEW_TYPES)} interview types")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 AI Voice-to-Voice Mock Interview System Setup")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return
    
    print()
    
    # Create directories
    create_directories()
    
    print()
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed during dependency installation")
        return
    
    print()
    
    # Create .env file
    create_env_file()
    
    print()
    
    # Check audio system
    check_audio_system()
    
    print()
    
    # Get API keys info
    get_api_keys_info()
    
    print()
    
    # Run tests
    if run_tests():
        print("✅ Setup completed successfully!")
        print("\n🎉 Next steps:")
        print("1. Edit .env file with your API keys")
        print("2. Run 'python demo.py' to test the system")
        print("3. Run 'streamlit run app.py' to start the web interface")
    else:
        print("❌ Setup completed with errors")
        print("Please check the error messages above")

if __name__ == "__main__":
    main()
