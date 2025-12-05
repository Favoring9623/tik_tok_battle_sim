# Système de Tournoi Amélioré 🎉

## Nouvelles Fonctionnalités

### 1. 🏅 Récompenses Basées sur la Performance

**Règle:** Le plus grand contributeur d'une bataille victorieuse qui a dépensé **80,000+ points** reçoit **3x les récompenses**.

#### Mécanique

**Standard (contribution < 80k):**
```
Victory rewards = 1 glove, 1 fog, 1 hammer, 1 time extension
```

**Bonus Performance (contribution ≥ 80k):**
```
Victory rewards = 3 gloves, 3 fogs, 3 hammers, 3 time extensions
```

#### Exemple Réel

```
Battle 1: Creator wins
  Top Contributor: StrikeMaster
  Contribution: 89,997 points
  🎉 BONUS! 80k+ → 3X REWARDS!

  Rewards Earned:
    +3 x5_glove
    +3 fog
    +3 hammer
    +3 time_ext
```

#### Impact Stratégique

**Avantages:**
- ✅ Récompense les performances exceptionnelles
- ✅ Encourage l'investissement dans victoires critiques
- ✅ Accélère accumulation de ressources
- ✅ Crée momentum pour batailles suivantes

**Inconvénients:**
- ⚠️ Nécessite dépense importante (80k+)
- ⚠️ Risque si bataille perdue
- ⚠️ Peut épuiser budget rapidement

**Stratégies:**

**All-In Strategy** 🔥
- Viser 80k+ dans batailles critiques (ex: Battle 1, match point)
- Utiliser multiplicateurs pour maximiser contribution (x3 + x5)
- Objectif: Accumulation rapide de ressources

**Conservative Strategy** 🛡️
- Viser victoires standards (~50-60k)
- Éviter risque de sur-dépense
- Préserver budget pour série longue

**Adaptive Strategy** 🎯
- Analyser série: si 0-1, viser bonus dans Battle 2
- Si leading 2-0, économiser budget
- Utiliser bonus quand momentum nécessaire

---

### 2. 🎲 Budgets Aléatoires par Bataille

**Règle:** Chaque bataille a un **scénario budgétaire aléatoire** qui définit les contraintes de dépense.

#### Scénarios Disponibles

##### 🔥 Aggressive
```
Description: High spending, all-out attack
Budget Range: 80,000 - 120,000 points
Strategy: Utiliser multiplicateurs x3/x5, viser domination
Use Case: Must-win situations, match point, comeback
```

##### ⚖️ Balanced
```
Description: Moderate spending, standard play
Budget Range: 50,000 - 80,000 points
Strategy: Jeu équilibré, gestion prudente
Use Case: Batailles normales, série serrée
```

##### 🛡️ Conservative
```
Description: Low spending, resource management
Budget Range: 30,000 - 50,000 points
Strategy: Économiser, minimal viable victory
Use Case: Préservation budget, leading in series
```

##### ⚡ Clutch
```
Description: All-in, must-win
Budget Range: 100,000 - 150,000 points
Strategy: Tout donner, pas de retenue
Use Case: Elimination matches, desperate situations
```

#### Exemple de Tournoi

```
Best of 3 Tournament (250,000 total budget)

Battle 1: 🛡️ Conservative (45,416 limit)
  - Budget spent: 61,003
  - Stratégie: Victoire efficace sans gaspillage
  - Result: Creator wins

Battle 2: ⚖️ Balanced (69,604 limit)
  - Budget spent: 91,002
  - Stratégie: Push pour victoire finale
  - Result: Creator wins 2-0

Total: 152,005 / 250,000 (60.8%)
Budget saved: 97,995 points
```

#### Impact sur le Gameplay

**Diversité:**
- ✅ Chaque bataille a contraintes différentes
- ✅ Force adaptation stratégique
- ✅ Empêche stratégies répétitives
- ✅ Rend matchs plus imprévisibles

**Équilibrage:**
- ✅ Crée scenarios plus serrés
- ✅ Évite domination écrasante
- ✅ Favorise matches compétitifs
- ✅ Augmente suspense

**Stratégie:**
- ✅ Nécessite lecture de scenario
- ✅ Adaptation en temps réel
- ✅ Gestion budgétaire complexe
- ✅ Décisions tactiques

---

## Utilisation

### Configuration Basique

```python
from core.tournament_system import TournamentManager, TournamentFormat

# Créer tournoi
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=250000,
    battle_duration=180
)

# Activer budgets aléatoires
tournament.enable_random_budgets()

# Lancer tournoi
tournament.start_tournament()
```

### Configuration Avancée

```python
# Scénarios personnalisés (seulement certains)
tournament.enable_random_budgets(
    scenarios=["aggressive", "clutch"]  # Seulement high-stakes
)

# OU utiliser tous les scénarios (défaut)
tournament.enable_random_budgets()  # Tous: aggressive, balanced, conservative, clutch
```

