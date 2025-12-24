# TikTok Battle Simulator - API Documentation

**Version:** 1.0.0
**Base URL:** `https://your-domain.com/api/v1`
**Protocol:** HTTPS
**Format:** JSON

---

## Overview

The TikTok Battle Simulator API provides real-time battle simulation, analytics, and leaderboard services for TikTok Live streams. This API enables third-party developers to integrate battle tracking, scoring, and visualization into their applications.

### Key Features
- Real-time battle state via WebSocket
- RESTful endpoints for battles, analytics, and leaderboards
- Support for live TikTok stream integration
- Comprehensive agent and gifter statistics

---

## Authentication

### API Key Authentication

All API requests require an API key passed in the header:

```http
Authorization: Bearer YOUR_API_KEY
X-API-Key: YOUR_API_KEY
```

### Rate Limits

| Tier | Requests/min | WebSocket Connections |
|------|--------------|----------------------|
| Free | 60 | 1 |
| Pro | 300 | 5 |
| Enterprise | Unlimited | Unlimited |

---

## Endpoints

### Battles

#### List Active Battles
```http
GET /api/v1/battles/active
```

**Response:**
```json
{
  "battles": [
    {
      "id": "battle_abc123",
      "status": "active",
      "creator_score": 45000,
      "opponent_score": 38000,
      "current_time": 45,
      "duration": 60,
      "phase": "boost1",
      "multiplier": 2.0
    }
  ],
  "count": 1
}
```

#### Get Battle Details
```http
GET /api/v1/battles/{battle_id}
```

**Response:**
```json
{
  "id": "battle_abc123",
  "started_at": "2025-12-06T10:30:00Z",
  "duration": 60,
  "battle_type": "strategic",
  "creator_score": 125000,
  "opponent_score": 98000,
  "winner": "creator",
  "agents": [
    {
      "name": "NovaWhale",
      "type": "Strategic Whale",
      "points": 45000,
      "gifts": 12
    }
  ],
  "analytics": {
    "total_gifts": 156,
    "momentum_shifts": 3,
    "closest_margin": 500
  }
}
```

