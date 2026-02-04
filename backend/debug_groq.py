from groq import Groq
import os

print("Testing Groq import...")
try:
    client = Groq(api_key="gsk_test")
    print("✅ Groq client initialized successfully")
except Exception as e:
    print(f"❌ Groq init failed: {e}")
    import traceback
    traceback.print_exc()
