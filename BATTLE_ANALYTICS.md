# Système d'Analytics de Bataille 📊

## Vue d'ensemble

Le système d'analytics complet pour TikTok Battle Simulator collecte et visualise toutes les données de bataille en temps réel.

---

## Fonctionnalités

### 📈 Collecte de Données

**Score Timeline**
- Snapshots à chaque seconde
- Progression Creator vs Opponent
- Détection des momentum shifts
- Identification du leader à tout moment

**Action Tracking**
- Tous les cadeaux envoyés par les agents
- Timing précis (seconde exacte)
- Multiplicateurs appliqués
- Métadonnées de coordination

**Agent Performance**
- Total des donations par agent
- Nombre de cadeaux envoyés
- Valeur moyenne des cadeaux
- Meilleur cadeau (gift signature)
- Distribution temporelle (early/mid/late/final)

**Multiplier Sessions**
- Type de session (x2, x3, x5)
- Heures de début/fin
- Durée totale
- Source (auto, threshold, manual)
- Couverture de bataille (%)

**Gift Analytics**
- Distribution par type de cadeau
- Patterns temporels
- Premier/dernier usage
- Cadeau le plus utilisé

---

## Architecture

### Composants Principaux

**1. `BattleAnalytics` (core/battle_analytics.py)**
```python
class BattleAnalytics:
    def record_battle_start()      # Initialisation
    def record_score_snapshot()    # Score chaque seconde
    def record_action()             # Action d'agent
    def record_multiplier_session() # Session multiplicateur
    def record_coordination_event() # Événement de coordination
    def record_battle_end()         # Conclusion

    def get_complete_summary()      # Résumé JSON
    def export_to_json()            # Export fichier
    def print_summary()             # Console output
```

**2. `BattleVisualizer` (core/battle_visualizer.py)**
```python
class BattleVisualizer:
    @staticmethod
    def create_score_chart()          # Graphique ASCII score
    def create_action_timeline()      # Timeline d'actions
    def create_agent_comparison()     # Barres de performance
    def create_multiplier_timeline()  # Timeline multiplicateurs
    def create_complete_report()      # Rapport complet
```

**3. Intégration `BattleEngine`**
- Analytics activé par défaut (`enable_analytics=True`)
- Collecte automatique pendant la bataille
- Rapport visuel à la fin
- Export JSON disponible

---

## Utilisation

### Démo Rapide

```bash
python3 demo_analytics.py
```

### Dans Votre Code

```python
from core.battle_engine import BattleEngine
from core.battle_visualizer import BattleVisualizer

# Créer bataille avec analytics
engine = BattleEngine(
    battle_duration=180,
    enable_analytics=True  # ← Activé par défaut
)

# Ajouter agents...
engine.add_agent(kinetik)
engine.add_agent(strike_master)

# Lancer bataille
engine.run(silent=True)

# Générer rapport visuel
visualizer = BattleVisualizer()
report = visualizer.create_complete_report(engine.analytics)
print(report)

# Exporter JSON
engine.analytics.export_to_json("data/battle_results.json")
```

---

## Visualisations

### 📈 Score Progression Chart

```
91,002 |                     ███████████████████████████████████████
84,935 |                     ███████████████████████████████████████
78,868 |
72,801 |
66,734 |
60,668 |
54,601 |
48,534 |
42,467 |
36,400 |
30,334 |
24,267 |
18,200 |
12,133 |                                                       ░░░░░
 6,066 |XXXXXXXXXXXXXXXXXXXXX░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
       +------------------------------------------------------------
       0s                                        180s

  Legend: █ Creator  ░ Opponent  X Both
```

**Légende:**
- `█` : Score Creator
- `░` : Score Opponent
- `X` : Les deux scores au même niveau

---

### 👥 Agent Performance Bars

```
StrikeMaster      89,997 pts
                ████████████████████████████████████████
                Gifts: 1 | Avg: 89,997 | Best: Lion

Kinetik            1,000 pts

                Gifts: 1 | Avg: 1,000 | Best: Galaxy

Activator              5 pts

                Gifts: 5 | Avg: 1 | Best: Rose
```

**Informations:**
- Total points contributés
- Nombre de cadeaux
- Valeur moyenne
- Meilleur cadeau envoyé

---

### ⏱️ Action Timeline

```
0s |                       ⚡           📊📊📊📊                              🎯| 180s

KEY ACTIONS:
  [ 61s] 🎁 StrikeMaster: Lion (89,997 pts)
  [ 90s] 🎁 Activator: Rose (1 pts)
  [ 92s] 🎁 Activator: Rose (1 pts)
  [178s] 🎁 Kinetik: Galaxy (1,000 pts)
```

**Symboles:**
- `🎯` : Kinetik (Sniper)
- `⚡` : StrikeMaster (x5 strikes)
- `📊` : Activator (Bonus sessions)
- `🛡️` : Sentinel (Defensive)

