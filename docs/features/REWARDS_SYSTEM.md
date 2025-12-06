# Système de Récompenses Basées sur la Performance 🏅

## Vue d'ensemble

Le système de récompenses récompense les **performances exceptionnelles** dans les batailles de tournoi.

---

## Règles de Distribution

### Standard (< 80,000 points)

```
Top Contributor < 80k points:
  → 1 récompense: Time Extension (+20s)
```

**Utilité:**
- Permet comebacks dans batailles suivantes
- Auto-activée quand en retard au score
- Resource de base pour progression

---

### Performance Bonus (≥ 80,000 points)

```
Top Contributor ≥ 80k points:
  → 3 récompenses:
    • 1 x5 Glove (strike multiplicateur)
    • 1 Fog (cache score)
    • 1 Hammer (counter enemy x5)
```

**Utilité:**
- Arsenal tactique complet
- Domination dans batailles suivantes
- Advantage stratégique majeur

---

## Exemples Concrets

### Exemple 1: Performance Standard

```
Battle 1:
  Winner: Creator
  Top Contributor: StrikeMaster
  Contribution: 59,998 points

  ❌ Pas de bonus (< 80k)

  Rewards:
    +1 time_ext

  Inventory après:
    Gloves: 0
    Fogs: 0
    Hammers: 0
    Time Extensions: 1
```

---

### Exemple 2: Performance Bonus

```
Battle 1:
  Winner: Creator
  Top Contributor: StrikeMaster
  Contribution: 89,997 points

  🎉 BONUS! (≥ 80k)

  Rewards:
    +1 x5_glove
    +1 fog
    +1 hammer

  Inventory après:
    Gloves: 1
    Fogs: 1
    Hammers: 1
    Time Extensions: 0
```

---

### Exemple 3: Série Complète

```
Best of 3 Tournament

Battle 1:
  Top Contributor: StrikeMaster (85,000 pts)
  🎉 BONUS → +1 glove, +1 fog, +1 hammer

Battle 2:
  Top Contributor: Activator (45,000 pts)
  Standard → +1 time extension

Battle 3:
  Top Contributor: Kinetik (92,000 pts)
  🎉 BONUS → +1 glove, +1 fog, +1 hammer

Final Inventory:
  Gloves: 2
  Fogs: 2
  Hammers: 2
  Time Extensions: 1

Résultat: Arsenal complet pour futures batailles!
```

---

## Stratégies

### 🎯 Quand Viser le Bonus (80k+)?

**DO** ✅:
- **Match Point**: Viser bonus en Battle 2 si leading 1-0
- **Comeback**: Bonus en Battle 2 si trailing 0-1 pour ressources Battle 3
- **Multiplicateurs disponibles**: x3 session active = facilite 80k+
- **Budget suffisant**: >100k remaining dans tournoi

