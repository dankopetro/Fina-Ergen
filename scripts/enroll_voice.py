#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent
sys.path.append(str(project_root))

from auth.voice_auth import VoiceAuthenticator

def main():
    print("🎙️ Fina Voice Enrollment System 🎙️")
    print("=======================================")
    
    auth = VoiceAuthenticator()
    
    user_name = input("\n👤 Enter the user name to enroll (e.g. 'admin'): ").strip().lower()
    if not user_name:
        print("❌ Invalid name.")
        return
        
    print(f"\n🚀 Starting enrollment for user: {user_name}")
    print("You will be asked to speak 3 phrases.")
    print("Ensure your microphone is ready.")
    
    try:
        success = auth.enroll_new_user(user_name, num_samples=3)
        if success:
            print(f"\n✅ Enrollment successful! Voice profile for '{user_name}' is ready.")
            print("To enable verification, Fina needs to be updated to check this profile.")
        else:
            print("\n❌ Enrollment failed.")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