### Enregistrement avec Performance

```python
# Après bataille
winner, scores, budget, performance = run_battle(tournament)

# Enregistrer avec données de performance
tournament.record_battle_result(
    winner=winner,
    creator_score=scores[0],
    opponent_score=scores[1],
    budget_spent_this_battle=budget,
    agent_performance=performance  # ← Active bonus rewards si 80k+
)
```

### Récupération du Scénario

```python
# Avant bataille
scenario_name, budget_limit = tournament.get_random_budget_limit()

print(f"Scenario: {scenario_name}")
print(f"Budget Limit: {budget_limit:,} points")

# Exemple output:
# Scenario: 🔥 Aggressive
# Budget Limit: 86,257 points
```

---

## Exemples de Scénarios

### Scénario 1: Comeback avec Bonus

```
Battle 1: Opponent wins (standard rewards)
  Series: 0-1

Battle 2: Creator wins with performance bonus
  Top Contributor: StrikeMaster (92,000 points)
  🎉 3X REWARDS!
  Inventory: +3 gloves, +3 fogs, +3 hammers, +3 time ext
  Series: 1-1

Battle 3: Creator uses accumulated resources
  - 3 time extensions available
  - 3 fogs for stealth strategy
  - 3 gloves for x5 strikes
  Result: Creator wins 2-1 (comeback victory!)
```

**Analysis:**
- Performance bonus en Battle 2 a fourni ressources pour Battle 3
- Accumulation rapide a permis comeback
- Strategic use of bonus rewards = victory

---

### Scénario 2: Budget Management Challenge

```
Battle 1: 🔥 Aggressive (110,000 limit)
  Spent: 105,000
  Remaining: 145,000
  Result: Creator wins (standard)

Battle 2: ⚡ Clutch (135,000 limit)
  Spent: 125,000
  Remaining: 20,000
  Result: Creator wins (standard)
  Series: 2-0

Total: 230,000 / 250,000 (92%)
```

**Analysis:**
- Deux scénarios high-spending consécutifs
- Budget presque épuisé mais victoire 2-0
- Risqué mais efficace
- Pas de Battle 3 nécessaire

---

### Scénario 3: Conservative + Bonus Stack

```
Battle 1: 🛡️ Conservative (40,000 limit)
  Spent: 35,000
  Top Contributor: 32,000 points (no bonus)
  Remaining: 215,000
  Result: Creator wins

Battle 2: ⚖️ Balanced (65,000 limit)
  Spent: 55,000
  Top Contributor: 52,000 points (no bonus)
  Remaining: 160,000
  Result: Opponent wins
  Series: 1-1

Battle 3: 🔥 Aggressive (95,000 limit)
  Spent: 95,000
  Top Contributor: StrikeMaster (85,000 points)
  🎉 3X REWARDS!
  Remaining: 65,000
  Result: Creator wins 2-1

Total: 185,000 / 250,000 (74%)
```

**Analysis:**
- Budget conservé dans battles 1-2
- All-in avec bonus en Battle 3 décisive
- Perfect timing pour performance bonus
- Victoire finale avec ressources restantes

---

## Statistiques et Analytics

### Données Collectées

**Battle-Level Performance:**
```json
{
  "battle_number": 1,
  "winner": "creator",
  "top_contributor": "StrikeMaster",
  "top_contribution": 89997,
  "bonus_rewards_earned": true,
  "budget_spent": 91002
}
```

**Tournament Stats:**
```python
stats = tournament.get_tournament_stats()

# Performance highlights
for battle in stats['battles']:
    if battle['bonus_rewards_earned']:
        print(f"Battle {battle['number']}: {battle['top_contributor']} "
              f"({battle['top_contribution']:,}) 🎉 3X BONUS!")
```

### Métriques Clés

**Performance Bonus Rate:**
```
Bonus Rate = Battles with 80k+ contribution / Total Battles
High Performance = >50% bonus rate
Average = 20-40%
Conservative = <20%
```

**Budget Scenario Distribution:**
```
Aggressive: % of battles
Balanced: % of battles
Conservative: % of battles
Clutch: % of battles
```

**Resource Accumulation:**
```
Avg Rewards per Battle = Total Inventory / Battles Won
With Bonuses: ~2.0 items/battle
Without Bonuses: 1.0 items/battle
```

---

## API Reference

### TournamentManager.enable_random_budgets()

```python
tournament.enable_random_budgets(
    scenarios: Optional[List[str]] = None
)
```

**Parameters:**
- `scenarios`: Liste des scénarios à utiliser
  - `None` (défaut): Tous les scénarios
  - `["aggressive", "clutch"]`: Seulement high-stakes
  - `["balanced", "conservative"]`: Seulement moderate

**Scénarios disponibles:**
- `"aggressive"`: 80k-120k
- `"balanced"`: 50k-80k
- `"conservative"`: 30k-50k
- `"clutch"`: 100k-150k

