# Video Generator - Demo Video pour TikTok Developer Portal

## Structure

```
video_generator/
├── config.py         # Configuration globale
├── core/
│   ├── renderer.py   # Moteur de rendu des scènes
│   ├── compositor.py # Assemblage final
│   └── animations.py # Animations réutilisables
├── scenes/
│   ├── scene_01_intro.py
│   ├── scene_02_dashboard.py
│   ├── scene_03_oauth.py
│   ├── scene_04_battle.py
│   ├── scene_05_gifts.py
│   ├── scene_06_analytics.py
│   ├── scene_07_winner.py
│   └── scene_08_closing.py
└── assets/
    ├── backgrounds/
    ├── fonts/
    └── images/
```

## Scènes

| # | Scène | Durée | Scope TikTok |
|---|-------|-------|--------------|
| 1 | Intro | 15s | - |
| 2 | Dashboard | 15s | - |
| 3 | OAuth Login | 30s | `user.info.basic` |
| 4 | Start Battle | 30s | `live.room.info` |
| 5 | Gift Tracking | 60s | `live.gift.info` |
| 6 | Analytics | 30s | - |
| 7 | Winner | 20s | - |
| 8 | Closing | 25s | - |

**Total: ~3:45**

## Usage

```bash
# Générer la vidéo complète
python -m video_generator.generate

# Générer une scène spécifique
python -m video_generator.generate --scene intro

# Prévisualiser
python -m video_generator.preview --scene gifts
```
