# TikTok Developer Portal Submission Guide

**Application:** TikTok Battle Simulator
**Date:** December 6, 2025

---

## 1. App Description (For TikTok Users)

### Short Description (Recommended for form)
```
TikTok Battle Simulator is a real-time battle tracking and visualization platform for TikTok Live gift battles. It enhances the viewer experience by providing live scoreboards, analytics, leaderboards, and AI-powered battle agents. Creators can connect their live streams to display engaging battle overlays, track gifter contributions, and provide an interactive experience for their audience.
```

### Detailed Description
```
TikTok Battle Simulator is an entertainment and analytics platform designed for TikTok Live creators and their audiences.

KEY FEATURES:
- Real-time Battle Tracking: Connects to TikTok Live streams to track and display gift battles between two creators in real-time
- Live Scoreboards: Shows current scores, gift contributions, and battle progress with beautiful visualizations
- AI Battle Agents: Simulates strategic gift-giving patterns for entertainment and training purposes
- Analytics Dashboard: Provides insights on battle performance, gift patterns, and win/loss statistics
- Leaderboards: Ranks top gifters and agents across all battles
- OBS Integration: Streamers can add battle overlays directly to their streaming software
- Audience Interaction: Viewers can vote and trigger power-ups during battles

HOW IT WORKS:
1. Creator connects their TikTok Live stream via our secure integration
2. During a battle, our system receives gift events in real-time
3. Scores are calculated and displayed on an engaging dashboard
4. Analytics are generated for creators to review their performance
5. Top gifters are recognized on public leaderboards

The platform is designed to increase engagement during TikTok Live battles and provide creators with valuable insights into their streaming performance.
```

---

## 2. Products and Scopes Required

### Required Products

| Product | Scope | Usage |
|---------|-------|-------|
| **Login Kit** | `user.info.basic` | Allow users to log in with their TikTok account |
| **Live API** | `live.room.info` | Access live room information to connect to battles |
| **Live API** | `live.gift.info` | Receive real-time gift events during battles |

### Scope Explanations

#### Login Kit - `user.info.basic`
**How it works in our app:**
- When a user clicks "Connect TikTok Account", they are redirected to TikTok's OAuth flow
- Upon authorization, we receive their TikTok username and profile picture
- This information is used to:
  - Display their username on the leaderboard
  - Personalize their dashboard experience
  - Track their battle statistics
- We do NOT access any private data, messages, or content

**Demo Video Timestamp:** 0:00 - 0:30 (Login flow demonstration)

#### Live API - `live.room.info`
**How it works in our app:**
- Creator enters their TikTok username to start a live battle
- Our system uses the Live API to:
  - Verify the creator is currently live
  - Get the room ID for the live session
  - Display the creator's stream information
- This allows us to connect to the correct live stream

**Demo Video Timestamp:** 0:30 - 1:00 (Starting a live battle)

#### Live API - `live.gift.info`
**How it works in our app:**
- Once connected to a live battle, we receive gift events in real-time
- For each gift event, we extract:
  - Gift type (Rose, Galaxy, Universe, etc.)
  - Gift value in coins
  - Sender username
  - Timestamp
- This data is used to:
  - Update the live scoreboard
  - Calculate battle scores
  - Track top gifters
  - Generate analytics

**Demo Video Timestamp:** 1:00 - 2:00 (Gift tracking and scoreboard update)

---

## 3. Demo Video Requirements

### Video 1: Complete Integration Flow (Main Demo)
**Duration:** 3-5 minutes
**Format:** MP4, 1080p

**Required Scenes:**

| Timestamp | Scene | Description |
|-----------|-------|-------------|
| 0:00-0:30 | Login Flow | User clicks "Connect TikTok" → TikTok OAuth → Returns to app with profile |
| 0:30-1:00 | Start Battle | User enters two TikTok usernames → System connects to live streams |
| 1:00-2:00 | Live Tracking | Show gifts appearing → Scores updating → Leaderboard changing |
| 2:00-2:30 | Analytics | Navigate to analytics page → Show battle statistics |
| 2:30-3:00 | Leaderboard | Show top gifters → Show top agents → Rankings display |
| 3:00-3:30 | OBS Integration | Open OBS → Add battle overlay → Show on stream |
| 3:30-4:00 | Battle End | Battle concludes → Winner announced → Stats saved |

### Video 2: Sandbox Environment Test (Optional)
**Duration:** 2-3 minutes
**Format:** MP4, 1080p

**Scenes:**
- Show sandbox environment setup
- Demonstrate API calls with test data
- Verify all scopes work correctly

### Recording Tips
1. **Show the URL bar** to prove you're on your actual domain
2. **Clear browser cache** before recording for clean login flow
3. **Use a test account** (not your personal TikTok)
4. **Narrate or add captions** explaining each step
5. **Highlight data usage** - show exactly what data you access

---

## 4. URLs to Provide

### Production URLs (Replace with your actual domain)

| URL Type | URL |
|----------|-----|
| **Website URL** | `https://your-domain.com` |
| **Privacy Policy** | `https://your-domain.com/privacy` |
| **Terms of Service** | `https://your-domain.com/terms` |
| **API Documentation** | `https://your-domain.com/docs` |
| **OAuth Redirect** | `https://your-domain.com/auth/tiktok/callback` |

### Development/Sandbox URLs
| URL Type | URL |
|----------|-----|
| **Website URL** | `http://localhost:5000` |
| **Privacy Policy** | `http://localhost:5000/privacy` |
| **Terms of Service** | `http://localhost:5000/terms` |
| **API Documentation** | `http://localhost:5000/docs` |