### TournamentManager.get_random_budget_limit()

```python
scenario_name, budget_limit = tournament.get_random_budget_limit()
```

**Returns:**
- `scenario_name` (str): Nom du scénario (ex: "🔥 Aggressive")
- `budget_limit` (int): Limite de budget pour la bataille (ex: 86257)

**Usage:**
```python
# Avant chaque bataille
scenario, limit = tournament.get_random_budget_limit()
print(f"Scenario: {scenario} (Max: {limit:,})")
```

### TournamentManager.record_battle_result()

```python
tournament.record_battle_result(
    winner: str,
    creator_score: int,
    opponent_score: int,
    budget_spent_this_battle: int,
    agent_performance: Optional[Dict[str, Dict]] = None  # ← Nouveau
)
```

**Parameters:**
- `winner`: "creator" ou "opponent"
- `creator_score`: Score final creator
- `opponent_score`: Score final opponent
- `budget_spent_this_battle`: Budget dépensé
- `agent_performance`: **NOUVEAU** - Dict de stats d'agents
  - Format: `{"AgentName": {"total_donated": 89997, ...}, ...}`
  - Utilisé pour calculer top contributor et bonus rewards

**Performance Calculation:**
```python
# Depuis BattleAnalytics
performance = engine.analytics.get_agent_performance()
# {"StrikeMaster": {"total_donated": 89997, ...}, ...}

# Passer au tournament
tournament.record_battle_result(
    winner=winner,
    creator_score=c_score,
    opponent_score=o_score,
    budget_spent_this_battle=budget,
    agent_performance=performance  # Calcule bonus automatiquement
)
```

---

## Demos Disponibles

### Quick Test (Non-Interactive)
```bash
python3 demo_tournament_enhanced_quick.py
```

Montre:
- Performance-based rewards en action
- Random budget scenarios
- Complete BO3 tournament
- Performance highlights

### Interactive Demo
```bash
python3 demo_tournament_enhanced.py
```

Fonctionnalités:
- Pause entre batailles
- Détails complets de scénarios
- Budget tracking interactif
- Performance analysis

### Utilisation Programmatique

```python
from core.tournament_system import TournamentManager, TournamentFormat
from core.battle_engine import BattleEngine

# Setup
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=250000
)
tournament.enable_random_budgets()
tournament.start_tournament()

# Battle loop
while tournament.can_continue():
    # Get scenario
    scenario, limit = tournament.get_random_budget_limit()

    # Run battle
    engine = BattleEngine(battle_duration=180, enable_analytics=True)
    # ... add agents, run ...

    # Record with performance
    performance = engine.analytics.get_agent_performance()
    tournament.record_battle_result(
        winner=engine.analytics.winner,
        creator_score=engine.analytics.final_scores["creator"],
        opponent_score=engine.analytics.final_scores["opponent"],
        budget_spent_this_battle=calculate_budget(performance),
        agent_performance=performance
    )
```

---

## Best Practices

### Quand Viser le Bonus (80k+)?

✅ **DO**:
- Battles critiques (match point, elimination)
- Quand leading in series (resources for later)
- Quand multiplicateurs x3 disponibles
- Opponent est faible (score bas)

❌ **DON'T**:
- Si budget insuffisant (<100k remaining)
- Dans battles perdues (gaspillage)
- Trop tôt dans série (préserver budget)
- Quand victoire standard suffit

### Adaptation aux Scénarios

**🔥 Aggressive (80-120k)**:
- Utiliser multiplicateurs max (x3 + x5)
- Viser performance bonus si possible
- Investir dans victoire dominante

**⚖️ Balanced (50-80k)**:
- Jeu standard, efficace
- Multiplicateurs opportunistes
- Bon équilibre risk/reward

**🛡️ Conservative (30-50k)**:
- Minimal viable victory
- Économiser ressources
- Préserver budget pour later

**⚡ Clutch (100-150k)**:
- All-in mentality
- Combiner tous multiplicateurs
- Viser performance bonus absolute

---

## Résumé

### Nouvelles Fonctionnalités

✅ **Performance-Based Rewards**
- 80k+ contribution = 3x rewards
- Encourage excellence
- Accelerates resource accumulation

✅ **Random Budget Scenarios**
- 4 scénarios différents
- Crée diversité
- Favorise matchs serrés

### Impact

🎯 **Gameplay plus riche**
- Adaptation stratégique nécessaire
- Décisions tactiques complexes
- Matches plus imprévisibles

🏆 **Compétition améliorée**
- Récompense performance exceptionnelle
- Balance entre risk et reward
- Momentum shifts plus dramatiques

💎 **Resource Economy**
- Gestion budgétaire critique
- Accumulation stratégique
- Long-term planning

Le système de tournoi amélioré transforme chaque série en expérience unique avec des décisions stratégiques profondes! 🎮🔥
