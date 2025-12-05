"""
Battle History Database

Stores and retrieves battle history for agent learning:
- Battle outcomes and statistics
- Agent performance per battle
- Phase timing effectiveness
- Gift timing patterns
- Win/loss conditions
"""

import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path


@dataclass
class BattleRecord:
    """Record of a single battle."""
    battle_id: str
    timestamp: str
    duration: int
    winner: str
    creator_score: int
    opponent_score: int
    margin: int
    boost2_triggered: bool
    gloves_activated: int
    power_ups_used: int
    total_gifts_sent: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentBattleRecord:
    """Record of an agent's performance in a battle."""
    battle_id: str
    agent_name: str
    agent_type: str
    points_donated: int
    gifts_sent: int
    avg_gift_value: float
    best_gift_value: int
    early_phase_gifts: int
    mid_phase_gifts: int
    late_phase_gifts: int
    final_phase_gifts: int
    gloves_sent: int
    gloves_activated: int
    power_ups_used: int
    won: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class GiftTimingRecord:
    """Record of gift timing for pattern analysis."""
    battle_id: str
    agent_name: str
    gift_type: str
    gift_value: int
    timestamp: int
    phase: str
    multiplier: float
    effective_value: int  # value * multiplier
    score_diff_before: int
    activated_x5: bool


