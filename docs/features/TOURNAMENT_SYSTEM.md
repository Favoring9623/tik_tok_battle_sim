# Système de Tournoi 🏆

## Vue d'ensemble

Le système de tournoi permet de jouer des séries de batailles **Best of 3** ou **Best of 5** avec:
- **Budget partagé** de 250,000 points pour toute la série
- **Récompenses** distribuées au vainqueur de chaque bataille
- **Inventaire persistant** entre les batailles
- **Statistiques complètes** de tournoi

---

## Formats Disponibles

### Best of 3 (BO3)
- **Objectif**: Premier à **2 victoires**
- **Batailles max**: 3
- **Durée typique**: 9-15 minutes (3 × 180s)

### Best of 5 (BO5)
- **Objectif**: Premier à **3 victoires**
- **Batailles max**: 5
- **Durée typique**: 15-25 minutes (5 × 180s)

---

## Budget Partagé

### Mécanique

**Budget Total**: 250,000 points pour toute la série

**Règles**:
1. Le budget est **partagé** entre toutes les batailles
2. Points dépensés = somme de tous les cadeaux envoyés
3. Le budget **ne se recharge pas** entre batailles
4. **Gestion stratégique** nécessaire pour la série complète

### Exemple

```
Tournoi Best of 3 (250,000 points disponibles):

Battle 1: Creator gagne
  - Budget dépensé: 61,003 points
  - Restant: 188,997 points

Battle 2: Creator gagne
  - Budget dépensé: 91,002 points
  - Restant: 97,995 points

Total utilisé: 152,005 / 250,000 (60.8%)
Victoire en 2 batailles, économie de 97,995 points!
```

### Stratégies

**Early Dominance** 🔥
- Dépenser massivement dans les 2 premières batailles
- Objectif: Gagner 2-0 rapidement
- Risque: Budget insuffisant si ça va à la 3ème

**Conservative Play** 🛡️
- Dépenser ~60-80k par bataille
- Budget équilibré sur 3 batailles
- Sécurise la série même si ça va long

**Adaptive Strategy** 🎯
- Analyse après chaque bataille
- Ajuste dépenses selon la série
- Ex: Si 1-1, all-in dans la bataille 3

---

## Système de Récompenses

### Récompenses par Victoire

Le **vainqueur de chaque bataille** reçoit:

| Récompense | Quantité | Description |
|------------|----------|-------------|
| 🥊 x5 Glove | 1 | Peut déclencher un strike x5 |
| 🌫️ Fog | 1 | Cache le score de l'adversaire |
| 🔨 Hammer | 1 | Annule un x5 ennemi |
| ⏱️ Time Extension | 1 | Bonus de +20 secondes |

### Accumulation

**Exemple Best of 5**:
```
Creator gagne 3 batailles sur 5:
  🥊 x5 Gloves: 3
  🌫️ Fogs: 3
  🔨 Hammers: 3
  ⏱️ Time Extensions: 3

Opponent gagne 2 batailles:
  🥊 x5 Gloves: 2
  🌫️ Fogs: 2
  🔨 Hammers: 2
  ⏱️ Time Extensions: 2
```

### Utilisation des Récompenses

**x5 Gloves** 🥊
- Utilisés par **StrikeMaster**
- Déclenchent un strike x5 (multiplicateur additionnel)
- Optimal pendant sessions x2/x3

**Fogs** 🌫️
- Utilisés par **Sentinel**
- Cache votre score pendant ~30 secondes
- Parfait pour setup de snipe final

**Hammers** 🔨
- Utilisés par **Sentinel**
- Neutralisent un strike x5 ennemi
- Défense critique contre gros strikes

**Time Extensions** ⏱️
- **Auto-activées** par le système
- Ajoutent +20 secondes quand en retard
- Permettent comebacks stratégiques

---

## Architecture

### Composants Principaux