**DON'T** ❌:
- **Budget faible**: <80k remaining (risque d'échec)
- **Déjà leading 2-0**: Économiser budget
- **Batailles perdues**: Ne pas gaspiller sur défaites
- **Sans multiplicateurs**: Difficile d'atteindre 80k en base

---

### 💎 Utilisation des Récompenses

#### x5 Glove 🥊
```
Quand utiliser:
  • Pendant session x2/x3 (additive)
  • Moment critique (final 30s)
  • Pour sécuriser victoire

Impact:
  Base 29,999 × 5 = 149,995 points
  Avec x3: (29,999 × 3) + (29,999 × 5) = 239,992 points!
```

#### Fog 🌫️
```
Quand utiliser:
  • Avant setup de snipe final
  • Cache preparation de strike
  • Empêche counter-stratégie adverse

Durée: ~30 secondes
Combo: Fog → Kinetik Snipe
```

#### Hammer 🔨
```
Quand utiliser:
  • Counter enemy x5 strike
  • Défense critique
  • Annule 150k+ points adverses

Timing: Réactif (quand ennemi lance x5)
```

#### Time Extension ⏱️
```
Utilisation: Automatique
  • Activée si losing by 1000+ pts
  • +20 secondes pour comeback
  • Multiple extensions = long battles

Stratégie: Accumulation passive
```

---

## Mathématiques des Contributions

### Composition d'une Contribution 80k+

**Base (sans multiplicateurs):**
```
2-3 Lions = 2 × 29,999 = 59,998 (insuffisant)
Besoin multiplicateurs pour 80k+
```

**Avec x2 Session:**
```
Lion × 2 = 59,998 points
+ Activator roses (5 points)
+ Kinetik Galaxy (1,000 points)
= ~61,000 points (insuffisant)
```

**Avec x3 Session:**
```
Lion × 3 = 89,997 points ✅
+ Roses + Galaxy = ~91,000 points
= BONUS GARANTI!
```

**Avec x3 + x5 (combo):**
```
Lion pendant x3:
  Base × 3 = 89,997

Puis x5 strike:
  Base × 5 = 149,995

Total: 239,992 points (domination absolue)
```

---

## Impact sur le Gameplay

### Accumulation Progressive

**Tournament BO3:**
```
Battle 1: Bonus → 3 items tactiques
Battle 2: Standard → 1 time ext
Battle 3: Utilise items accumulés → Victoire

Inventory final:
  Si 3-0: 3 gloves, 3 fogs, 3 hammers (domination)
  Si 2-1: 1-2 de chaque (standard)
```

**Tournament BO5:**
```
Battles 1-3: Accumulation
Battle 4-5: Utilisation ressources

Max possible: 5 bonus = 15 items tactiques!
```

---

### Momentum Shifts

**Scénario: Comeback**
```
Battle 1: Opponent gagne (creator gets 0 rewards)
  Series: 0-1

Battle 2: Creator gagne avec bonus (85k contribution)
  Rewards: +1 glove, +1 fog, +1 hammer
  Series: 1-1

Battle 3: Creator utilise items accumulés
  - Fog pour stealth
  - x5 Glove strike
  - Victoire décisive
  Series: 2-1 (comeback!)
```

---

## Détection du Top Contributor

### Algorithme

```python
top_contributor = None
top_contribution = 0

for agent, stats in agent_performance.items():
    contribution = stats['total_donated']
    if contribution > top_contribution:
        top_contribution = contribution
        top_contributor = agent

# Check bonus threshold
if top_contribution >= 80000:
    rewards = BONUS (3 items)
else:
    rewards = STANDARD (1 time ext)
```

### Contributions par Agent

**StrikeMaster:** Souvent top contributor
- Lions (29,999) × multiplicateurs
- Contributions typiques: 60k-90k

**Kinetik:** Occasionnellement top
- Final snipe (1,000-5,000)
- Rare > 80k (nécessite multiples snipes)

**Activator:** Rarement top
- Roses (1 point each)
- Support role, pas contributeur majeur

**Sentinel:** Jamais top
- Rôle défensif (fog/hammer)
- 0 contribution directe aux points

---

## Affichage en Jeu

### Battle Results

**Standard:**
```
⭐ Top Contributor: StrikeMaster
   Contribution: 59,998 points

🎁 Rewards Earned by Creator:
   +1 time_ext
```

**Bonus:**
```
⭐ Top Contributor: StrikeMaster
   Contribution: 89,997 points
   🎉 BONUS! Spent 80k+ → 3 récompenses!

🎁 Rewards Earned by Creator (Performance Bonus!):
   +1 x5_glove
   +1 fog
   +1 hammer
```

### Tournament Summary

```
⭐ Performance Highlights:
   Battle 1: StrikeMaster (89,997) 🎉 BONUS!
   Battle 2: StrikeMaster (59,998)
   Battle 3: Kinetik (85,000) 🎉 BONUS!

🎁 Final Inventory:
   Gloves: 2 | Fogs: 2 | Hammers: 2 | Time: 1
```

---

## Configuration

### Code

```python
from core.tournament_system import TournamentManager

# Créer tournoi
tournament = TournamentManager(
    format=TournamentFormat.BEST_OF_3,
    total_budget=250000
)

# Lancer
tournament.start_tournament()

# Battle loop
while tournament.can_continue():
    # ... run battle ...

    # Enregistrer avec performance
    performance = engine.analytics.get_agent_performance()

    tournament.record_battle_result(
        winner=winner,
        creator_score=c_score,
        opponent_score=o_score,
        budget_spent_this_battle=budget,
        agent_performance=performance  # ← Calcule rewards automatiquement
    )
```

### Bonus Threshold

```python
# Dans tournament_system.py
BONUS_THRESHOLD = 80000  # Points minimum pour bonus

if top_contribution >= BONUS_THRESHOLD:
    # 3 récompenses: glove + fog + hammer
    rewards = BattleReward(x5_gloves=1, fogs=1, hammers=1, time_extensions=0)
else:
    # Standard: 1 time extension
    rewards = BattleReward(x5_gloves=0, fogs=0, hammers=0, time_extensions=1)
```

---

## Statistiques

### Taux de Bonus

```
Performance Bonus Rate = Battles avec 80k+ / Total Battles

Excellent: >60% (stratégie agressive réussie)
Bon: 40-60% (équilibré)
Moyen: 20-40% (conservative)
Faible: <20% (sous-performance)
```

### Distribution Typique (BO3)

**Aggressive Play:**
```
2 battles avec bonus (2/2 = 100%)
Inventory: 2 gloves, 2 fogs, 2 hammers
```

**Balanced Play:**
```
1 battle avec bonus (1/2 = 50%)
Inventory: 1 glove, 1 fog, 1 hammer, 1 time ext
```

**Conservative Play:**
```
0 battles avec bonus (0/2 = 0%)
Inventory: 2 time extensions
```

---

## API Reference

### BattleReward

```python
@dataclass
class BattleReward:
    x5_gloves: int = 0
    fogs: int = 0
    hammers: int = 0
    time_extensions: int = 0
```

**Configurations:**
```python
# Standard
standard = BattleReward(time_extensions=1)

# Bonus
bonus = BattleReward(x5_gloves=1, fogs=1, hammers=1)
```

### record_battle_result()

```python
tournament.record_battle_result(
    winner: str,                    # "creator" ou "opponent"
    creator_score: int,             # Score final
    opponent_score: int,            # Score final
    budget_spent_this_battle: int,  # Budget dépensé
    agent_performance: Dict         # Stats d'agents (optionnel)
)
```

**Performance Dict:**
```python
{
    "StrikeMaster": {
        "total_donated": 89997,
        "gifts_sent": 1,
        "avg_gift_value": 89997.0
    },
    "Kinetik": {
        "total_donated": 1000,
        ...
    }
}
```

---

## Best Practices

### Maximisation des Bonus

✅ **DO**:
1. Utiliser multiplicateurs x3 (facilite 80k+)
2. Focus contributions sur 1 agent
3. Timing optimal (sessions multiplicateurs)
4. Budget suffisant (>100k)

❌ **DON'T**:
1. Distribuer contributions sur multiples agents
2. Ignorer multiplicateurs disponibles
3. Sur-dépenser sans atteindre 80k
4. Viser bonus avec budget insuffisant

### Utilisation Stratégique

**Items Tactiques (Bonus):**
- Conserver pour batailles critiques
- Combiner (fog + glove strike)
- Ne pas gaspiller sur victoires acquises

**Time Extensions (Standard):**
- Accumulation passive
- Auto-utilisées en cas de besoin
- Assurance comeback

---

## Résumé

✅ **Système de Récompenses**
- Performance < 80k: 1 time extension
- Performance ≥ 80k: 3 items tactiques (glove + fog + hammer)

✅ **Impact**
- Récompense excellence
- Encourage investissement stratégique
- Crée momentum entre batailles
- Balance risk/reward

✅ **Stratégie**
- Viser bonus dans batailles clés
- Utiliser multiplicateurs pour faciliter 80k+
- Accumulation progressive sur série
- Usage tactique des items gagnés

Le système de récompenses transforme chaque performance en avantage stratégique! 🏅🎯