class BattleHistoryDB:
    """
    SQLite-based battle history database.

    Provides:
    - Battle storage and retrieval
    - Agent performance history
    - Pattern analysis queries
    - Statistics aggregation
    """

    def __init__(self, db_path: str = "data/battle_history.db"):
        self.db_path = db_path

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        # Battles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battles (
                battle_id TEXT PRIMARY KEY,
                timestamp TEXT,
                duration INTEGER,
                winner TEXT,
                creator_score INTEGER,
                opponent_score INTEGER,
                margin INTEGER,
                boost2_triggered INTEGER,
                gloves_activated INTEGER,
                power_ups_used INTEGER,
                total_gifts_sent INTEGER
            )
        """)

        # Agent performance table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id TEXT,
                agent_name TEXT,
                agent_type TEXT,
                points_donated INTEGER,
                gifts_sent INTEGER,
                avg_gift_value REAL,
                best_gift_value INTEGER,
                early_phase_gifts INTEGER,
                mid_phase_gifts INTEGER,
                late_phase_gifts INTEGER,
                final_phase_gifts INTEGER,
                gloves_sent INTEGER,
                gloves_activated INTEGER,
                power_ups_used INTEGER,
                won INTEGER,
                FOREIGN KEY (battle_id) REFERENCES battles(battle_id)
            )
        """)

        # Gift timing table for detailed analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS gift_timing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                battle_id TEXT,
                agent_name TEXT,
                gift_type TEXT,
                gift_value INTEGER,
                timestamp INTEGER,
                phase TEXT,
                multiplier REAL,
                effective_value INTEGER,
                score_diff_before INTEGER,
                activated_x5 INTEGER,
                FOREIGN KEY (battle_id) REFERENCES battles(battle_id)
            )
        """)

        # Strategy parameters table (for learning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_params (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT,
                param_name TEXT,
                param_value REAL,
                version INTEGER,
                win_rate REAL,
                sample_size INTEGER,
                updated_at TEXT,
                UNIQUE(agent_type, param_name, version)
            )
        """)

        # Agent learning state table (for persistence across sessions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_learning_state (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT UNIQUE,
                agent_type TEXT,
                total_battles INTEGER DEFAULT 0,
                total_wins INTEGER DEFAULT 0,
                performance_history TEXT,
                current_params TEXT,
                epsilon REAL DEFAULT 0.3,
                updated_at TEXT
            )
        """)

        # Q-tables storage (JSON serialized)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS q_tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_type TEXT UNIQUE,
                q_table TEXT,
                episodes INTEGER DEFAULT 0,
                total_rewards REAL DEFAULT 0,
                wins INTEGER DEFAULT 0,
                epsilon REAL DEFAULT 0.3,
                updated_at TEXT
            )
        """)

        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_perf_name
            ON agent_performance(agent_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_gift_timing_agent
            ON gift_timing(agent_name)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_battles_winner
            ON battles(winner)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_learning_state_name
            ON agent_learning_state(agent_name)
        """)

        self.conn.commit()

    def record_battle(self, battle: BattleRecord):
        """Record a battle to the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO battles
            (battle_id, timestamp, duration, winner, creator_score, opponent_score,
             margin, boost2_triggered, gloves_activated, power_ups_used, total_gifts_sent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            battle.battle_id, battle.timestamp, battle.duration,
            battle.winner, battle.creator_score, battle.opponent_score,
            battle.margin, int(battle.boost2_triggered), battle.gloves_activated,
            battle.power_ups_used, battle.total_gifts_sent
        ))
        self.conn.commit()

    def record_agent_performance(self, record: AgentBattleRecord):
        """Record agent performance for a battle."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO agent_performance
            (battle_id, agent_name, agent_type, points_donated, gifts_sent,
             avg_gift_value, best_gift_value, early_phase_gifts, mid_phase_gifts,
             late_phase_gifts, final_phase_gifts, gloves_sent, gloves_activated,
             power_ups_used, won)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.battle_id, record.agent_name, record.agent_type,
            record.points_donated, record.gifts_sent, record.avg_gift_value,
            record.best_gift_value, record.early_phase_gifts, record.mid_phase_gifts,
            record.late_phase_gifts, record.final_phase_gifts, record.gloves_sent,
            record.gloves_activated, record.power_ups_used, int(record.won)
        ))
        self.conn.commit()

    def record_gift_timing(self, record: GiftTimingRecord):
        """Record gift timing for pattern analysis."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO gift_timing
            (battle_id, agent_name, gift_type, gift_value, timestamp, phase,
             multiplier, effective_value, score_diff_before, activated_x5)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.battle_id, record.agent_name, record.gift_type,
            record.gift_value, record.timestamp, record.phase,
            record.multiplier, record.effective_value, record.score_diff_before,
            int(record.activated_x5)
        ))
        self.conn.commit()

    def get_agent_stats(self, agent_name: str) -> Dict:
        """Get aggregate statistics for an agent."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_battles,
                SUM(won) as wins,
                AVG(points_donated) as avg_points,
                SUM(points_donated) as total_points,
                AVG(gifts_sent) as avg_gifts,
                SUM(gloves_activated) as total_gloves_activated,
                SUM(gloves_sent) as total_gloves_sent
            FROM agent_performance
            WHERE agent_name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        if row and row['total_battles'] > 0:
            return {
                'total_battles': row['total_battles'],
                'wins': row['wins'] or 0,
                'win_rate': (row['wins'] or 0) / row['total_battles'],
                'avg_points': row['avg_points'] or 0,
                'total_points': row['total_points'] or 0,
                'avg_gifts': row['avg_gifts'] or 0,
                'glove_success_rate': (
                    (row['total_gloves_activated'] or 0) /
                    max(row['total_gloves_sent'] or 1, 1)
                )
            }
        return {
            'total_battles': 0,
            'wins': 0,
            'win_rate': 0,
            'avg_points': 0,
            'total_points': 0,
            'avg_gifts': 0,
            'glove_success_rate': 0
        }

    def get_optimal_gift_timing(self, agent_type: str) -> Dict:
        """Analyze optimal gift timing patterns from history."""
        cursor = self.conn.cursor()

        # Get effectiveness by phase
        cursor.execute("""
            SELECT
                gt.phase,
                AVG(gt.effective_value) as avg_effective_value,
                COUNT(*) as gift_count,
                SUM(CASE WHEN ap.won = 1 THEN 1 ELSE 0 END) as wins_when_gifted
            FROM gift_timing gt
            JOIN agent_performance ap ON gt.battle_id = ap.battle_id
                AND gt.agent_name = ap.agent_name
            WHERE ap.agent_type = ?
            GROUP BY gt.phase
        """, (agent_type,))

        phase_stats = {}
        for row in cursor.fetchall():
            phase_stats[row['phase']] = {
                'avg_effective_value': row['avg_effective_value'],
                'gift_count': row['gift_count'],
                'win_rate': row['wins_when_gifted'] / max(row['gift_count'], 1)
            }

        # Get glove timing effectiveness
        cursor.execute("""
            SELECT
                phase,
                SUM(activated_x5) as activations,
                COUNT(*) as attempts,
                CAST(SUM(activated_x5) AS REAL) / COUNT(*) as activation_rate
            FROM gift_timing
            WHERE gift_type = 'GLOVE'
            GROUP BY phase
        """)

        glove_stats = {}
        for row in cursor.fetchall():
            glove_stats[row['phase']] = {
                'activations': row['activations'],
                'attempts': row['attempts'],
                'activation_rate': row['activation_rate']
            }

        return {
            'phase_effectiveness': phase_stats,
            'glove_timing': glove_stats
        }

    def get_win_conditions(self, min_samples: int = 10) -> Dict:
        """Analyze common win conditions."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                boost2_triggered,
                AVG(margin) as avg_margin,
                COUNT(*) as count
            FROM battles
            WHERE winner = 'creator'
            GROUP BY boost2_triggered
            HAVING COUNT(*) >= ?
        """, (min_samples,))

        boost2_impact = {}
        for row in cursor.fetchall():
            key = "with_boost2" if row['boost2_triggered'] else "without_boost2"
            boost2_impact[key] = {
                'avg_margin': row['avg_margin'],
                'count': row['count']
            }

        return {
            'boost2_impact': boost2_impact
        }

    def get_learning_data(self, agent_type: str, limit: int = 100) -> List[Dict]:
        """Get recent battle data for learning."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                ap.*,
                b.duration,
                b.boost2_triggered,
                b.margin
            FROM agent_performance ap
            JOIN battles b ON ap.battle_id = b.battle_id
            WHERE ap.agent_type = ?
            ORDER BY b.timestamp DESC
            LIMIT ?
        """, (agent_type, limit))

        return [dict(row) for row in cursor.fetchall()]

    def save_strategy_params(
        self,
        agent_type: str,
        params: Dict[str, float],
        win_rate: float,
        sample_size: int
    ):
        """Save learned strategy parameters."""
        cursor = self.conn.cursor()

        # Get next version
        cursor.execute("""
            SELECT COALESCE(MAX(version), 0) + 1 as next_version
            FROM strategy_params
            WHERE agent_type = ?
        """, (agent_type,))

        version = cursor.fetchone()['next_version']
        timestamp = datetime.now().isoformat()

        for param_name, param_value in params.items():
            cursor.execute("""
                INSERT INTO strategy_params
                (agent_type, param_name, param_value, version, win_rate, sample_size, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (agent_type, param_name, param_value, version, win_rate, sample_size, timestamp))

        self.conn.commit()
        return version

    def get_latest_strategy_params(self, agent_type: str) -> Optional[Dict]:
        """Get the most recent strategy parameters for an agent type."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT param_name, param_value, version, win_rate, sample_size
            FROM strategy_params
            WHERE agent_type = ? AND version = (
                SELECT MAX(version) FROM strategy_params WHERE agent_type = ?
            )
        """, (agent_type, agent_type))

        rows = cursor.fetchall()
        if not rows:
            return None

        params = {}
        meta = {}
        for row in rows:
            params[row['param_name']] = row['param_value']
            meta = {
                'version': row['version'],
                'win_rate': row['win_rate'],
                'sample_size': row['sample_size']
            }

        return {
            'params': params,
            'meta': meta
        }

    def get_battle_count(self) -> int:
        """Get total number of recorded battles."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM battles")
        return cursor.fetchone()[0]

    def get_recent_battles(self, limit: int = 10) -> List[Dict]:
        """Get recent battles."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM battles
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]

    def save_agent_learning_state(
        self,
        agent_name: str,
        agent_type: str,
        total_battles: int,
        total_wins: int,
        performance_history: List[Dict],
        current_params: Dict,
        epsilon: float = 0.3
    ):
        """Save agent learning state for persistence across sessions."""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()

        cursor.execute("""
            INSERT OR REPLACE INTO agent_learning_state
            (agent_name, agent_type, total_battles, total_wins, performance_history,
             current_params, epsilon, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_name, agent_type, total_battles, total_wins,
            json.dumps(performance_history[-100:]),  # Keep last 100
            json.dumps(current_params),
            epsilon, timestamp
        ))
        self.conn.commit()

    def load_agent_learning_state(self, agent_name: str) -> Optional[Dict]:
        """Load agent learning state from database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_learning_state WHERE agent_name = ?
        """, (agent_name,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            'agent_name': row['agent_name'],
            'agent_type': row['agent_type'],
            'total_battles': row['total_battles'],
            'total_wins': row['total_wins'],
            'performance_history': json.loads(row['performance_history'] or '[]'),
            'current_params': json.loads(row['current_params'] or '{}'),
            'epsilon': row['epsilon'],
            'updated_at': row['updated_at']
        }

    def save_q_table(
        self,
        agent_type: str,
        q_table: Dict,
        episodes: int,
        total_rewards: float,
        wins: int,
        epsilon: float
    ):
        """Save Q-table for persistence across sessions."""
        cursor = self.conn.cursor()
        timestamp = datetime.now().isoformat()

        # Convert Q-table to serializable format
        serializable_q_table = {
            str(k): {a.value if hasattr(a, 'value') else str(a): v for a, v in actions.items()}
            for k, actions in q_table.items()
        }

        cursor.execute("""
            INSERT OR REPLACE INTO q_tables
            (agent_type, q_table, episodes, total_rewards, wins, epsilon, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_type, json.dumps(serializable_q_table),
            episodes, total_rewards, wins, epsilon, timestamp
        ))
        self.conn.commit()

    def load_q_table(self, agent_type: str) -> Optional[Dict]:
        """Load Q-table from database."""
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT * FROM q_tables WHERE agent_type = ?
        """, (agent_type,))

        row = cursor.fetchone()
        if not row:
            return None

        return {
            'agent_type': row['agent_type'],
            'q_table': json.loads(row['q_table'] or '{}'),
            'episodes': row['episodes'],
            'total_rewards': row['total_rewards'],
            'wins': row['wins'],
            'epsilon': row['epsilon'],
            'updated_at': row['updated_at']
        }

    def get_all_agent_stats(self) -> Dict[str, Dict]:
        """Get learning stats for all agents."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM agent_learning_state")

        stats = {}
        for row in cursor.fetchall():
            stats[row['agent_name']] = {
                'agent_type': row['agent_type'],
                'total_battles': row['total_battles'],
                'total_wins': row['total_wins'],
                'win_rate': row['total_wins'] / max(row['total_battles'], 1),
                'epsilon': row['epsilon'],
                'updated_at': row['updated_at']
            }
        return stats

    def close(self):
        """Close database connection."""
        self.conn.close()


