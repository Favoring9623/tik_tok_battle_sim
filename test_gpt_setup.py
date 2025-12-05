#!/usr/bin/env python3
"""
Quick test to verify GPT setup is working.

Tests:
1. API key is set
2. OpenAI package is installed
3. API key is valid
4. Can make simple GPT call
"""

import os
import sys

def test_api_key():
    """Check if API key is set."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("❌ OPENAI_API_KEY not set")
        print("\nTo fix:")
        print("  export OPENAI_API_KEY='your-key-here'")
        return False

    if not api_key.startswith("sk-"):
        print("⚠️  API key doesn't start with 'sk-' - might be invalid")
        return False

    print(f"✅ API key set (length: {len(api_key)} chars)")
    print(f"   Starts with: {api_key[:7]}...")
    print(f"   Ends with: ...{api_key[-4:]}")
    return True

def test_openai_package():
    """Check if OpenAI package is installed."""
    try:
        import openai
        print(f"✅ OpenAI package installed (version {openai.__version__})")
        return True
    except ImportError:
        print("❌ OpenAI package not installed")
        print("\nTo fix:")
        print("  pip install openai")
        return False

def test_api_connection():
    """Test actual API connection."""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        print("\n🔄 Testing API connection...")

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheap model for testing
            messages=[
                {"role": "user", "content": "Say 'API test successful!' and nothing else."}
            ],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        print(f"✅ API connection successful!")
        print(f"   Response: {result}")
        return True

    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 GPT Setup Test")
    print("=" * 60 + "\n")

    # Run tests
    tests = [
        ("API Key", test_api_key),
        ("OpenAI Package", test_openai_package),
        ("API Connection", test_api_connection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {name} test crashed: {e}")
            results.append(False)
        print()

    # Summary
    print("=" * 60)
    print("📊 Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    if all(results):
        print(f"\n✅ All tests passed! ({passed}/{total})")
        print("\n🎉 GPT integration is ready to use!")
        print("\nNext step:")
        print("  python3 demo_gpt_battle.py")
    else:
        print(f"\n⚠️  Some tests failed ({passed}/{total} passed)")
        print("\nFix the issues above and run this test again:")
        print("  python3 test_gpt_setup.py")

    print()

if __name__ == "__main__":
    main()
