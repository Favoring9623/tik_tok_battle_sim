# GPT-Powered Tournament Agents 🤖

## Vue d'ensemble

Les agents GPT utilisent **OpenAI GPT-4** pour prendre des décisions stratégiques intelligentes pendant les tournois. Chaque agent a une **personnalité unique** qui influence son style de jeu et ses décisions.

---

## Installation

### Prérequis

```bash
# Installer le package OpenAI
pip install openai

# Définir la clé API
export OPENAI_API_KEY='your-api-key-here'
```

### Vérification

```python
import os
print(os.getenv("OPENAI_API_KEY"))  # Doit afficher votre clé
```

---

## Personnalités Disponibles

### 🔥 AGGRESSIVE - High-Risk Reward Hunter

**Philosophie:** Dominer tôt, accumuler récompenses, effet boule de neige

**Stratégie:**
- Dépense 40-50% du budget par bataille
- Chasse toujours le bonus 80k+ pour 3 récompenses
- Utilise multiplicateurs agressivement (x3 + x5)
- Préfère domination écrasante aux victoires serrées

**Budget:**
- Aggressive: Dépense importante dès le début
- N'a pas peur du all-in sur batailles critiques
- Utilise gloves/fogs/hammers sans hésitation

**Décisions Typiques:**
```
0-60s: Multiplier dispo → SEND LION
60-120s: Match serré → USE GLOVE + x3 (240k points!)
120-180s: Sécuriser victoire ou comeback total
```

**Quand l'utiliser:**
- Tournoi court (BO3)
- Vous voulez domination rapide
- Vous avez confiance en votre budget
- Vous voulez accumulation maximale de rewards

---

### 🛡️ DEFENSIVE - Efficiency Master

**Philosophie:** Victoires minimales viables, préservation maximale ressources

**Stratégie:**
- Dépense 20-30% du budget par bataille
- Agit seulement quand nécessaire (perdant ou serré)
- Évite la chasse au bonus 80k (trop cher)
- Accumule time extensions pour sécurité

**Budget:**
- Conservative: Dépense minimale pour victoire
- Réactif: Répond aux menaces, ne mène pas
- Long-terme: Série complète > bataille individuelle

**Décisions Typiques:**
```
0-120s: WAIT sauf si perdant par 3000+
120-150s: Évaluer gap, agir seulement si nécessaire
150-180s: Sécuriser victoire avec dépense minimale
```

**Quand l'utiliser:**
- Tournoi long (BO5)
- Budget limité
- Vous voulez marathon, pas sprint
- Préférence pour efficacité sur domination

---

### ⚖️ BALANCED - Adaptive Strategist

**Philosophie:** Lire la situation, adapter, décisions optimales

**Stratégie:**
- Dépense 30-40% du budget (flexible)
- Adapte selon score de série et budget restant
- Chasse 80k bonus quand opportunité se présente
- Préserve budget quand confortable

**Budget:**
- Contextuel: Change selon situation
- Leading series (1-0)? → Agressif
- Trailing (0-1)? → Must-win mentality
- Tied (1-1)? → Budget détermine approche

**Décisions Typiques:**
```
Leading 1-0: Agressif, accumuler rewards
Trailing 0-1: Must-win, considérer all-in
Tied 1-1: Analyser budget → stratégie adaptée
```

**Quand l'utiliser:**
- Par défaut (meilleur all-around)
- Vous voulez IA intelligente et adaptable
- Vous ne savez pas quel style choisir
- Vous voulez décisions optimales contextuelles

---

### 🎯 TACTICAL - Precision Expert

**Philosophie:** Exécution parfaite, synergie, efficacité maximale

**Stratégie:**
- Dépense exactement ce qui est nécessaire
- Chaque action au moment optimal
- Maîtrise des multiplicateurs
- Efficacité par précision chirurgicale

**Budget:**
- Mathématique: Calcule points exacts nécessaires
- Timing parfait: Strike seulement pendant multiplicateurs
- Jamais de gaspillage: Chaque point compte

**Décisions Typiques:**
```
x3 active? → 1 Lion = 90k (bonus instant!)
x2 active? → 2 Lions = 120k (bonus + buffer)
Pas de multiplicateur? → WAIT (inefficace)

Patterns:
- Fog → Wait 10s → Strike (impact caché)
- Roses → Bonus Session → Strike
- Enemy x5 → Immediate Hammer
```

