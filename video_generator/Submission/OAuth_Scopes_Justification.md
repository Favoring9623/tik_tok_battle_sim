# TikTok Battle Simulator - OAuth Scopes Justification

## Application Overview
TikTok Battle Simulator is a real-time live battle platform that enables creators to compete through gift-based scoring during live streams. The application provides dashboards, analytics, and OBS overlays for streamers.

---

## Requested OAuth Scopes

### 1. `user.info.basic`

**Purpose:** User Authentication & Profile Display

**How it's used:**
- Authenticate users securely via TikTok Login
- Display the user's username and profile picture in the dashboard
- Personalize the user experience with their TikTok identity
- Show user identity in leaderboards and battle history

**Data accessed:**
- Username (display_name)
- Profile image URL (avatar_url)
- User ID (for session management only)

**Why it's necessary:**
Users need to log in to access personalized features like their battle history, saved settings, and leaderboard rankings. Without this scope, we cannot identify users or provide a personalized experience.

**Video demonstration:** 00:12-00:20 (OAuth login flow)

---

### 2. `live.room.info`

**Purpose:** Live Room Detection & Connection

**How it's used:**
- Check if a TikTok creator is currently live streaming
- Get live room details (room_id) to connect to the stream
- Display live status indicators in the battle setup interface
- Enable real-time connection to active live rooms

**Data accessed:**
- Live room status (is_live)
- Room ID (room_id)
- Stream title
- Viewer count (for display only)

**Why it's necessary:**
The core functionality of our application is tracking live battles between creators. We need to detect which creators are live and connect to their rooms to track gift events in real-time. Without this scope, we cannot provide the live battle functionality.

**Video demonstration:** 00:20-00:30 (Battle setup with live detection)

---

### 3. `live.gift.info`

**Purpose:** Real-time Gift Tracking & Scoring

**How it's used:**
- Track gifts sent during live battles in real-time
- Calculate battle scores based on gift values
- Display gift animations and notifications
- Build leaderboards of top gifters
- Generate post-battle analytics and replays

**Data accessed:**
- Gift events (gift_id, gift_name, coin value)
- Sender information (username, for leaderboard)
- Gift timestamps (for replay functionality)

**Why it's necessary:**
Gift tracking is the fundamental feature of TikTok Battle Simulator. The entire scoring system is based on gifts sent during live streams. Without this scope, we cannot:
- Track battle scores
- Show real-time gift animations
- Build gifter leaderboards
- Generate battle replays and analytics

**Video demonstration:** 00:38-00:55 (Gift tracking, leaderboards, analytics)

---

## Data Privacy & Security

### Data We Store:
- Battle history (scores, timestamps, participant usernames)
- Aggregated gift statistics (no personal financial data)
- User preferences and settings

### Data We DO NOT Store:
- TikTok access tokens (session-only)
- Personal financial information
- Private messages or comments
- Follower/following lists

### Data Retention:
- Battle data: 90 days
- User sessions: Until logout
- Analytics: Aggregated only, anonymized after 30 days

---

## Scope Usage Summary Table

| Scope | Feature | Data Used | User Benefit |
|-------|---------|-----------|--------------|
| `user.info.basic` | Login & Profile | Username, Avatar | Personalized experience |
| `live.room.info` | Live Detection | Room status, ID | Connect to live battles |
| `live.gift.info` | Gift Tracking | Gift events | Real-time scoring & analytics |

---

## Contact

- **Website:** https://orionlabs.live
- **Privacy Policy:** https://orionlabs.live/privacy
- **Support:** orion.intelligence@protonmail.com

---

*Document prepared for TikTok Developer Portal submission*
*Last updated: January 2026*
