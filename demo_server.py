#!/usr/bin/env python3
"""Lightweight demo battle server for video recording."""

from flask import Flask, send_from_directory
from flask_socketio import SocketIO, emit
import random
import time
import threading

app = Flask(__name__, static_folder='web/frontend/public')
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def index():
    return send_from_directory('web/frontend/public', 'demo-battle.html')

@app.route('/api/health')
def health():
    return {'status': 'ok'}

demo_active = False

@socketio.on('connect')
def on_connect():
    print('Client connecté')

@socketio.on('start_demo_battle')
def start_demo(data):
    global demo_active
    if demo_active:
        return
    demo_active = True
    threading.Thread(target=run_battle, args=(data,), daemon=True).start()
    emit('demo_battle_started', data)

def run_battle(data):
    global demo_active
    gifts = [
        {'name': 'Rose', 'coins': 1, 'emoji': '🌹'},
        {'name': 'Ice Cream', 'coins': 10, 'emoji': '🍦'},
        {'name': 'Cap', 'coins': 99, 'emoji': '🧢'},
        {'name': 'Fest Pop', 'coins': 100, 'emoji': '🎉'},
        {'name': 'TikTok Universe', 'coins': 500, 'emoji': '🌌'},
        {'name': 'Dragon', 'coins': 10000, 'emoji': '🐉'},
        {'name': 'Lion', 'coins': 29999, 'emoji': '🦁'},
    ]
    agents = ['PixelPixie', 'GlitchMancer', 'BoostResponder', 'StrikeMaster', 'PhaseTracker']

    creator_score = 0
    opponent_score = 0
    duration = data.get('duration', 90)
    multiplier = 1.0

    start = time.time()
    last_phase = 0

    print(f"🎮 Battle démarré: {data.get('creator')} vs {data.get('opponent')}")

    while demo_active and (time.time() - start) < duration:
        elapsed = int(time.time() - start)
        remaining = duration - elapsed

        # Phase changes every 20 seconds
        if elapsed > 0 and elapsed % 20 == 0 and elapsed != last_phase:
            last_phase = elapsed
            multiplier = random.choice([1.0, 2.0, 3.0, 5.0])
            phase = {1.0:'Normal', 2.0:'Boost x2', 3.0:'Boost x3', 5.0:'MEGA x5'}[multiplier]
            socketio.emit('demo_battle_update', {'type':'phase', 'phase':phase, 'multiplier':multiplier})
            print(f"⚡ Phase: {phase}")

        # Generate gifts
        for _ in range(random.randint(2, 5)):
            team = random.choice(['creator', 'opponent'])
            gift = random.choice(gifts)
            agent = random.choice(agents) if team == 'creator' else 'Opponent_AI'
            points = int(gift['coins'] * multiplier)

            if team == 'creator':
                creator_score += points
            else:
                opponent_score += points

            socketio.emit('demo_battle_update', {
                'type': 'gift',
                'team': team,
                'agent': agent,
                'gift_name': gift['name'],
                'gift_emoji': gift['emoji'],
                'coins': gift['coins'],
                'points': points,
                'multiplier': multiplier,
                'creator_score': creator_score,
                'opponent_score': opponent_score,
                'time_remaining': remaining
            })

        time.sleep(0.35)

    winner = 'creator' if creator_score > opponent_score else 'opponent'
    socketio.emit('demo_battle_update', {
        'type': 'end',
        'winner': winner,
        'creator': data.get('creator', 'AI'),
        'opponent': data.get('opponent', 'Bot'),
        'creator_score': creator_score,
        'opponent_score': opponent_score
    })
    demo_active = False
    print(f'🏆 Battle terminé! Score: {creator_score:,} vs {opponent_score:,}')

if __name__ == '__main__':
    print('=' * 50)
    print('🎮 Demo Battle Server')
    print('=' * 50)
    print('Open: http://localhost:5000')
    print('Click "Start Demo Battle" to begin!')
    print('=' * 50)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
