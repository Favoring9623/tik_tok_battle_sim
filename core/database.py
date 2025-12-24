"""
Database module for persisting battle history and statistics.
Uses SQLite for simplicity and portability.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


DATABASE_PATH = os.environ.get('DATABASE_PATH', 'data/battles.db')


def get_db_path() -> str:
    """Get database path, creating directory if needed."""
    db_path = DATABASE_PATH
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)
    return db_path


@contextmanager
def get_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize database tables."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Battles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battles (
                id TEXT PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                duration INTEGER,
                creator_score INTEGER DEFAULT 0,
                opponent_score INTEGER DEFAULT 0,
                winner TEXT,
                battle_type TEXT DEFAULT 'standard',
                config TEXT,
                analytics TEXT
            )
        ''')

        # Battle events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS battle_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id TEXT,
                timestamp REAL,
                event_type TEXT,
                data TEXT,
                FOREIGN KEY (battle_id) REFERENCES battles(id)
            )
        ''')

        # Agent statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id TEXT,
                agent_name TEXT,
                agent_type TEXT,
                total_points INTEGER DEFAULT 0,
                total_gifts INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                efficiency REAL DEFAULT 0,
                FOREIGN KEY (battle_id) REFERENCES battles(id)
            )
        ''')

        # Tournaments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id TEXT PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ended_at TIMESTAMP,
                format TEXT,
                battles_to_win INTEGER,
                creator_wins INTEGER DEFAULT 0,
                opponent_wins INTEGER DEFAULT 0,
                winner TEXT,
                config TEXT
            )
        ''')

        # Tournament battles (link table)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tournament_battles (
                tournament_id TEXT,
                battle_id TEXT,
                battle_number INTEGER,
                PRIMARY KEY (tournament_id, battle_id),
                FOREIGN KEY (tournament_id) REFERENCES tournaments(id),
                FOREIGN KEY (battle_id) REFERENCES battles(id)
            )
        ''')

        # Users table (for authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_admin INTEGER DEFAULT 0
            )
        ''')

        # Leaderboard - aggregated agent stats
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_agents (
                agent_name TEXT PRIMARY KEY,
                agent_type TEXT,
                total_battles INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                total_points INTEGER DEFAULT 0,
                total_gifts INTEGER DEFAULT 0,
                total_spent INTEGER DEFAULT 0,
                avg_points_per_battle REAL DEFAULT 0,
                best_single_battle INTEGER DEFAULT 0,
                last_battle_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Leaderboard - top gifters (for live battles)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leaderboard_gifters (
                username TEXT PRIMARY KEY,
                total_gifts INTEGER DEFAULT 0,
                total_coins INTEGER DEFAULT 0,
                total_battles INTEGER DEFAULT 0,
                favorite_gift TEXT,
                last_gift_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_battles_started ON battles(started_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_battle ON battle_events(battle_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_stats_battle ON agent_stats(battle_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leaderboard_agents_points ON leaderboard_agents(total_points DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_leaderboard_gifters_coins ON leaderboard_gifters(total_coins DESC)')


class BattleRepository:
    """Repository for battle data operations."""

    @staticmethod
    def create_battle(battle_id: str, duration: int, battle_type: str = 'standard',
                      config: Optional[Dict] = None) -> str:
        """Create a new battle record."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO battles (id, duration, battle_type, config)
                VALUES (?, ?, ?, ?)
            ''', (battle_id, duration, battle_type, json.dumps(config or {})))
        return battle_id

    @staticmethod
    def end_battle(battle_id: str, creator_score: int, opponent_score: int,
                   winner: str, analytics: Optional[Dict] = None):
        """Update battle with final results."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE battles
                SET ended_at = ?, creator_score = ?, opponent_score = ?,
                    winner = ?, analytics = ?
                WHERE id = ?
            ''', (datetime.now(), creator_score, opponent_score, winner,
                  json.dumps(analytics or {}), battle_id))

    @staticmethod
    def add_event(battle_id: str, timestamp: float, event_type: str, data: Dict):
        """Add an event to battle history."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO battle_events (battle_id, timestamp, event_type, data)
                VALUES (?, ?, ?, ?)
            ''', (battle_id, timestamp, event_type, json.dumps(data)))

    @staticmethod
    def add_agent_stats(battle_id: str, agent_name: str, agent_type: str,
                        total_points: int, total_gifts: int, total_spent: int,
                        efficiency: float):
        """Add agent statistics for a battle."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO agent_stats
                (battle_id, agent_name, agent_type, total_points, total_gifts, total_spent, efficiency)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (battle_id, agent_name, agent_type, total_points, total_gifts,
                  total_spent, efficiency))

    @staticmethod
    def get_battle(battle_id: str) -> Optional[Dict]:
        """Get a battle by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM battles WHERE id = ?', (battle_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['config'] = json.loads(result['config']) if result['config'] else {}
                result['analytics'] = json.loads(result['analytics']) if result['analytics'] else {}
                return result
        return None

    @staticmethod
    def get_battle_events(battle_id: str) -> List[Dict]:
        """Get all events for a battle."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM battle_events
                WHERE battle_id = ?
                ORDER BY timestamp
            ''', (battle_id,))
            events = []
            for row in cursor.fetchall():
                event = dict(row)
                event['data'] = json.loads(event['data']) if event['data'] else {}
                events.append(event)
            return events

    @staticmethod
    def get_recent_battles(limit: int = 20) -> List[Dict]:
        """Get recent battles."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM battles
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            battles = []
            for row in cursor.fetchall():
                battle = dict(row)
                battle['config'] = json.loads(battle['config']) if battle['config'] else {}
                battle['analytics'] = json.loads(battle['analytics']) if battle['analytics'] else {}
                battles.append(battle)
            return battles

    @staticmethod
    def get_statistics() -> Dict:
        """Get overall battle statistics."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Total battles
            cursor.execute('SELECT COUNT(*) as total FROM battles WHERE ended_at IS NOT NULL')
            total = cursor.fetchone()['total']

            # Win rates
            cursor.execute('''
                SELECT winner, COUNT(*) as wins
                FROM battles
                WHERE ended_at IS NOT NULL AND winner IS NOT NULL
                GROUP BY winner
            ''')
            wins = {row['winner']: row['wins'] for row in cursor.fetchall()}

            # Average scores
            cursor.execute('''
                SELECT
                    AVG(creator_score) as avg_creator,
                    AVG(opponent_score) as avg_opponent
                FROM battles
                WHERE ended_at IS NOT NULL
            ''')
            avg = cursor.fetchone()

            return {
                'total_battles': total,
                'creator_wins': wins.get('creator', 0),
                'opponent_wins': wins.get('opponent', 0),
                'creator_win_rate': wins.get('creator', 0) / total if total > 0 else 0,
                'avg_creator_score': avg['avg_creator'] or 0,
                'avg_opponent_score': avg['avg_opponent'] or 0
            }

    @staticmethod
    def get_advanced_statistics() -> Dict:
        """Get comprehensive analytics data."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Basic stats
            cursor.execute('SELECT COUNT(*) as total FROM battles WHERE ended_at IS NOT NULL')
            total = cursor.fetchone()['total']

            # Win distribution
            cursor.execute('''
                SELECT winner, COUNT(*) as wins
                FROM battles
                WHERE ended_at IS NOT NULL AND winner IS NOT NULL
                GROUP BY winner
            ''')
            wins = {row['winner']: row['wins'] for row in cursor.fetchall()}

            # Score statistics
            cursor.execute('''
                SELECT
                    AVG(creator_score) as avg_creator,
                    AVG(opponent_score) as avg_opponent,
                    MAX(creator_score) as max_creator,
                    MAX(opponent_score) as max_opponent,
                    MIN(creator_score) as min_creator,
                    MIN(opponent_score) as min_opponent,
                    AVG(creator_score + opponent_score) as avg_total,
                    AVG(ABS(creator_score - opponent_score)) as avg_margin
                FROM battles
                WHERE ended_at IS NOT NULL
            ''')
            scores = cursor.fetchone()

            # Battles per day (last 30 days)
            cursor.execute('''
                SELECT DATE(started_at) as date, COUNT(*) as count
                FROM battles
                WHERE started_at >= DATE('now', '-30 days')
                GROUP BY DATE(started_at)
                ORDER BY date
            ''')
            battles_per_day = [{'date': row['date'], 'count': row['count']}
                              for row in cursor.fetchall()]

            # Battle type distribution
            cursor.execute('''
                SELECT battle_type, COUNT(*) as count
                FROM battles
                WHERE ended_at IS NOT NULL
                GROUP BY battle_type
            ''')
            battle_types = {row['battle_type']: row['count'] for row in cursor.fetchall()}

            # Close battles (margin < 10%)
            cursor.execute('''
                SELECT COUNT(*) as close_battles
                FROM battles
                WHERE ended_at IS NOT NULL
                AND ABS(creator_score - opponent_score) <
                    (creator_score + opponent_score) * 0.1
            ''')
            close_battles = cursor.fetchone()['close_battles']

            return {
                'total_battles': total,
                'creator_wins': wins.get('creator', 0),
                'opponent_wins': wins.get('opponent', 0),
                'ties': wins.get('tie', 0),
                'creator_win_rate': round(wins.get('creator', 0) / total * 100, 1) if total > 0 else 0,
                'opponent_win_rate': round(wins.get('opponent', 0) / total * 100, 1) if total > 0 else 0,
                'avg_creator_score': round(scores['avg_creator'] or 0),
                'avg_opponent_score': round(scores['avg_opponent'] or 0),
                'max_creator_score': scores['max_creator'] or 0,
                'max_opponent_score': scores['max_opponent'] or 0,
                'avg_total_score': round(scores['avg_total'] or 0),
                'avg_margin': round(scores['avg_margin'] or 0),
                'close_battles': close_battles,
                'close_battle_rate': round(close_battles / total * 100, 1) if total > 0 else 0,
                'battles_per_day': battles_per_day,
                'battle_types': battle_types
            }

    @staticmethod
    def get_agent_statistics() -> List[Dict]:
        """Get aggregated agent performance statistics."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT
                    agent_name,
                    agent_type,
                    COUNT(*) as battles,
                    SUM(total_points) as total_points,
                    AVG(total_points) as avg_points,
                    SUM(total_gifts) as total_gifts,
                    AVG(total_gifts) as avg_gifts,
                    SUM(total_spent) as total_spent,
                    AVG(efficiency) as avg_efficiency
                FROM agent_stats
                GROUP BY agent_name, agent_type
                ORDER BY total_points DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_score_distribution() -> Dict:
        """Get score distribution for histogram."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Creator score distribution
            cursor.execute('''
                SELECT
                    CASE
                        WHEN creator_score < 50000 THEN '0-50K'
                        WHEN creator_score < 100000 THEN '50K-100K'
                        WHEN creator_score < 200000 THEN '100K-200K'
                        WHEN creator_score < 300000 THEN '200K-300K'
                        WHEN creator_score < 500000 THEN '300K-500K'
                        ELSE '500K+'
                    END as range,
                    COUNT(*) as count
                FROM battles
                WHERE ended_at IS NOT NULL
                GROUP BY range
                ORDER BY creator_score
            ''')
            creator_dist = {row['range']: row['count'] for row in cursor.fetchall()}

            # Opponent score distribution
            cursor.execute('''
                SELECT
                    CASE
                        WHEN opponent_score < 50000 THEN '0-50K'
                        WHEN opponent_score < 100000 THEN '50K-100K'
                        WHEN opponent_score < 200000 THEN '100K-200K'
                        WHEN opponent_score < 300000 THEN '200K-300K'
                        WHEN opponent_score < 500000 THEN '300K-500K'
                        ELSE '500K+'
                    END as range,
                    COUNT(*) as count
                FROM battles
                WHERE ended_at IS NOT NULL
                GROUP BY range
            ''')
            opponent_dist = {row['range']: row['count'] for row in cursor.fetchall()}

            return {
                'ranges': ['0-50K', '50K-100K', '100K-200K', '200K-300K', '300K-500K', '500K+'],
                'creator': creator_dist,
                'opponent': opponent_dist
            }

    @staticmethod
    def get_battle_timeline(battle_id: str) -> List[Dict]:
        """Get score progression over time for a battle."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, event_type, data
                FROM battle_events
                WHERE battle_id = ?
                AND event_type = 'gift_sent'
                ORDER BY timestamp
            ''', (battle_id,))

            timeline = []
            creator_score = 0
            opponent_score = 0

            for row in cursor.fetchall():
                data = json.loads(row['data']) if row['data'] else {}
                if data.get('team') == 'creator':
                    creator_score += data.get('points', 0)
                else:
                    opponent_score += data.get('points', 0)

                timeline.append({
                    'time': row['timestamp'],
                    'creator_score': creator_score,
                    'opponent_score': opponent_score,
                    'event': data
                })

            return timeline