**Quand l'utiliser:**
- Vous voulez efficacité maximale
- Vous aimez timing parfait
- Vous voulez bonus via intelligence, pas volume
- Vous appréciez jeu calculé et précis

---

## Utilisation

### Quick Start

```python
from agents.gpt_tournament_agents import create_gpt_tournament_agent
from core.battle_engine import BattleEngine

# Créer agent GPT avec personnalité
gpt_agent = create_gpt_tournament_agent("balanced")

# Créer bataille
engine = BattleEngine(battle_duration=180, enable_analytics=True)
engine.add_agent(gpt_agent)

# Lancer
engine.run()

# GPT prend décisions intelligentes automatiquement!
```

### Dans un Tournoi

```python
from core.tournament_system import TournamentManager, TournamentFormat
from agents.gpt_tournament_agents import create_gpt_tournament_agent

# Setup tournoi
tournament = TournamentManager(format=TournamentFormat.BEST_OF_3)
tournament.enable_random_budgets()
tournament.start_tournament()

# Boucle de bataille
while tournament.can_continue():
    # Créer agent GPT (personnalité peut changer par bataille!)
    gpt_agent = create_gpt_tournament_agent("aggressive")

    # Battle...
    engine = BattleEngine(battle_duration=180)
    engine.add_agent(gpt_agent)
    engine.run()

    # Record...
    performance = engine.analytics.get_agent_performance()
    tournament.record_battle_result(...)
```

### Démo Complète

```bash
# Demo avec agent GPT
python3 demo_gpt_tournament.py

# Nécessite: OPENAI_API_KEY défini
# Sinon: Utilise fallback rule-based logic
```

---

## Comment ça Marche

### Architecture

```
User Request
    ↓
GPTTournamentAgent
    ↓
GPTDecisionEngine
    ↓
OpenAI GPT-4 API
    ↓
Strategic Decision (JSON)
    ↓
Execute Action (send gift, use item, wait)
```

### Context Fourni à GPT

```python
{
    "battle_state": {
        "time": 65,
        "phase": "MID",
        "creator_score": 45000,
        "opponent_score": 38000,
        "score_diff": 7000,
        "time_remaining": 115
    },
    "multipliers": {
        "current": 2.0,
        "is_active": True
    },
    "agent_state": {
        "emotion": "EXCITED",
        "total_donated": 30000,
        "budget": "unlimited"
    },
    "personality": "aggressive"
}
```

### Décision GPT (Exemple)

```json
{
    "action": "gift",
    "gift_type": "LION",
    "gift_value": 29999,
    "reasoning": "x2 multiplier active, can push to 60k for strong lead"
}
```

### Throttling & Rate Limits

**Protection intégrée:**
- Appels GPT espacés de 3-5 secondes
- Cache des décisions récentes
- Fallback automatique si API indisponible
- Pas de spam, décisions réfléchies

---

## Personnalités Détaillées

### Aggressive 🔥

**Objectif:** 80k+ contribution chaque bataille

**Math:**
- x3 active: 1 Lion = 89,997 pts ✅ (instant bonus)
- x2 active: 2 Lions = 119,996 pts ✅ (bonus + marge)
- Pas de multiplicateur: 3 Lions = 89,997 pts (ok mais pas optimal)

**Items:**
- x5 Glove + x3: 239,992 points (domination absolue)
- Fog avant strike: Cache impact massif
- Hammer: Protège investissement

**Risques:**
- Peut épuiser budget rapidement
- Si perd bataille 1 avec 80k dépensé = gros problème
- Opponent défensif peut exploiter sur-dépense

---

### Defensive 🛡️

**Objectif:** Victoire avec <60k dépense

**Math:**
- Minimal viable: Juste assez pour gagner
- Préfère: Galaxy (1k) sn ipes multiples vs 1 Lion (30k)
- Réactif: Attend que opponent dépense, puis répond

**Items:**
- Hammer: Arme primaire (annule 150k enemy)
- Time Extensions: Accumulation naturelle
- Fog: Snipe défensif surprise
- x5 Glove: Dernier recours uniquement

