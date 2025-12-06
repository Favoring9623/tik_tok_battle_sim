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

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_battles_started ON battles(started_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_battle ON battle_events(battle_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_agent_stats_battle ON agent_stats(battle_id)')


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


# Initialize database on module import
init_database()