---

### ⚡ Multiplier Session Timeline

```
0s |                       ▓▓▓▓▓▓▓▓▓      ▓▓▓▓▓▓▓▓▓▓                      | 180s

  ▓ = x3 session   ▒ = x2 session

SESSION DETAILS:
  1. x3 @ 61s-82s (21s, auto)
  2. x3 @ 98s-121s (23s, threshold)

Total coverage: 24.4% of battle
```

**Informations:**
- Type de session (x2, x3, x5)
- Temps de début/fin
- Durée
- Source (auto/threshold/manual)
- Couverture totale (%)

---

## Export JSON

### Structure Complète

```json
{
  "battle": {
    "duration": 180,
    "winner": "creator",
    "final_scores": {
      "creator": 91002,
      "opponent": 7522
    },
    "score_diff": -83480
  },
  "agents": {
    "StrikeMaster": {
      "total_donated": 89997,
      "gifts_sent": 1,
      "avg_gift_value": 89997.0,
      "best_gift": {
        "name": "Lion",
        "value": 89997
      },
      "timing": {
        "early": 0,
        "mid": 1,
        "late": 0,
        "final": 0
      }
    },
    "Kinetik": { ... },
    "Activator": { ... }
  },
  "multipliers": {
    "total_sessions": 2,
    "total_duration": 44,
    "sessions_by_type": {
      "x3": 2
    },
    "avg_duration": 22.0,
    "coverage": 24.4
  },
  "gifts": {
    "distribution": {
      "Lion": 1,
      "Rose": 5,
      "Galaxy": 1
    },
    "timing_patterns": {
      "Lion": {
        "count": 1,
        "first": 61,
        "last": 61,
        "avg_time": 61.0
      },
      ...
    },
    "most_used": "Rose"
  },
  "timeline": {
    "snapshots": 180,
    "actions": 7
  }
}
```

---

## Métriques Clés

### Performance des Agents

**Total Donated**
- Points totaux contribués au score Creator
- Inclut multiplicateurs appliqués

**Gifts Sent**
- Nombre de cadeaux envoyés
- Indicateur d'activité

**Average Gift Value**
- Valeur moyenne des cadeaux
- Efficacité de l'agent

**Best Gift**
- Cadeau le plus cher envoyé
- Gift signature de l'agent

**Timing Distribution**
- Early: 0-33% de la bataille
- Mid: 33-67%
- Late: 67-97%
- Final: 97-100%

### Sessions Multiplicateurs

**Total Sessions**
- Nombre de sessions activées

**Total Duration**
- Durée cumulée (secondes)

**Coverage**
- % de bataille sous multiplicateur
- Métrique d'efficacité

**Sessions by Type**
- Distribution x2 / x3 / x5

### Patterns de Cadeaux

**Distribution**
- Comptage par type de cadeau

**Timing Patterns**
- Premier usage
- Dernier usage
- Temps moyen
- Fréquence

---

## API Reference

### BattleAnalytics

#### Enregistrement de Données

```python
# Initialiser bataille
analytics.record_battle_start(duration=180, agent_count=4)

# Enregistrer snapshot de score
analytics.record_score_snapshot(
    time=current_time,
    creator_score=50000,
    opponent_score=45000,
    phase="mid"
)

# Enregistrer action d'agent
analytics.record_action(
    time=current_time,
    agent="StrikeMaster",
    action_type="gift",
    gift_name="Lion",
    points=89997,
    multiplier=3.0,
    coordinated=True
)

# Enregistrer session multiplicateur
analytics.record_multiplier_session(
    session_type="x3",
    start_time=60,
    end_time=85,
    source="auto"
)

# Terminer bataille
analytics.record_battle_end(
    winner="creator",
    creator_score=91002,
    opponent_score=7522
)
```

#### Récupération de Données

```python
# Score progression (liste de dicts)
progression = analytics.get_score_progression()
# [{"time": 0, "creator": 0, "opponent": 0, ...}, ...]

# Timeline d'actions
timeline = analytics.get_action_timeline()
# [{"time": 60, "agent": "StrikeMaster", "gift": "Lion", ...}, ...]

# Performance des agents
performance = analytics.get_agent_performance(include_actions=False)
# {"StrikeMaster": {"total_donated": 89997, ...}, ...}

# Résumé coordination
coordination = analytics.get_coordination_summary()
# {"total_events": 5, "conflicts_prevented": 2, ...}

# Analyse multiplicateurs
multipliers = analytics.get_multiplier_analysis()
# {"total_sessions": 2, "coverage": 24.4, ...}

# Analyse cadeaux
gifts = analytics.get_gift_analysis()
# {"distribution": {...}, "timing_patterns": {...}, ...}

# Résumé complet
summary = analytics.get_complete_summary()
# Dict complet avec toutes les données
```

#### Export et Affichage

```python
# Exporter JSON
analytics.export_to_json("data/battle_001.json")

# Afficher résumé console
analytics.print_summary()
```