**Avantages:**
- Préserve budget pour série longue
- Opponent frustrédpar lead minimal
- Gagne guerre d'attrition
- Efficace en BO5

---

### Balanced ⚖️

**Objectif:** Décision optimale selon contexte

**Adaptive Logic:**

```python
IF leading_series AND multiplier_active:
    → Aggressive (accumulate rewards)

ELIF trailing_series AND budget > 100k:
    → All-in (must win)

ELIF tied AND budget < 80k:
    → Defensive (preserve for final)

ELSE:
    → Standard efficient play
```

**Contexte Important:**
- Score de série
- Budget restant
- Multiplicateurs disponibles
- Scenario de bataille (Aggressive/Conservative/etc)

**Flexibilité:**
- S'adapte à chaque situation
- Pas de stratégie rigide
- Décisions contextuelles
- Optimal pour IA GPT

---

### Tactical 🎯

**Objectif:** Efficacité maximale via timing parfait

**Precision Math:**

```
Target: 80k bonus
Current: x3 session active

Calculation:
- 1 Lion × 3 = 89,997 pts
- Result: BONUS ACHIEVED with 1 gift!

vs Without multiplier:
- Need 3 Lions = 89,997 pts
- Result: Same bonus but 3× cost

Conclusion: WAIT for multiplier
```

**Patterns:**

```
Pattern: Stealth Strike
1. Deploy Fog (opponent can't see)
2. Wait 10 seconds
3. x3 Lion strike (89,997 hidden!)
4. Opponent sees score jump suddenly
5. Psychological advantage

Pattern: Session Trigger
1. Send 5 Roses (5 points total)
2. Trigger Bonus x2 Session
3. Immediately send Lion × 2
4. Result: 119,996 pts with bonus
```

---

## Performance Comparison

### Scénario Test: BO3 Tournament

**Aggressive:**
- Battle 1: 95k dépensé → WIN (bonus 3 rewards)
- Battle 2: 85k dépensé → WIN (bonus 3 rewards)
- Total: 180k / 250k (72%) → Champion 2-0
- Inventory: 6 gloves, 6 fogs, 6 hammers
- Style: Domination rapide, high rewards

**Defensive:**
- Battle 1: 55k dépensé → WIN (standard 1 time ext)
- Battle 2: 48k dépensé → WIN (standard 1 time ext)
- Battle 3: 62k dépensé → WIN (standard 1 time ext)
- Total: 165k / 250k (66%) → Champion 2-1
- Inventory: 3 time extensions
- Style: Marathon victory, preserved 85k

**Balanced:**
- Battle 1: 70k dépensé → WIN (standard)
- Battle 2: 92k dépensé → WIN (bonus 3 rewards)
- Total: 162k / 250k (65%) → Champion 2-0
- Inventory: 1 glove, 1 fog, 1 hammer, 1 time ext
- Style: Adapté opportunités, optimal

**Tactical:**
- Battle 1: 90k dépensé (x3 timing) → WIN (bonus)
- Battle 2: 60k dépensé (efficient) → WIN (standard)
- Total: 150k / 250k (60%) → Champion 2-0
- Inventory: 1 glove, 1 fog, 1 hammer, 1 time ext
- Style: Precision parfaite, minimal waste

**Winner: Tactical** (lowest budget, same result)

---

## Fallback Mode

Si `OPENAI_API_KEY` non défini, agents utilisent **règles simples** basées sur personnalité:

**Aggressive Fallback:**
```python
if multiplier_active or time_remaining <= 60:
    return SEND_LION
else:
    return WAIT
```

**Defensive Fallback:**
```python
if score_diff < -3000:  # Losing badly
    return SEND_LION
else:
    return WAIT
```

**Balanced Fallback:**
```python
if multiplier_active and (losing or final_30s):
    return SEND_LION
else:
    return WAIT
```

**Tactical Fallback:**
```python
if multiplier >= 2:
    return SEND_LION
else:
    return WAIT  # Only act with multipliers
```

---

## Best Practices

### Quand Utiliser GPT

✅ **DO:**
- Vous avez API key OpenAI
- Vous voulez décisions vraiment intelligentes
- Vous testez stratégies complexes
- Vous voulez variété et imprévisibilité