def generate_battle_id() -> str:
    """Generate unique battle ID."""
    import uuid
    return f"battle_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"


if __name__ == '__main__':
    # Demo
    print("Battle History Database Demo")
    print("="*60)

    db = BattleHistoryDB("data/test_history.db")

    # Create sample battle
    battle_id = generate_battle_id()

    battle = BattleRecord(
        battle_id=battle_id,
        timestamp=datetime.now().isoformat(),
        duration=180,
        winner="creator",
        creator_score=262240,
        opponent_score=8756,
        margin=253484,
        boost2_triggered=True,
        gloves_activated=2,
        power_ups_used=1,
        total_gifts_sent=11
    )

    db.record_battle(battle)
    print(f"✅ Recorded battle: {battle_id}")

    # Record agent performance
    agent_record = AgentBattleRecord(
        battle_id=battle_id,
        agent_name="Kinetik",
        agent_type="sniper",
        points_donated=259990,
        gifts_sent=1,
        avg_gift_value=259990,
        best_gift_value=259990,
        early_phase_gifts=0,
        mid_phase_gifts=0,
        late_phase_gifts=0,
        final_phase_gifts=1,
        gloves_sent=0,
        gloves_activated=0,
        power_ups_used=0,
        won=True
    )

    db.record_agent_performance(agent_record)
    print(f"✅ Recorded agent performance: Kinetik")

    # Record gift timing
    gift_record = GiftTimingRecord(
        battle_id=battle_id,
        agent_name="Kinetik",
        gift_type="PHOENIX",
        gift_value=259990,
        timestamp=175,
        phase="FINAL",
        multiplier=1.0,
        effective_value=259990,
        score_diff_before=-6000,
        activated_x5=False
    )

    db.record_gift_timing(gift_record)
    print(f"✅ Recorded gift timing: PHOENIX at t=175s")

    # Get stats
    stats = db.get_agent_stats("Kinetik")
    print(f"\n📊 Agent Stats (Kinetik):")
    print(f"   Total battles: {stats['total_battles']}")
    print(f"   Win rate: {stats['win_rate']*100:.1f}%")
    print(f"   Avg points: {stats['avg_points']:,.0f}")

    # Save strategy params
    version = db.save_strategy_params(
        agent_type="sniper",
        params={
            'snipe_window': 5.0,
            'min_deficit_for_universe': 300000,
            'min_deficit_for_lion': 150000
        },
        win_rate=0.85,
        sample_size=10
    )
    print(f"\n✅ Saved strategy params v{version}")

    # Get latest params
    latest = db.get_latest_strategy_params("sniper")
    print(f"\n📋 Latest Strategy Params (sniper):")
    print(f"   Version: {latest['meta']['version']}")
    print(f"   Win rate: {latest['meta']['win_rate']*100:.1f}%")
    print(f"   Params: {latest['params']}")

    print(f"\n📊 Total battles in DB: {db.get_battle_count()}")

    db.close()
    print("\n✅ Database demo complete!")