### BattleVisualizer

```python
visualizer = BattleVisualizer()

# Graphique de score
chart = visualizer.create_score_chart(analytics, width=60, height=15)
print(chart)

# Timeline d'actions
timeline = visualizer.create_action_timeline(analytics, width=70)
print(timeline)

# Comparaison agents
comparison = visualizer.create_agent_comparison(analytics)
print(comparison)

# Timeline multiplicateurs
mult_timeline = visualizer.create_multiplier_timeline(analytics, width=70)
print(mult_timeline)

# Rapport complet
report = visualizer.create_complete_report(analytics)
print(report)
```

---

## Intégration avec Coordination

Le système d'analytics s'intègre avec le `TeamCoordinator` pour tracker:

- **Événements de coordination** (approvals, deferrals, dependencies)
- **Conflits prévenus** (count)
- **Dépendances satisfaites** (count)
- **Taux de coordination** (%)

```python
# Dans TeamCoordinator
if analytics:
    analytics.record_coordination_event(
        event_type="approved",
        agent=agent_name,
        action=action_type,
        time=current_time,
        priority=priority.name
    )
```

---

## Cas d'Usage

### 1. Post-Battle Analysis

Analyser pourquoi une bataille a été gagnée/perdue:

```python
summary = analytics.get_complete_summary()

# Vérifier contribution des agents
for agent, stats in summary['agents'].items():
    print(f"{agent}: {stats['total_donated']:,} points")

# Vérifier efficacité multiplicateurs
mult = summary['multipliers']
print(f"Multiplier coverage: {mult['coverage']:.1f}%")

# Identifier moments clés
timeline = analytics.get_action_timeline()
big_actions = [a for a in timeline if a['points'] > 10000]
```

### 2. Agent Optimization

Comparer performance de différentes configurations d'agents:

```python
# Battle 1: Team A
engine1.run()
perf1 = engine1.analytics.get_agent_performance()

# Battle 2: Team B
engine2.run()
perf2 = engine2.analytics.get_agent_performance()

# Comparer
for agent in perf1:
    diff = perf2[agent]['total_donated'] - perf1[agent]['total_donated']
    print(f"{agent} improvement: {diff:+,} points")
```

### 3. Strategy Testing

Tester différentes stratégies de timing:

```python
# Analyser timing optimal pour x5 strikes
timeline = analytics.get_action_timeline()
x5_strikes = [a for a in timeline if "Strike" in a['agent']]

for strike in x5_strikes:
    print(f"x5 at {strike['time']}s: {strike['points']:,} points")

# Analyser couverture multiplicateur
mult = analytics.get_multiplier_analysis()
print(f"Total coverage: {mult['coverage']:.1f}%")
```

### 4. Tournament Analysis

Comparer multiples batailles:

```python
battles = []
for i in range(10):
    engine = BattleEngine(battle_duration=180, enable_analytics=True)
    # ... setup agents ...
    engine.run(silent=True)

    battles.append({
        'winner': engine.analytics.winner,
        'score_diff': engine.analytics.final_scores['opponent'] -
                     engine.analytics.final_scores['creator'],
        'multiplier_coverage': engine.analytics.get_multiplier_analysis()['coverage']
    })

# Statistiques
wins = sum(1 for b in battles if b['winner'] == 'creator')
avg_coverage = sum(b['multiplier_coverage'] for b in battles) / len(battles)

print(f"Win rate: {wins}/{len(battles)} ({wins/len(battles)*100:.1f}%)")
print(f"Avg multiplier coverage: {avg_coverage:.1f}%")
```

---

## Performance

### Overhead

- **Collecte**: <1% de temps CPU
- **Mémoire**: ~10KB par bataille de 180s
- **Export JSON**: ~50KB pour bataille complète

### Scalabilité

- Testé avec batailles de 60s à 180s
- Supporte 1-10 agents
- 180+ snapshots de score
- 100+ actions trackées

---

## Prochaines Étapes

### Améliorations Futures

**Visualisations Avancées**
- Export vers HTML avec charts interactifs
- Graphs Matplotlib/Plotly
- Real-time dashboard

**Analytics Avancés**
- Machine learning pour pattern detection
- Win probability prediction
- Agent synergy analysis

**Comparaison**
- Multi-battle comparison views
- A/B testing framework
- Tournament leaderboards

---

## Résumé

✅ **Collecte complète de données** - Scores, actions, sessions, performance
✅ **Visualisations ASCII** - Charts, timelines, barres de performance
✅ **Export JSON** - Format structuré pour analyse externe
✅ **Intégration automatique** - Activé par défaut dans BattleEngine
✅ **API simple** - Méthodes claires pour toutes les données
✅ **Performance optimale** - Overhead minimal, scalable

Le système d'analytics transforme chaque bataille en source de données exploitables pour améliorer stratégies et performances! 📊🎯