---

## 5. TikTok OAuth Implementation

### Step 1: Get Credentials
After approval, you'll receive:
- `CLIENT_KEY` - Your app's unique identifier
- `CLIENT_SECRET` - Secret key for authentication

### Step 2: Add OAuth Route

Add this code to `web/backend/app.py`:

```python
import requests

TIKTOK_CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY')
TIKTOK_CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET')
TIKTOK_REDIRECT_URI = os.environ.get('TIKTOK_REDIRECT_URI', 'http://localhost:5000/auth/tiktok/callback')

@app.route('/auth/tiktok')
def tiktok_auth():
    """Initiate TikTok OAuth flow."""
    scope = 'user.info.basic,live.room.info,live.gift.info'
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    auth_url = (
        f"https://www.tiktok.com/v2/auth/authorize/"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&redirect_uri={TIKTOK_REDIRECT_URI}"
        f"&state={state}"
    )
    return redirect(auth_url)


@app.route('/auth/tiktok/callback')
def tiktok_callback():
    """Handle TikTok OAuth callback."""
    code = request.args.get('code')
    state = request.args.get('state')

    # Verify state
    if state != session.get('oauth_state'):
        return jsonify({'error': 'Invalid state'}), 400

    # Exchange code for access token
    token_url = 'https://open.tiktokapis.com/v2/oauth/token/'
    response = requests.post(token_url, data={
        'client_key': TIKTOK_CLIENT_KEY,
        'client_secret': TIKTOK_CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code',
        'redirect_uri': TIKTOK_REDIRECT_URI
    })

    token_data = response.json()
    if 'access_token' in token_data:
        session['tiktok_access_token'] = token_data['access_token']
        session['tiktok_open_id'] = token_data['open_id']

        # Get user info
        user_info = get_tiktok_user_info(token_data['access_token'])
        session['tiktok_username'] = user_info.get('display_name')
        session['tiktok_avatar'] = user_info.get('avatar_url')

        return redirect(url_for('index'))

    return jsonify({'error': 'Failed to get access token'}), 400


def get_tiktok_user_info(access_token):
    """Get TikTok user info."""
    response = requests.get(
        'https://open.tiktokapis.com/v2/user/info/',
        headers={'Authorization': f'Bearer {access_token}'},
        params={'fields': 'display_name,avatar_url'}
    )
    return response.json().get('data', {}).get('user', {})
```

### Step 3: Configure Environment Variables

```bash
export TIKTOK_CLIENT_KEY="your_client_key"
export TIKTOK_CLIENT_SECRET="your_client_secret"
export TIKTOK_REDIRECT_URI="https://your-domain.com/auth/tiktok/callback"
```

---

## 6. Live API Integration

### WebSocket Connection for Gift Events

```python
import websocket
import json

def connect_to_live_gifts(room_id, access_token, on_gift_callback):
    """Connect to TikTok Live gift stream."""
    ws_url = f"wss://webcast-ws.tiktok.com/webcast/room/{room_id}/"

    def on_message(ws, message):
        data = json.loads(message)
        if data.get('type') == 'gift':
            gift_event = {
                'username': data['user']['nickname'],
                'gift_name': data['gift']['name'],
                'gift_id': data['gift']['id'],
                'coins': data['gift']['diamond_count'],
                'repeat_count': data.get('repeat_count', 1),
                'timestamp': data['timestamp']
            }
            on_gift_callback(gift_event)

    ws = websocket.WebSocketApp(
        ws_url,
        header={'Authorization': f'Bearer {access_token}'},
        on_message=on_message
    )
    ws.run_forever()
```

---

## 7. Checklist Before Submission

### Documents Ready
- [x] Privacy Policy (`/privacy`)
- [x] Terms of Service (`/terms`)
- [x] API Documentation (`/docs`)
- [x] OpenAPI Specification (`/api/openapi.yaml`)

### Technical Requirements
- [ ] HTTPS enabled on production domain
- [ ] OAuth redirect URI matches exactly
- [ ] All scopes demonstrated in video
- [ ] Rate limiting implemented
- [ ] Error handling for API failures

### Demo Video Checklist
- [ ] Shows login flow with TikTok OAuth
- [ ] Shows live room connection
- [ ] Shows gift events being tracked
- [ ] Shows scoreboard updating in real-time
- [ ] Shows analytics/leaderboard pages
- [ ] URL bar visible throughout
- [ ] Matches the domain in application

### App Review Guidelines Compliance
- [ ] No scraping of TikTok content
- [ ] No storing of user videos
- [ ] Clear data usage disclosure
- [ ] User consent for data collection
- [ ] Age restrictions implemented (13+)

---

## 8. Common Rejection Reasons & Solutions

| Rejection Reason | Solution |
|------------------|----------|
| Demo video doesn't show all scopes | Record a new video showing each scope in use |
| Privacy Policy missing required sections | Use our comprehensive template |
| Redirect URI mismatch | Ensure exact match including trailing slashes |
| Unclear app description | Use our detailed description template |
| Missing sandbox demonstration | Use TikTok Developer Portal sandbox |

---

## 9. Support Contacts

- **TikTok Developer Support:** developers@tiktok.com
- **API Documentation:** https://developers.tiktok.com/doc
- **Our Support:** support@your-domain.com

---

**Good luck with your submission!**
