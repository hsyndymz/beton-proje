import google.generativeai as genai
import os

# Using the key found in app.py
os.environ["GOOGLE_API_KEY"] = "AIzaSyAXRV-0bk3JYSpu6tgvcGpNttoq4eVKl_8"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
except Exception as e:
    print(f"Error: {e}")