**1. `TournamentManager`**
```python
class TournamentManager:
    def __init__(self, format, total_budget, battle_duration)
    def start_tournament()
    def can_continue() -> bool
    def record_battle_result(winner, scores, budget_spent)
    def get_tournament_stats() -> Dict
```

**2. `SharedBudget`**
```python
class SharedBudget:
    total_budget: int = 250000
    spent: int = 0
    remaining: int = 250000

    def spend(amount, agent_name) -> bool
    def get_status() -> Dict
```

**3. `TeamInventory`**
```python
class TeamInventory:
    x5_gloves: int
    fogs: int
    hammers: int
    time_extensions: int

    def add_reward(reward: BattleReward)
    def consume_item(item_type, count) -> bool
    def get_status() -> Dict
```

**4. `BattleReward`**
```python
@dataclass
class BattleReward:
    x5_gloves: int = 1
    fogs: int = 1
    hammers: int = 1
    time_extensions: int = 1
```

---

## Utilisation

### Quick Start - Best of 3

```python
from core.tournament_system import TournamentManager, TournamentFormat

# Créer tournoi
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=250000,
    battle_duration=180
)

# Lancer
tournament.start_tournament()

# Boucle de bataille
while tournament.can_continue():
    # Jouer bataille
    winner, c_score, o_score, budget_spent = run_battle(tournament)

    # Enregistrer résultat
    tournament.record_battle_result(
        winner=winner,
        creator_score=c_score,
        opponent_score=o_score,
        budget_spent_this_battle=budget_spent
    )

# Stats finales
stats = tournament.get_tournament_stats()
print(f"Champion: {stats['tournament_winner']}")
```

### Démo Complète

```bash
# Quick test (automatique, non-interactif)
python3 demo_tournament_quick.py

# Best of 3 (interactif)
python3 demo_tournament_bo3.py

# Best of 5 (interactif avec analytics)
python3 demo_tournament_bo5.py
```

---

## Exemples de Scénarios

### Scénario 1: Sweep 2-0

```
Best of 3 Tournament

Battle 1: Creator wins (61,003 vs 7,287)
  - Budget: 61,003 / 250,000 (24.4%)
  - Rewards: Creator +1 each

Battle 2: Creator wins (91,002 vs 7,476)
  - Budget: 91,002 / 188,997 (48.2% of remaining)
  - Rewards: Creator +1 each

CHAMPION: CREATOR (2-0)
Budget used: 152,005 / 250,000 (60.8%)
Creator inventory: 2 gloves, 2 fogs, 2 hammers, 2 time ext
```

**Analysis**:
- ✅ Victoire rapide en 2 batailles
- ✅ Budget bien géré (40% restant)
- ✅ Double récompenses pour usage futur
- ⚠️ Opponent n'a eu aucune récompense

---

### Scénario 2: Comeback 3-2

```
Best of 5 Tournament

Battle 1: Opponent wins (45,000 vs 52,000)
  - Creator: 0-1
  - Opponent rewards: +1 each

Battle 2: Opponent wins (38,000 vs 48,000)
  - Creator: 0-2 (danger!)
  - Opponent rewards: +1 each (total: 2)

Battle 3: Creator wins (95,000 vs 42,000)
  - Creator: 1-2
  - Creator rewards: +1 each
  - Heavy spending to avoid elimination

Battle 4: Creator wins (88,000 vs 39,000)
  - Creator: 2-2 (comeback!)
  - Creator rewards: +1 each (total: 2)

Battle 5: Creator wins (72,000 vs 51,000)
  - CHAMPION: CREATOR (3-2)
  - Creator rewards: +1 each (total: 3)

Budget used: 238,000 / 250,000 (95.2%)
```

**Analysis**:
- 🎯 Comeback héroïque après 0-2
- 💰 Budget presque épuisé (95%)
- 🏆 Victory despite early deficit
- 📊 High drama, close series

---

