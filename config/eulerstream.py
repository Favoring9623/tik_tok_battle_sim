"""
EulerStream API Key Configuration

To get your free API key:
1. Go to https://www.eulerstream.com
2. Sign in with GitHub, Discord, or email
3. Copy your API key from the dashboard
4. Paste it below

Free tier includes:
- 1,000 requests/day
- 25 daily captcha credits
- 10 cloud WebSockets
"""

# Paste your EulerStream API key here
EULERSTREAM_API_KEY = "euler_MmM4YmZiYjk4YWJiYTRiYTY4NGIwNTYwOWE0ZTk4ZWQ4ZjViYjE3YzRkZjk1MzAwM2EwMjIz"


def configure_tiktok_live():
    """Configure TikTokLive with the EulerStream API key."""
    if EULERSTREAM_API_KEY:
        try:
            from TikTokLive.client.web.web_settings import WebDefaults
            WebDefaults.tiktok_sign_api_key = EULERSTREAM_API_KEY
            print(f"✅ EulerStream API key configured")
            return True
        except ImportError:
            print("❌ TikTokLive not installed")
            return False
    else:
        print("⚠️  No EulerStream API key configured - using rate-limited defaults")
        return False


# Auto-configure when imported
if EULERSTREAM_API_KEY:
    configure_tiktok_live()
