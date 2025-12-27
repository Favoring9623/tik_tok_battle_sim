# Audit Complet des Scripts - TikTok Battle Simulator

**Date:** 2025-12-24
**Status:** Tous les scripts sont syntaxiquement valides

---

## PHASE 1: DEMO (Entraînement AI)

Scripts de simulation pour entraîner les agents IA sans connexion TikTok réelle.

### Scripts Principaux (Recommandés)

| Script | Description | Status |
|--------|-------------|--------|
| `demo_web_strategic_battle.py` | **PRINCIPAL** - Battle stratégique avec dashboard web, GPT commentary, phases | ✅ Fonctionnel |
| `demo_evolving_agents.py` | Entraînement multi-battles avec agents évolutifs | ✅ Fonctionnel |
| `demo_strategic_battle.py` | Battle stratégique en CLI avec tous les power-ups | ✅ Fonctionnel |
| `demo_tournament_bo5.py` | Tournoi Best-of-5 complet | ✅ Fonctionnel |

### Scripts Secondaires

| Script | Description | Usage |
|--------|-------------|-------|
| `demo_battle.py` | Battle simple basique | Tests rapides |
| `demo_coordination.py` | Test coordination entre agents | Debug |
| `demo_fog_hammer_visual.py` | Visualisation power-ups | Demo visuelle |
| `demo_gpt_battle.py` | Battle avec GPT commentary | Avec OpenAI API |
| `demo_gpt_personas.py` | Personas GPT avancées | Avec OpenAI API |
| `demo_gpt_strategic_battle.py` | Battle stratégique + GPT | Avec OpenAI API |
| `demo_gpt_tournament.py` | Tournoi avec GPT | Avec OpenAI API |
| `demo_new_agents.py` | Test nouveaux agents | Développement |
| `demo_realistic_mode.py` | Simulation réaliste | Entraînement avancé |
| `demo_specialists.py` | Agents spécialistes | Tests spécifiques |
| `demo_time_extension.py` | Système d'extension de temps | Feature test |
| `demo_tournament.py` | Tournoi complet | Tests longs |
| `demo_tournament_bo3.py` | Tournoi Best-of-3 | Tests moyens |
| `demo_tournament_enhanced*.py` | Tournois améliorés | Variantes |
| `demo_web_battle.py` | Battle basique + web | Dashboard simple |
| `demo_web_tournament.py` | Tournoi web | Dashboard tournoi |

### Agents Évolutifs (core/agents/)

| Module | Description |
|--------|-------------|
| `evolving_agents.py` | Système d'apprentissage Q-learning |
| `learning_system.py` | Optimisation de stratégie |
| `base_agent.py` | Classe de base agent |
| `personas/boost_responder.py` | Spécialiste des boosts |
| `personas/pixel_pixie.py` | Agent roses tactiques |
| `personas/evolving_glitch_mancer.py` | Burst master évolutif |

---

## PHASE 2: LIVE (Tests Réels TikTok)

Scripts connectés à l'API TikTok Live pour tester en conditions réelles.

### Scripts Principaux (Recommandés)

| Script | Description | Prérequis |
|--------|-------------|-----------|
| `train_live_tiktok.py` | **PRINCIPAL** - Entraînement sur streams réels | TikTokLive + EulerStream |
| `run_ai_vs_live.py` | AI vs Streamer réel | TikTokLive |
| `run_live_tournament.py` | Tournoi sur streams réels | TikTokLive |

### Scripts Gift Sender (Envoi réel)

| Script | Description | Status |
|--------|-------------|--------|
| `send_fest_pop_v2.py` | Envoi Fest Pop optimisé | ✅ Testé |
| `send_fest_pop_fixed.py` | Version corrigée | ✅ Stable |
| `send_gifts_now.py` | Envoi immédiat | ✅ Fonctionnel |
| `parallel_gift_sender.py` | Envoi parallèle | ⚠️ Expérimental |

### Scripts Utilitaires Live

| Script | Description |
|--------|-------------|
| `run_ai_battle.py` | Battle AI autonome |
| `run_auto_clicker_live.py` | Auto-clicker pour tests |
| `train_live_agents.py` | Entraînement continu |
| `demo_live_battle.py` | Demo battle live |

### Modules Core Live

| Module | Description |
|--------|-------------|
| `core/tiktok_live_connector.py` | Connexion TikTok WebSocket |
| `core/live_battle_engine.py` | Moteur battle temps réel |
| `core/live_learning_engine.py` | Apprentissage en live |
| `core/gift_sender.py` | Envoi de gifts |
| `core/battle_platform.py` | Plateforme intégrée |

---

## STRATÉGIE DE FUSION DEMO/LIVE

### Architecture Proposée

```
┌─────────────────────────────────────────────────────────┐
│                    PHASE 1: DEMO                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Simulation  │  │  Evolving    │  │   Q-Table     │  │
│  │   Engine    │→ │   Agents     │→ │   Training    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         ↓                                    ↓          │
│  ┌─────────────────────────────────────────────────┐   │
│  │         MODÈLES ENTRAÎNÉS (data/*.json)         │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    PHASE 2: LIVE                        │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  TikTok     │  │   Trained    │  │  Real-time    │  │
│  │ Connector   │→ │   Agents     │→ │  Decisions    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         ↑                                    ↓          │
│  ┌─────────────────────────────────────────────────┐   │
│  │        FEEDBACK LOOP (Continuous Learning)       │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Workflow Recommandé

1. **Entraînement Initial (Demo)**
   ```bash
   python demo_evolving_agents.py --battles 50
   ```

2. **Validation Stratégique (Demo + Web)**
   ```bash
   python demo_web_strategic_battle.py
   ```

3. **Test Live Passif (Observation)**
   ```bash
   python train_live_tiktok.py --mode single --username @streamer
   ```

4. **Test Live Actif (AI vs Streamer)**
   ```bash
   python run_ai_vs_live.py --target @streamer --format bo3
   ```

5. **Déploiement Production**
   ```bash
   python run_live_tournament.py --creators @user1,@user2
   ```

---

## FICHIERS DE DONNÉES

| Fichier | Description |
|---------|-------------|
| `data/q_tables/*.json` | Tables Q-learning par agent |
| `data/agent_states/*.json` | États sauvegardés agents |
| `data/training_history.db` | Historique SQLite |
| `data/web_battle_history.db` | Historique web |

---

## SCRIPTS À ÉVITER

| Script | Raison |
|--------|--------|
| `debug_*.py` | Debug uniquement |
| `investigate_*.py` | Investigation ponctuelle |
| `test_*.py` | Tests unitaires |
| `check_*.py` | Vérifications ponctuelles |

---

## PROCHAINES ÉTAPES

1. [ ] Consolider les Q-tables entre Demo et Live
2. [ ] Ajouter métriques de transfert learning
3. [ ] Créer pipeline CI/CD pour validation agents
4. [ ] Implémenter A/B testing en production