class TournamentRepository:
    """Repository for tournament data operations."""

    @staticmethod
    def create_tournament(tournament_id: str, format: str, battles_to_win: int,
                          config: Optional[Dict] = None) -> str:
        """Create a new tournament record."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tournaments (id, format, battles_to_win, config)
                VALUES (?, ?, ?, ?)
            ''', (tournament_id, format, battles_to_win, json.dumps(config or {})))
        return tournament_id

    @staticmethod
    def update_tournament(tournament_id: str, creator_wins: int, opponent_wins: int,
                          winner: Optional[str] = None):
        """Update tournament progress."""
        with get_connection() as conn:
            cursor = conn.cursor()
            if winner:
                cursor.execute('''
                    UPDATE tournaments
                    SET creator_wins = ?, opponent_wins = ?, winner = ?, ended_at = ?
                    WHERE id = ?
                ''', (creator_wins, opponent_wins, winner, datetime.now(), tournament_id))
            else:
                cursor.execute('''
                    UPDATE tournaments
                    SET creator_wins = ?, opponent_wins = ?
                    WHERE id = ?
                ''', (creator_wins, opponent_wins, tournament_id))

    @staticmethod
    def link_battle(tournament_id: str, battle_id: str, battle_number: int):
        """Link a battle to a tournament."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tournament_battles (tournament_id, battle_id, battle_number)
                VALUES (?, ?, ?)
            ''', (tournament_id, battle_id, battle_number))

    @staticmethod
    def get_tournament(tournament_id: str) -> Optional[Dict]:
        """Get a tournament by ID."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tournaments WHERE id = ?', (tournament_id,))
            row = cursor.fetchone()
            if row:
                result = dict(row)
                result['config'] = json.loads(result['config']) if result['config'] else {}
                return result
        return None

    @staticmethod
    def get_recent_tournaments(limit: int = 10) -> List[Dict]:
        """Get recent tournaments."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM tournaments
                ORDER BY started_at DESC
                LIMIT ?
            ''', (limit,))
            tournaments = []
            for row in cursor.fetchall():
                tournament = dict(row)
                tournament['config'] = json.loads(tournament['config']) if tournament['config'] else {}
                tournaments.append(tournament)
            return tournaments