#### Get Battle History
```http
GET /api/v1/battles/history?limit=20&offset=0
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 20 | Number of results (max 100) |
| offset | integer | 0 | Pagination offset |
| battle_type | string | all | Filter: standard, strategic, live |

---

### Live Battles

#### Get Live Battle Status
```http
GET /api/v1/live/status
```

**Response:**
```json
{
  "tiktok_live_available": true,
  "active_battle": true,
  "battle_state": {
    "creator_username": "creator1",
    "opponent_username": "creator2",
    "creator_score": 75000,
    "opponent_score": 68000,
    "creator_connected": true,
    "opponent_connected": true,
    "time_remaining": 120,
    "current_phase": "normal",
    "current_multiplier": 1.0
  }
}
```

#### Start Live Battle
```http
POST /api/v1/live/start
```

**Request Body:**
```json
{
  "creator_username": "creator1",
  "opponent_username": "creator2",
  "duration": 300
}
```

**Response:**
```json
{
  "status": "started",
  "battle_id": "live_xyz789",
  "creator": "creator1",
  "opponent": "creator2",
  "duration": 300
}
```

#### Stop Live Battle
```http
POST /api/v1/live/stop
```

---

### Analytics

#### Get Analytics Overview
```http
GET /api/v1/analytics/overview
```

**Response:**
```json
{
  "total_battles": 1250,
  "creator_wins": 680,
  "opponent_wins": 545,
  "ties": 25,
  "creator_win_rate": 54.4,
  "avg_creator_score": 125000,
  "avg_opponent_score": 118000,
  "avg_margin": 15000,
  "close_battles": 312,
  "close_battle_rate": 25.0,
  "battles_per_day": [
    {"date": "2025-12-01", "count": 45},
    {"date": "2025-12-02", "count": 52}
  ]
}
```

#### Get Agent Statistics
```http
GET /api/v1/analytics/agents
```

**Response:**
```json
{
  "agents": [
    {
      "agent_name": "NovaWhale",
      "agent_type": "Strategic Whale",
      "battles": 250,
      "total_points": 12500000,
      "avg_points": 50000,
      "total_gifts": 3200,
      "avg_efficiency": 0.85
    }
  ]
}
```

#### Get Score Distribution
```http
GET /api/v1/analytics/distribution
```

---

### Leaderboard

#### Get Top Agents
```http
GET /api/v1/leaderboard/agents?sort=total_points&limit=20
```

**Query Parameters:**
| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| sort | string | total_points | total_points, total_wins, total_battles, avg_points_per_battle |
| limit | integer | 20 | 1-100 |

**Response:**
```json
{
  "agents": [
    {
      "agent_name": "NovaWhale",
      "agent_type": "Strategic Whale",
      "total_battles": 500,
      "total_wins": 320,
      "total_points": 25000000,
      "total_gifts": 6500,
      "avg_points_per_battle": 50000,
      "best_single_battle": 185000,
      "last_battle_at": "2025-12-06T10:30:00Z"
    }
  ]
}
```

#### Get Top Gifters
```http
GET /api/v1/leaderboard/gifters?sort=total_coins&limit=20
```

**Query Parameters:**
| Parameter | Type | Default | Options |
|-----------|------|---------|---------|
| sort | string | total_coins | total_coins, total_gifts, total_battles |
| limit | integer | 20 | 1-100 |

**Response:**
```json
{
  "gifters": [
    {
      "username": "whale_supporter",
      "total_gifts": 1500,
      "total_coins": 2500000,
      "total_battles": 45,
      "favorite_gift": "Universe",
      "last_gift_at": "2025-12-06T10:30:00Z"
    }
  ]
}
```

#### Get Leaderboard Summary
```http
GET /api/v1/leaderboard/summary
```

**Response:**
```json
{
  "total_agents": 45,
  "total_agent_battles": 5600,
  "total_gifters": 1200,
  "total_coins_gifted": 125000000,
  "top_agent": {
    "agent_name": "NovaWhale",
    "total_points": 25000000
  },
  "top_gifter": {
    "username": "whale_supporter",
    "total_coins": 2500000
  }
}
```

---

### Replay

#### List Available Replays
```http
GET /api/v1/replay/list?limit=20
```

**Response:**
```json
{
  "replays": [
    {
      "id": "battle_abc123",
      "started_at": "2025-12-06T10:30:00Z",
      "duration": 60,
      "creator_score": 125000,
      "opponent_score": 98000,
      "winner": "creator",
      "event_count": 156
    }
  ]
}
```

#### Get Replay Data
```http
GET /api/v1/replay/{battle_id}
```

**Response:**
```json
{
  "battle": {
    "id": "battle_abc123",
    "duration": 60,
    "creator_score": 125000,
    "opponent_score": 98000
  },
  "events": [
    {
      "timestamp": 5.2,
      "event_type": "gift_sent",
      "data": {
        "agent": "NovaWhale",
        "gift": "Rose",
        "points": 100,
        "team": "creator"
      }
    }
  ],
  "agents": [
    {"agent_name": "NovaWhale", "total_points": 45000}
  ]
}
```

#### Get State at Time
```http
GET /api/v1/replay/{battle_id}/state?time=30.5
```

---

### Audience Interaction

#### Get Vote Counts
```http
GET /api/v1/audience/votes
```

**Response:**
```json
{
  "votes": {
    "creator": 156,
    "opponent": 142
  },
  "total_viewers": 298
}
```

#### Reset Votes
```http
POST /api/v1/audience/reset
```

---

## WebSocket API

### Connection
```javascript
const socket = io('wss://your-domain.com', {
  auth: { token: 'YOUR_API_KEY' }
});
```

### Events

#### Subscribing to Battle Updates
```javascript
socket.on('connect', () => {
  socket.emit('subscribe_battle', { battle_id: 'battle_abc123' });
});
```

#### Receiving Events

| Event | Description |
|-------|-------------|
| `battle_start` | Battle has started |
| `battle_tick` | Periodic state update (every second) |
| `battle_end` | Battle completed |
| `gift_sent` | Gift received |
| `phase_change` | Battle phase changed |
| `power_up` | Power-up activated |
| `agent_action` | Agent performed action |

**Example: battle_tick**
```json
{
  "battle_id": "battle_abc123",
  "time": 45,
  "scores": {
    "creator": 75000,
    "opponent": 68000
  },
  "phase": "boost1",
  "multiplier": 2.0
}
```

**Example: gift_sent**
```json
{
  "battle_id": "battle_abc123",
  "team": "creator",
  "agent": "NovaWhale",
  "gift": "Galaxy",
  "points": 5000,
  "total_creator": 80000,
  "total_opponent": 68000
}
```

---

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "BATTLE_NOT_FOUND",
    "message": "The requested battle does not exist",
    "status": 404
  }
}
```

### Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing API key |
| `RATE_LIMITED` | 429 | Too many requests |
| `BATTLE_NOT_FOUND` | 404 | Battle ID not found |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `SERVER_ERROR` | 500 | Internal server error |

---

## SDKs and Libraries

### Python
```python
from tiktok_battle_sdk import BattleClient

client = BattleClient(api_key="YOUR_API_KEY")
battles = client.get_active_battles()
```

### JavaScript
```javascript
import { BattleClient } from 'tiktok-battle-sdk';

const client = new BattleClient({ apiKey: 'YOUR_API_KEY' });
const battles = await client.getActiveBattles();
```

---

## Changelog

### v1.0.0 (December 2025)
- Initial API release
- Battle management endpoints
- Live TikTok integration
- Analytics and leaderboard
- WebSocket real-time updates
- Replay system

---

## Support

- **Documentation:** https://your-domain.com/docs
- **GitHub:** https://github.com/Favoring9623/tik_tok_battle_sim
- **Email:** support@your-domain.com