### Scénario 3: Budget Management Failure

```
Best of 3 Tournament

Battle 1: Creator wins (125,000 vs 45,000)
  - Budget: 125,000 / 250,000 (50%)
  - Rewards: Creator +1 each
  - ⚠️ Heavy spending!

Battle 2: Opponent wins (80,000 vs 95,000)
  - Budget: 80,000 / 125,000 (64% of remaining)
  - Rewards: Opponent +1 each
  - Series tied 1-1

Battle 3: Creator needs to win
  - Budget available: 45,000 points
  - ❌ Insufficient for decisive victory
  - Opponent wins with modest spending

CHAMPION: OPPONENT (2-1)
Budget mismanagement led to defeat!
```

**Lessons**:
- ❌ Don't overspend in Battle 1
- ❌ Keep budget for potential Battle 3
- ✅ Conservative strategy safer for BO3

---

## Statistiques et Analytics

### Data Collectées

**Tournament Level**:
```python
{
    "format": "BEST_OF_3",
    "total_battles": 2,
    "creator_wins": 2,
    "opponent_wins": 0,
    "tournament_winner": "creator",
    "budget": {
        "total": 250000,
        "spent": 152005,
        "remaining": 97995,
        "spent_percent": 60.8
    },
    "creator_inventory": {
        "x5_gloves": 2,
        "fogs": 2,
        "hammers": 2,
        "time_extensions": 2
    },
    "opponent_inventory": { ... }
}
```

**Battle Level**:
```python
{
    "battle_number": 1,
    "winner": "creator",
    "creator_score": 61003,
    "opponent_score": 7287,
    "score_diff": 53716,
    "budget_spent": 61003,
    "rewards_earned": { ... }
}
```

### Métriques Clés

**Budget Efficiency**:
```
Budget par bataille = Total Spent / Battles Played
Budget restant par victoire = Remaining / Wins Needed
Utilisation % = (Spent / Total) × 100
```

**Win Rate**:
```
Win Rate = Creator Wins / Total Battles
Sweep Rate = Wins without opponent win
Comeback Rate = Wins after trailing in series
```

**Reward Accumulation**:
```
Total Rewards = Wins × Rewards per Battle
Reward Advantage = Creator Inventory - Opponent Inventory
```

---

## Configuration Avancée

### Custom Rewards

```python
from core.tournament_system import BattleReward

# Généreux (plus de récompenses)
generous_rewards = BattleReward(
    x5_gloves=2,      # 2 gloves par victoire
    fogs=2,
    hammers=2,
    time_extensions=2
)

tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_5,
    reward_config=generous_rewards
)
```

### Custom Budget

```python
# Budget élevé (plus de marge)
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=500000  # Double budget
)

# Budget serré (challenge)
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=150000  # Budget réduit
)
```

### Custom Battle Duration

```python
# Batailles courtes
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    battle_duration=60  # 60s par bataille
)

# Batailles longues
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_5,
    battle_duration=300  # 5 minutes par bataille
)
```

---

## API Reference

### TournamentManager

#### Initialisation

```python
tournament = TournamentManager(
    format: TournamentFormat = TournamentFormat.BEST_OF_3,
    total_budget: int = 250000,
    battle_duration: int = 180,
    reward_config: Optional[BattleReward] = None
)
```

#### Méthodes Principales

**`start_tournament()`**
- Initialise et annonce le tournoi
- Affiche format, budget, récompenses

**`can_continue() -> bool`**
- Vérifie si le tournoi peut continuer
- Retourne `False` si victoire ou max batailles

**`record_battle_result(winner, creator_score, opponent_score, budget_spent)`**
- Enregistre résultat d'une bataille
- Distribue récompenses au vainqueur
- Met à jour statistiques
- Vérifie fin de tournoi

**`get_tournament_stats() -> Dict`**
- Retourne statistiques complètes
- Format, batailles, scores, budget, inventaires