# =============================================================================
# REPLAY SYSTEM
# =============================================================================

@dataclass
class ReplayTick:
    """Single tick of replay data."""
    time: int
    creator_score: int
    opponent_score: int
    phase: str
    multiplier: float
    events: List[Dict]  # List of events at this tick


@dataclass
class ReplayData:
    """Complete replay data for a battle."""
    replay_id: str
    battle_id: str
    recorded_at: str
    duration: int
    winner: str
    final_creator_score: int
    final_opponent_score: int
    ticks: List[ReplayTick]
    agent_config: Dict  # Agent configuration used


class BattleRecorder:
    """
    Records battle tick-by-tick for later replay.

    Usage:
        recorder = BattleRecorder(battle_id)
        recorder.start_recording()

        # During battle:
        recorder.record_tick(time, creator_score, opponent_score, phase, multiplier)
        recorder.record_event(time, event_type, event_data)

        # At end:
        recorder.finish_recording(winner)
        replay_id = recorder.save_to_db(db)
    """

    REPLAY_RECORDING_BANNER = """
┌──────────────────────────────────────────────────────────────────────────────┐
│   🎬 RECORDING: Battle {battle_id}                                           │
│   Duration: {duration}s                                                       │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    def __init__(self, battle_id: str, duration: int = 180):
        """Initialize recorder for a battle."""
        self.battle_id = battle_id
        self.duration = duration
        self.recording = False
        self.ticks: Dict[int, ReplayTick] = {}
        self.agent_config: Dict = {}
        self.winner: str = ""
        self.recorded_at: str = ""
        self.replay_id: str = ""

    def start_recording(self, agent_config: Dict = None):
        """Start recording the battle."""
        import uuid
        self.recording = True
        self.recorded_at = datetime.now().isoformat()
        self.replay_id = f"replay_{self.battle_id}_{uuid.uuid4().hex[:6]}"
        self.agent_config = agent_config or {}
        self.ticks = {}

    def record_tick(self, time: int, creator_score: int, opponent_score: int,
                    phase: str, multiplier: float):
        """Record a single tick of the battle."""
        if not self.recording:
            return

        if time not in self.ticks:
            self.ticks[time] = ReplayTick(
                time=time,
                creator_score=creator_score,
                opponent_score=opponent_score,
                phase=phase,
                multiplier=multiplier,
                events=[]
            )
        else:
            # Update scores (events may have been recorded first)
            self.ticks[time].creator_score = creator_score
            self.ticks[time].opponent_score = opponent_score
            self.ticks[time].phase = phase
            self.ticks[time].multiplier = multiplier

    def record_event(self, time: int, event_type: str, event_data: Dict):
        """Record an event at a specific time."""
        if not self.recording:
            return

        if time not in self.ticks:
            self.ticks[time] = ReplayTick(
                time=time,
                creator_score=0,
                opponent_score=0,
                phase="UNKNOWN",
                multiplier=1.0,
                events=[]
            )

        self.ticks[time].events.append({
            'type': event_type,
            **event_data
        })

    def finish_recording(self, winner: str, final_creator: int, final_opponent: int):
        """Finish recording and set final state."""
        self.recording = False
        self.winner = winner
        self.final_creator_score = final_creator
        self.final_opponent_score = final_opponent

    def get_replay_data(self) -> ReplayData:
        """Get the complete replay data."""
        sorted_ticks = sorted(self.ticks.values(), key=lambda t: t.time)

        return ReplayData(
            replay_id=self.replay_id,
            battle_id=self.battle_id,
            recorded_at=self.recorded_at,
            duration=self.duration,
            winner=self.winner,
            final_creator_score=getattr(self, 'final_creator_score', 0),
            final_opponent_score=getattr(self, 'final_opponent_score', 0),
            ticks=sorted_ticks,
            agent_config=self.agent_config
        )

    def save_to_db(self, db: BattleHistoryDB) -> str:
        """Save replay to database and return replay_id."""
        replay = self.get_replay_data()

        # Serialize ticks
        ticks_data = [
            {
                'time': t.time,
                'creator_score': t.creator_score,
                'opponent_score': t.opponent_score,
                'phase': t.phase,
                'multiplier': t.multiplier,
                'events': t.events
            }
            for t in replay.ticks
        ]

        cursor = db.conn.cursor()

        # Create replays table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS battle_replays (
                replay_id TEXT PRIMARY KEY,
                battle_id TEXT,
                recorded_at TEXT,
                duration INTEGER,
                winner TEXT,
                final_creator_score INTEGER,
                final_opponent_score INTEGER,
                tick_data TEXT,
                agent_config TEXT
            )
        """)

        # Insert replay
        cursor.execute("""
            INSERT OR REPLACE INTO battle_replays
            (replay_id, battle_id, recorded_at, duration, winner,
             final_creator_score, final_opponent_score, tick_data, agent_config)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            replay.replay_id,
            replay.battle_id,
            replay.recorded_at,
            replay.duration,
            replay.winner,
            replay.final_creator_score,
            replay.final_opponent_score,
            json.dumps(ticks_data),
            json.dumps(replay.agent_config)
        ))

        db.conn.commit()
        return replay.replay_id

    def save_to_file(self, filepath: str):
        """Save replay to JSON file."""
        replay = self.get_replay_data()

        data = {
            'replay_id': replay.replay_id,
            'battle_id': replay.battle_id,
            'recorded_at': replay.recorded_at,
            'duration': replay.duration,
            'winner': replay.winner,
            'final_creator_score': replay.final_creator_score,
            'final_opponent_score': replay.final_opponent_score,
            'ticks': [
                {
                    'time': t.time,
                    'creator_score': t.creator_score,
                    'opponent_score': t.opponent_score,
                    'phase': t.phase,
                    'multiplier': t.multiplier,
                    'events': t.events
                }
                for t in replay.ticks
            ],
            'agent_config': replay.agent_config
        }

        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"💾 Replay saved to: {filepath}")


class ReplayPlayer:
    """
    Plays back recorded battles with dramatic commentary.

    Features:
    - Variable playback speed (0.25x - 4x)
    - Pause/resume
    - Skip to timestamp
    - Event highlighting
    - Dramatic commentary
    """

    PLAYBACK_START_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🎬🎬🎬  R E P L A Y   P L A Y B A C K  🎬🎬🎬                              ║
║                                                                              ║
║   Battle: {battle_id}                                                        ║
║   Duration: {duration}s | Speed: {speed}x                                    ║
║   Final: Creator {creator:,} vs Opponent {opponent:,}                        ║
║   Winner: {winner}                                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    PHASE_CHANGE_BANNER = """
┌──────────────────────────────────────────────────────────────────────────────┐
│   ⚡ PHASE CHANGE: {phase} (x{multiplier:.1f})                               │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    GIFT_EVENT_FORMAT = "   🎁 [{time:>3}s] {agent}: {gift} (+{points:,})"

    WHALE_EVENT_FORMAT = """
┌──────────────────────────────────────────────────────────────────────────────┐
│   🐋 WHALE ALERT! {agent} sends {gift} (+{points:,})                         │
└──────────────────────────────────────────────────────────────────────────────┘
"""

    CLUTCH_MOMENT_FORMAT = """
╔══════════════════════════════════════════════════════════════════════════════╗
║   🔥 CLUTCH MOMENT at {time}s! Score diff: {diff:,}                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, speed: float = 1.0):
        """Initialize replay player."""
        self.speed = speed
        self.paused = False
        self.current_time = 0
        self.replay_data: Optional[ReplayData] = None

    def load_from_db(self, db: BattleHistoryDB, replay_id: str) -> bool:
        """Load replay from database."""
        cursor = db.conn.cursor()

        cursor.execute("""
            SELECT * FROM battle_replays WHERE replay_id = ?
        """, (replay_id,))

        row = cursor.fetchone()
        if not row:
            print(f"❌ Replay not found: {replay_id}")
            return False

        # Parse tick data
        tick_data = json.loads(row['tick_data'])
        ticks = [
            ReplayTick(
                time=t['time'],
                creator_score=t['creator_score'],
                opponent_score=t['opponent_score'],
                phase=t['phase'],
                multiplier=t['multiplier'],
                events=t.get('events', [])
            )
            for t in tick_data
        ]

        self.replay_data = ReplayData(
            replay_id=row['replay_id'],
            battle_id=row['battle_id'],
            recorded_at=row['recorded_at'],
            duration=row['duration'],
            winner=row['winner'],
            final_creator_score=row['final_creator_score'],
            final_opponent_score=row['final_opponent_score'],
            ticks=ticks,
            agent_config=json.loads(row['agent_config'] or '{}')
        )

        return True

    def load_from_file(self, filepath: str) -> bool:
        """Load replay from JSON file."""
        if not os.path.exists(filepath):
            print(f"❌ File not found: {filepath}")
            return False

        with open(filepath, 'r') as f:
            data = json.load(f)

        ticks = [
            ReplayTick(
                time=t['time'],
                creator_score=t['creator_score'],
                opponent_score=t['opponent_score'],
                phase=t['phase'],
                multiplier=t['multiplier'],
                events=t.get('events', [])
            )
            for t in data['ticks']
        ]

        self.replay_data = ReplayData(
            replay_id=data['replay_id'],
            battle_id=data['battle_id'],
            recorded_at=data['recorded_at'],
            duration=data['duration'],
            winner=data['winner'],
            final_creator_score=data['final_creator_score'],
            final_opponent_score=data['final_opponent_score'],
            ticks=ticks,
            agent_config=data.get('agent_config', {})
        )

        return True

    def play(self, verbose: bool = True, step_callback: callable = None):
        """
        Play the loaded replay.

        Args:
            verbose: Print events during playback
            step_callback: Optional callback(time, creator_score, opponent_score)
        """
        import time as time_module

        if not self.replay_data:
            print("❌ No replay loaded!")
            return

        replay = self.replay_data

        if verbose:
            print(self.PLAYBACK_START_BANNER.format(
                battle_id=replay.battle_id,
                duration=replay.duration,
                speed=self.speed,
                creator=replay.final_creator_score,
                opponent=replay.final_opponent_score,
                winner=replay.winner.upper()
            ))

        last_phase = None
        tick_delay = 1.0 / self.speed

        for tick in replay.ticks:
            if self.paused:
                while self.paused:
                    time_module.sleep(0.1)

            self.current_time = tick.time

            # Phase change
            if tick.phase != last_phase and verbose:
                print(self.PHASE_CHANGE_BANNER.format(
                    phase=tick.phase,
                    multiplier=tick.multiplier
                ))
                last_phase = tick.phase

            # Process events
            for event in tick.events:
                if verbose:
                    self._display_event(tick.time, event)

            # Callback
            if step_callback:
                step_callback(tick.time, tick.creator_score, tick.opponent_score)

            # Progress bar every 30s
            if verbose and tick.time % 30 == 0:
                bar = self._progress_bar(tick.time, replay.duration)
                diff = tick.creator_score - tick.opponent_score
                diff_str = f"+{diff:,}" if diff >= 0 else f"{diff:,}"
                print(f"   [{bar}] {tick.time}s | Creator: {tick.creator_score:,} ({diff_str})")

            # Delay based on speed
            time_module.sleep(tick_delay * 0.1)  # Scaled for quick replay

        if verbose:
            self._display_end(replay)

    def _display_event(self, time: int, event: Dict):
        """Display an event during playback."""
        event_type = event.get('type', 'unknown')

        if event_type == 'gift':
            points = event.get('points', 0)
            if points >= 10000:
                print(self.WHALE_EVENT_FORMAT.format(
                    agent=event.get('agent', 'Unknown'),
                    gift=event.get('gift', 'GIFT'),
                    points=points
                ))
            else:
                print(self.GIFT_EVENT_FORMAT.format(
                    time=time,
                    agent=event.get('agent', 'Unknown'),
                    gift=event.get('gift', 'GIFT'),
                    points=points
                ))

        elif event_type == 'glove':
            activated = "ACTIVATED!" if event.get('activated') else "sent"
            print(f"   🥊 [{time:>3}s] Glove {activated}")

        elif event_type == 'phase_change':
            pass  # Handled separately

        elif event_type == 'clutch':
            print(self.CLUTCH_MOMENT_FORMAT.format(
                time=time,
                diff=event.get('score_diff', 0)
            ))

    def _display_end(self, replay: ReplayData):
        """Display end of replay."""
        print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏁 REPLAY COMPLETE                                                         ║
║                                                                              ║
║   Final Score: Creator {replay.final_creator_score:,} vs Opponent {replay.final_opponent_score:,}                ║
║   Winner: {replay.winner.upper():<66} ║
║   Margin: {abs(replay.final_creator_score - replay.final_opponent_score):,}                                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    def _progress_bar(self, current: int, total: int, width: int = 20) -> str:
        """Create ASCII progress bar."""
        filled = int(width * current / total)
        empty = width - filled
        return f"{'█' * filled}{'░' * empty}"

    def skip_to(self, target_time: int):
        """Skip to a specific time in the replay."""
        self.current_time = target_time

    def pause(self):
        """Pause playback."""
        self.paused = True

    def resume(self):
        """Resume playback."""
        self.paused = False

    def set_speed(self, speed: float):
        """Set playback speed (0.25 - 4.0)."""
        self.speed = max(0.25, min(4.0, speed))

    @staticmethod
    def list_replays(db: BattleHistoryDB) -> List[Dict]:
        """List available replays in database."""
        cursor = db.conn.cursor()

        # Check if table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='battle_replays'
        """)
        if not cursor.fetchone():
            return []

        cursor.execute("""
            SELECT replay_id, battle_id, recorded_at, duration, winner,
                   final_creator_score, final_opponent_score
            FROM battle_replays
            ORDER BY recorded_at DESC
        """)

        replays = []
        for row in cursor.fetchall():
            replays.append({
                'replay_id': row['replay_id'],
                'battle_id': row['battle_id'],
                'recorded_at': row['recorded_at'],
                'duration': row['duration'],
                'winner': row['winner'],
                'creator_score': row['final_creator_score'],
                'opponent_score': row['final_opponent_score']
            })

        return replays

    @staticmethod
    def print_replays(db: BattleHistoryDB):
        """Print formatted list of available replays."""
        replays = ReplayPlayer.list_replays(db)

        print("\n" + "=" * 80)
        print("   🎬 AVAILABLE REPLAYS")
        print("=" * 80)

        if not replays:
            print("   No replays found.")
        else:
            print(f"\n   {'#':<4}{'Replay ID':<30}{'Winner':<12}{'Score':<20}{'Date':<20}")
            print("   " + "-" * 75)

            for i, r in enumerate(replays, 1):
                score = f"{r['creator_score']:,} - {r['opponent_score']:,}"
                date = r['recorded_at'][:19] if len(r['recorded_at']) > 19 else r['recorded_at']
                print(f"   {i:<4}{r['replay_id'][:28]:<30}{r['winner']:<12}{score:<20}{date:<20}")

        print("=" * 80 + "\n")