class ReplayRepository:
    """Repository for battle replay operations."""

    @staticmethod
    def get_replay_list(limit: int = 20) -> List[Dict]:
        """Get list of battles available for replay."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT b.id, b.started_at, b.duration, b.creator_score,
                       b.opponent_score, b.winner, b.battle_type,
                       (SELECT COUNT(*) FROM battle_events WHERE battle_id = b.id) as event_count
                FROM battles b
                WHERE b.ended_at IS NOT NULL
                ORDER BY b.started_at DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_replay_data(battle_id: str) -> Optional[Dict]:
        """Get full replay data for a battle."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get battle info
            cursor.execute('SELECT * FROM battles WHERE id = ?', (battle_id,))
            battle_row = cursor.fetchone()
            if not battle_row:
                return None

            battle = dict(battle_row)
            battle['config'] = json.loads(battle['config']) if battle['config'] else {}
            battle['analytics'] = json.loads(battle['analytics']) if battle['analytics'] else {}

            # Get all events
            cursor.execute('''
                SELECT timestamp, event_type, data
                FROM battle_events
                WHERE battle_id = ?
                ORDER BY timestamp ASC
            ''', (battle_id,))

            events = []
            for row in cursor.fetchall():
                event = {
                    'timestamp': row['timestamp'],
                    'event_type': row['event_type'],
                    'data': json.loads(row['data']) if row['data'] else {}
                }
                events.append(event)

            # Get agent stats
            cursor.execute('''
                SELECT agent_name, agent_type, total_points, total_gifts, efficiency
                FROM agent_stats
                WHERE battle_id = ?
            ''', (battle_id,))
            agents = [dict(row) for row in cursor.fetchall()]

            return {
                'battle': battle,
                'events': events,
                'agents': agents,
                'event_count': len(events),
                'duration': battle['duration']
            }

    @staticmethod
    def save_replay_event(battle_id: str, timestamp: float, event_type: str, data: Dict):
        """Save a replay event."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO battle_events (battle_id, timestamp, event_type, data)
                VALUES (?, ?, ?, ?)
            ''', (battle_id, timestamp, event_type, json.dumps(data)))

    @staticmethod
    def get_replay_events_range(battle_id: str, start_time: float, end_time: float) -> List[Dict]:
        """Get events within a time range for seeking."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT timestamp, event_type, data
                FROM battle_events
                WHERE battle_id = ? AND timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            ''', (battle_id, start_time, end_time))

            events = []
            for row in cursor.fetchall():
                event = {
                    'timestamp': row['timestamp'],
                    'event_type': row['event_type'],
                    'data': json.loads(row['data']) if row['data'] else {}
                }
                events.append(event)
            return events

    @staticmethod
    def get_state_at_time(battle_id: str, target_time: float) -> Dict:
        """Reconstruct battle state at a specific time for seeking."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get all events up to target time
            cursor.execute('''
                SELECT timestamp, event_type, data
                FROM battle_events
                WHERE battle_id = ? AND timestamp <= ?
                ORDER BY timestamp ASC
            ''', (battle_id, target_time))

            # Reconstruct state
            state = {
                'creator_score': 0,
                'opponent_score': 0,
                'current_phase': 'normal',
                'multiplier': 1.0,
                'gifts': [],
                'power_ups_used': [],
                'glove_active': False
            }

            for row in cursor.fetchall():
                event_type = row['event_type']
                data = json.loads(row['data']) if row['data'] else {}

                if event_type == 'gift_sent':
                    if data.get('team') == 'creator':
                        state['creator_score'] += data.get('points', 0)
                    else:
                        state['opponent_score'] += data.get('points', 0)
                    state['gifts'].append(data)

                elif event_type == 'phase_change':
                    state['current_phase'] = data.get('phase', 'normal')
                    state['multiplier'] = data.get('multiplier', 1.0)

                elif event_type == 'power_up':
                    state['power_ups_used'].append(data)

                elif event_type == 'glove_activated':
                    state['glove_active'] = True

                elif event_type == 'glove_ended':
                    state['glove_active'] = False

            return state


class LeaderboardRepository:
    """Repository for leaderboard data operations."""

    @staticmethod
    def get_top_agents(limit: int = 20, sort_by: str = 'total_points') -> List[Dict]:
        """Get top agents sorted by specified metric."""
        valid_sorts = ['total_points', 'total_wins', 'total_battles', 'avg_points_per_battle', 'best_single_battle']
        if sort_by not in valid_sorts:
            sort_by = 'total_points'

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT * FROM leaderboard_agents
                WHERE total_battles > 0
                ORDER BY {sort_by} DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_top_gifters(limit: int = 20, sort_by: str = 'total_coins') -> List[Dict]:
        """Get top gifters sorted by specified metric."""
        valid_sorts = ['total_coins', 'total_gifts', 'total_battles']
        if sort_by not in valid_sorts:
            sort_by = 'total_coins'

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                SELECT * FROM leaderboard_gifters
                WHERE total_gifts > 0
                ORDER BY {sort_by} DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def update_agent_stats(agent_name: str, agent_type: str, points: int,
                           gifts: int, spent: int, won: bool):
        """Update agent leaderboard stats after a battle."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if agent exists
            cursor.execute('SELECT * FROM leaderboard_agents WHERE agent_name = ?', (agent_name,))
            existing = cursor.fetchone()

            if existing:
                # Update existing agent
                new_battles = existing['total_battles'] + 1
                new_wins = existing['total_wins'] + (1 if won else 0)
                new_points = existing['total_points'] + points
                new_gifts = existing['total_gifts'] + gifts
                new_spent = existing['total_spent'] + spent
                new_avg = new_points / new_battles if new_battles > 0 else 0
                new_best = max(existing['best_single_battle'], points)

                cursor.execute('''
                    UPDATE leaderboard_agents
                    SET total_battles = ?, total_wins = ?, total_points = ?,
                        total_gifts = ?, total_spent = ?, avg_points_per_battle = ?,
                        best_single_battle = ?, last_battle_at = ?
                    WHERE agent_name = ?
                ''', (new_battles, new_wins, new_points, new_gifts, new_spent,
                      new_avg, new_best, datetime.now(), agent_name))
            else:
                # Insert new agent
                cursor.execute('''
                    INSERT INTO leaderboard_agents
                    (agent_name, agent_type, total_battles, total_wins, total_points,
                     total_gifts, total_spent, avg_points_per_battle, best_single_battle, last_battle_at)
                    VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                ''', (agent_name, agent_type, 1 if won else 0, points, gifts, spent,
                      points, points, datetime.now()))

    @staticmethod
    def update_gifter_stats(username: str, gift_name: str, coins: int):
        """Update gifter leaderboard stats after a gift."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Check if gifter exists
            cursor.execute('SELECT * FROM leaderboard_gifters WHERE username = ?', (username,))
            existing = cursor.fetchone()

            if existing:
                # Update existing gifter
                new_gifts = existing['total_gifts'] + 1
                new_coins = existing['total_coins'] + coins

                # Track favorite gift (most common)
                cursor.execute('''
                    UPDATE leaderboard_gifters
                    SET total_gifts = ?, total_coins = ?, last_gift_at = ?
                    WHERE username = ?
                ''', (new_gifts, new_coins, datetime.now(), username))
            else:
                # Insert new gifter
                cursor.execute('''
                    INSERT INTO leaderboard_gifters
                    (username, total_gifts, total_coins, total_battles, favorite_gift, last_gift_at)
                    VALUES (?, 1, ?, 1, ?, ?)
                ''', (username, coins, gift_name, datetime.now()))

    @staticmethod
    def increment_gifter_battles(username: str):
        """Increment battle count for a gifter."""
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE leaderboard_gifters
                SET total_battles = total_battles + 1
                WHERE username = ?
            ''', (username,))

    @staticmethod
    def get_agent_rank(agent_name: str) -> Optional[Dict]:
        """Get an agent's rank and stats."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get agent stats
            cursor.execute('SELECT * FROM leaderboard_agents WHERE agent_name = ?', (agent_name,))
            agent = cursor.fetchone()

            if not agent:
                return None

            # Get rank by points
            cursor.execute('''
                SELECT COUNT(*) + 1 as rank
                FROM leaderboard_agents
                WHERE total_points > (SELECT total_points FROM leaderboard_agents WHERE agent_name = ?)
            ''', (agent_name,))
            rank = cursor.fetchone()['rank']

            result = dict(agent)
            result['rank'] = rank
            return result

    @staticmethod
    def get_gifter_rank(username: str) -> Optional[Dict]:
        """Get a gifter's rank and stats."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get gifter stats
            cursor.execute('SELECT * FROM leaderboard_gifters WHERE username = ?', (username,))
            gifter = cursor.fetchone()

            if not gifter:
                return None

            # Get rank by coins
            cursor.execute('''
                SELECT COUNT(*) + 1 as rank
                FROM leaderboard_gifters
                WHERE total_coins > (SELECT total_coins FROM leaderboard_gifters WHERE username = ?)
            ''', (username,))
            rank = cursor.fetchone()['rank']

            result = dict(gifter)
            result['rank'] = rank
            return result

    @staticmethod
    def get_leaderboard_summary() -> Dict:
        """Get summary stats for leaderboard page."""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Agent stats
            cursor.execute('SELECT COUNT(*) as count, SUM(total_battles) as battles FROM leaderboard_agents')
            agent_summary = cursor.fetchone()

            # Gifter stats
            cursor.execute('SELECT COUNT(*) as count, SUM(total_coins) as coins FROM leaderboard_gifters')
            gifter_summary = cursor.fetchone()

            # Top agent
            cursor.execute('SELECT agent_name, total_points FROM leaderboard_agents ORDER BY total_points DESC LIMIT 1')
            top_agent = cursor.fetchone()

            # Top gifter
            cursor.execute('SELECT username, total_coins FROM leaderboard_gifters ORDER BY total_coins DESC LIMIT 1')
            top_gifter = cursor.fetchone()

            return {
                'total_agents': agent_summary['count'] or 0,
                'total_agent_battles': agent_summary['battles'] or 0,
                'total_gifters': gifter_summary['count'] or 0,
                'total_coins_gifted': gifter_summary['coins'] or 0,
                'top_agent': dict(top_agent) if top_agent else None,
                'top_gifter': dict(top_gifter) if top_gifter else None
            }


# Initialize database on module import
init_database()