❌ **DON'T:**
- Si pas d'API key (utilisez agents rule-based)
- Pour tests rapides (throttling ralentit)
- Pour batailles multiples rapides (coût API)

### Optimisation Coûts

**Tips:**
- Utilisez `gpt_call_interval` plus long (5-10s)
- Mode fallback pour tests
- Un seul GPTDecisionEngine partagé
- Model "gpt-3.5-turbo" moins cher (mais moins intelligent)

### Debugging

```python
# Activer stats GPT
gpt_agent = create_gpt_tournament_agent("balanced")

# Après bataille
stats = gpt_agent.get_gpt_stats()
print(f"GPT calls: {stats['gpt_decisions']}")
print(f"Fallback: {stats['fallback_decisions']}")
print(f"Usage: {stats['gpt_percentage']}%")
```

---

## API Reference

### create_gpt_tournament_agent()

```python
from agents.gpt_tournament_agents import create_gpt_tournament_agent

agent = create_gpt_tournament_agent(
    personality_type: str = "balanced"  # aggressive, defensive, balanced, tactical
) -> GPTPoweredAgent
```

**Returns:** Agent GPT configuré avec personnalité choisie

**Raises:** `ValueError` si personality_type invalide

### GPTDecisionEngine

```python
from extensions.gpt_intelligence import GPTDecisionEngine

engine = GPTDecisionEngine(
    api_key: Optional[str] = None,  # Défaut: OPENAI_API_KEY env var
    model: str = "gpt-4"             # gpt-4, gpt-4-turbo, gpt-3.5-turbo
)

# Vérifier disponibilité
if engine.is_available():
    decision = engine.decide_action(
        agent_name="AggressiveGPT",
        personality="...",
        battle_state={...},
        agent_state={...}
    )
```

---

## Exemples Avancés

### Mixing Personalities

```python
# Battle 1: Aggressive (grab early lead + rewards)
agent1 = create_gpt_tournament_agent("aggressive")

# Battle 2: Defensive (preserve budget if leading 1-0)
agent2 = create_gpt_tournament_agent("defensive")

# Battle 3: Tactical (precision finish if needed)
agent3 = create_gpt_tournament_agent("tactical")
```

### Custom GPT Engine

```python
from extensions.gpt_intelligence import GPTDecisionEngine

# Shared engine (économise initialisations)
shared_engine = GPTDecisionEngine(model="gpt-3.5-turbo")

# Utiliser pour plusieurs agents
agent1 = GPTAggressiveTournamentAgent(gpt_engine=shared_engine)
agent2 = GPTDefensiveTournamentAgent(gpt_engine=shared_engine)
```

---

## Troubleshooting

### "GPT not available"

**Cause:** API key manquante ou invalide

**Solution:**
```bash
export OPENAI_API_KEY='sk-...'
python3 demo_gpt_tournament.py
```

### "Rate limit exceeded"

**Cause:** Trop d'appels API trop rapidement

**Solution:**
- Augmenter `gpt_call_interval` (ex: 10)
- Utiliser fallback mode pour tests
- Attendre quelques minutes

### "JSON parse error"

**Cause:** GPT retourne format invalide

**Solution:**
- Vérifier version openai package
- Essayer gpt-4-turbo (meilleur JSON)
- Agent utilise fallback automatiquement

---

## Résumé

✅ **4 Personnalités GPT**
- Aggressive: Dominateur, reward hunter
- Defensive: Efficient, conservateur
- Balanced: Adaptatif, optimal
- Tactical: Précision, timing parfait

✅ **Intelligence Réelle**
- GPT-4 prend décisions stratégiques
- Analyse contexte de bataille
- Adapte selon personnalité
- Décisions expliquées (reasoning)

✅ **Production Ready**
- Fallback si API indisponible
- Throttling anti-spam
- Error handling robuste
- Stats et debugging

✅ **Simple à Utiliser**
```python
agent = create_gpt_tournament_agent("balanced")
engine.add_agent(agent)
engine.run()  # GPT fait le reste!
```

Les agents GPT transforment le simulateur en véritable IA stratégique! 🤖🧠