**`get_available_time_extensions(team: str) -> int`**
- Retourne nombre d'extensions disponibles
- Utilisé pour initialiser BattleEngine

**`print_series_status()`**
- Affiche état actuel de la série
- Scores, inventaires, budget

### SharedBudget

```python
budget = SharedBudget(total_budget=250000)

# Dépenser
success = budget.spend(amount=50000, agent_name="StrikeMaster")

# Status
status = budget.get_status()
# {"total": 250000, "spent": 50000, "remaining": 200000, "spent_percent": 20.0}

# Afficher
budget.print_status()
```

### TeamInventory

```python
inventory = TeamInventory(team_name="Creator Team")

# Ajouter récompenses
reward = BattleReward()
inventory.add_reward(reward)

# Consommer item
success = inventory.consume_item(RewardType.X5_GLOVE, count=1)

# Status
status = inventory.get_status()
# {"x5_gloves": 1, "fogs": 1, "hammers": 1, "time_extensions": 1}

# Afficher
inventory.print_inventory()
```

---

## Intégration avec BattleEngine

### Time Extensions

```python
# Récupérer extensions du tournoi
time_ext = tournament.get_available_time_extensions("creator")

# Créer battle avec extensions
engine = BattleEngine(
    battle_duration=180,
    time_extensions=time_ext  # Passé au engine
)
```

### Budget Tracking

```python
# Après bataille
performance = engine.analytics.get_agent_performance()
budget_spent = sum(stats['total_donated'] for stats in performance.values())

# Enregistrer dépense
tournament.shared_budget.spend(budget_spent, "Tournament")
```

### Inventory Usage

**StrikeMaster avec Gloves**:
```python
# Check inventory avant strike
if tournament.creator_inventory.x5_gloves > 0:
    # Consommer glove
    tournament.creator_inventory.consume_item(RewardType.X5_GLOVE)
    # Exécuter strike
    strike_master.execute_x5_strike(battle)
```

**Sentinel avec Fog/Hammer**:
```python
# Deploy fog
if tournament.creator_inventory.fogs > 0:
    tournament.creator_inventory.consume_item(RewardType.FOG)
    sentinel.deploy_fog(battle)

# Use hammer
if tournament.creator_inventory.hammers > 0:
    tournament.creator_inventory.consume_item(RewardType.HAMMER)
    sentinel.deploy_hammer(battle)
```

---

## Best Practices

### Budget Management

✅ **DO**:
- Plan budget for all potential battles
- Save 30-40% for final battle
- Track spending after each battle
- Adjust strategy based on remaining budget

❌ **DON'T**:
- Spend >50% in first battle
- Go all-in unless must-win situation
- Ignore budget remaining
- Assume you'll win in 2 battles

### Reward Strategy

✅ **DO**:
- Use time extensions strategically
- Save gloves for critical moments
- Combine fog + snipe for max effect
- Use hammers to counter enemy x5

❌ **DON'T**:
- Waste gloves on already-won battles
- Use fog too early
- Forget about accumulated rewards
- Ignore opponent's inventory

### Tournament Planning

✅ **DO**:
- Choose format based on time available
- Consider BO5 for more strategic depth
- Track series momentum
- Adapt between battles

❌ **DON'T**:
- Start BO5 without time commitment
- Use same strategy every battle
- Ignore opponent patterns
- Tilt after losses

---

## Résumé

✅ **Formats**: Best of 3 (first to 2) et Best of 5 (first to 3)
✅ **Budget**: 250,000 points partagés pour toute la série
✅ **Récompenses**: 4 types d'items par victoire
✅ **Inventaire**: Persistence entre batailles
✅ **Analytics**: Stats complètes de tournoi
✅ **Stratégie**: Gestion budget + accumulation récompenses

Le système de tournoi ajoute une couche stratégique profonde avec gestion de ressources à long terme! 🏆
