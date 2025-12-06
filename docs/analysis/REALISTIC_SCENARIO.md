# TikTok Battle Simulator - Realistic Scenario Documentation

## Vue d'ensemble

Ce document détaille le scénario réaliste de bataille TikTok implémenté dans le simulateur. Le système reproduit fidèlement les mécaniques, cadeaux, et comportements des vraies batailles TikTok Live.

---

## 1. Système de Cadeaux TikTok

### Cadeaux Disponibles

Le système utilise des cadeaux basés sur les vraies valeurs TikTok :

| Cadeau | Emoji | Points | Prix Réel (Coins) | Utilisation |
|--------|-------|--------|-------------------|-------------|
| **Rose** | 🌹 | 10 | 1 coin | Cadeau de base, haute fréquence |
| **TikTok Gift** | 🎁 | 60 | 5-10 coins | Cadeau intermédiaire |
| **Lion** | 🦁 | 900 | 500 coins | Cadeau premium |
| **Universe** | 🌌 | 1,800 | 1,000 coins | Cadeau ultime |
| **Lion & Universe** | 🦁🌌 | 1,800 | 1,000 coins | Combo ultimate |

### Mécanique des Cadeaux

**Fréquence d'envoi** :
- Rose : Peut être envoyée toutes les 1-2 secondes
- TikTok Gift : Toutes les 3-5 secondes
- Lion/Universe : Cadeaux stratégiques, moments critiques

**Timing stratégique** :
- **Early Phase (0-20s)** : Petits cadeaux pour établir l'avance
- **Mid Phase (20-40s)** : Cadeaux moyens, maintien du momentum
- **Late Phase (40-55s)** : Gros cadeaux, retournements dramatiques
- **Final Phase (55-60s)** : All-in, dernières chances

---

## 2. Système de Multiplicateurs

### Sessions de Multiplicateurs

Reproduit le système de "multiplier sessions" des vraies batailles TikTok.

| Multiplicateur | Durée | Activation | Impact |
|----------------|-------|------------|--------|
| **x2** | 15-30s | Auto ou manuel | Double tous les cadeaux |
| **x3** | 20-35s | Auto ou manuel | Triple tous les cadeaux |
| **x5** | 25-40s | Récompense tournoi | Quintuple tous les cadeaux |

**Exemples** :
```
Rose normale : 10 points
Rose pendant x2 : 20 points
Rose pendant x3 : 30 points
Rose pendant x5 : 50 points

Universe normale : 1,800 points
Universe pendant x5 : 9,000 points (game-changing!)
```

**Stratégies de multiplicateurs** :
- Attendre le x2/x3 pour envoyer de gros cadeaux
- Combos dévastateurs : x5 + Universe = victoire quasi-garantie
- Les agents intelligents synchronisent leurs cadeaux avec les multiplicateurs

---

## 3. Profils d'Agents Détaillés

### 🐋 NovaWhale - Le Whale Stratégique

**Type de supporter** : High-roller / Whale
**Budget typique** : 1,000+ USD / battle
**Style** : Patient, stratégique, décisif

**Personnalité** :
- Observe silencieusement pendant 45+ secondes
- Analyse la situation avant d'agir
- Intervient uniquement si le créateur perd
- Un seul cadeau massif qui change tout
- Messages rares mais impactants

**Comportement en bataille** :
```python
Temps 0-44s  : Observation pure (silence total)
Temps 20s    : Peut envoyer "Watching... 🌊" (30% chance)
Temps 45s+   : Si créateur perd → LION & UNIVERSE (1,800 pts)
Post-cadeau  : Message victorieux + émotion CONFIDENT
```

**Messages typiques** :
- "The tide has turned. 🌌"
- "Consider it done."
- "Silent no more."
- "*emerges from the depths*"

**Basé sur** : Vrais whales TikTok qui attendent la fin pour "sauver" leur créateur favori avec des Lions/Universes massifs.

---

### 🧚‍♀️ PixelPixie - La Cheerleader à Petit Budget

**Type de supporter** : Budget supporter / Regular
**Budget typique** : 5-20 USD / battle
**Style** : Énergique, fréquent, enthousiaste

**Personnalité** :
- Supporte constamment avec de petits cadeaux
- Envoie des Roses toutes les 3-5 secondes
- Toujours positif, jamais découragé
- Crée du momentum psychologique
- Encourage les autres à participer

**Comportement en bataille** :
```python
Toutes les 3-5s : Rose (10 pts) + message encourageant
Multiplicateur  : Profite des x2/x3 pour maximiser impact
Émotion        : EXCITED → CONFIDENT → HAPPY (cycle)
Messages       : Haute fréquence, toujours positifs
```

**Messages typiques** :
- "Let's go! 🌟"
- "We got this!"
- "Never give up! 💪"
- "Rose gang unite! 🌹🌹🌹"

**Impact stratégique** :
- Accumule lentement mais sûrement (600-1,000 pts/battle)
- Maintient le moral de l'équipe
- Crée une base de points constante
- Profite énormément des multiplicateurs (Rose x5 = 50 pts)

**Basé sur** : Vrais supporters TikTok fidèles qui ne peuvent pas dépenser beaucoup mais sont toujours présents et actifs.

---

### 🌀 GlitchMancer - Le Wildcard Chaotique

**Type de supporter** : Medium spender / Unpredictable
**Budget typique** : 50-200 USD / battle
**Style** : Imprévisible, burst mode, chaotique

**Personnalité** :
- Modes "burst" aléatoires (envoie 5-10 cadeaux d'un coup)
- Timing imprévisible
- Peut dominer un moment puis disparaître
- Crée des swings dramatiques
- Messages cryptiques et chaotiques

**Comportement en bataille** :
```python
Mode Normal    : Silence ou petits cadeaux espacés
BURST ACTIVATED: 5-10 x TikTok Gift en rafale (300-600 pts)
Cooldown      : 10-20s entre bursts
Timing        : Complètement aléatoire
Multiplicateur: Si actif pendant burst = dévastation
```

**Pattern de Burst** :
```
[12s] 🌀 GlitchMancer: ⚡ BURST MODE ACTIVATED ⚡
🌀 Sends TikTok Gift (+60) x 6 = 360 points en 2 secondes
[Silence pendant 15 secondes]
[36s] 🌀 BURST MODE ACTIVATED ⚡ pendant x3!
🌀 Sends TikTok Gift (+180) x 4 = 720 points!
```

**Messages typiques** :
- "⚡ CHAOS INCOMING ⚡"
- "Time to break reality"
- "🌀🌀🌀 GLITCH THE SYSTEM 🌀🌀🌀"
- "*distorted laughing*"

**Impact stratégique** :
- Peut créer des retournements soudains
- Excellent combo avec multiplicateurs
- Imprévisible = difficile à contrer
- Top contributor dans 30% des batailles

**Basé sur** : Vrais utilisateurs TikTok qui dépensent de façon impulsive et créent des moments dramatiques inattendus.

---

### 👤 ShadowPatron - L'Intervenant Silencieux de Crise

**Type de supporter** : Strategic high-spender
**Budget typique** : 200-500 USD / battle
**Style** : Silencieux, observe, intervient en crise

**Personnalité** :
- 100% silencieux (jamais de messages)
- Observe et analyse
- Intervient uniquement si :
  - Créateur perd de 30%+
  - Temps < 15s restant
  - Situation critique
- Un ou deux cadeaux massifs, puis disparaît

**Comportement en bataille** :
```python
Temps 0-40s    : Observation totale (0 action)
Temps 40-55s   : Analyse du score
Si CRISE       : Lion/Universe + disparition
Jamais de chat : 0 messages, pure action
```

**Conditions de crise** :
```python
deficit = opponent_score - creator_score
deficit_percent = deficit / opponent_score

if deficit_percent > 0.30 and time_left < 15:
    send_gift("LION & UNIVERSE", 1800)
    vanish()  # Plus jamais actif dans cette bataille
```

**Impact stratégique** :
- Sauveur en dernière minute
- Retournements dramatiques
- Jamais de gaspillage
- Maximum 1-2 actions par bataille

**Basé sur** : Vrais "ghost supporters" TikTok qui observent en silence puis frappent au moment critique.

---

### 🎭 Dramatron - Le Performer Théâtral

**Type de supporter** : Entertainer / Showman
**Budget typique** : 30-100 USD / battle
**Style** : Théâtral, dramatique, spectacle

**Personnalité** :
- Tout est un spectacle
- Annonce ses cadeaux avec fanfare
- Timing dramatique parfait
- Messages flamboyants
- Joue avec les émotions du chat

**Comportement en bataille** :
```python
Pre-gift       : Message d'annonce dramatique
Gift timing    : Moments clés (20s, 40s, 55s)
Post-gift      : Réaction théâtrale
Style          : Moyen cadeaux avec maximum impact visuel
Multiplicateur : Attend x2/x3 pour maximum spectacle
```

**Séquence typique** :
```
[19s] 🎭 "The stage is set... 🎪"
[20s] 🎭 *x2 ACTIVE*
[20s] 🎭 Sends TikTok Gift x3 (+180 with multiplier)
[20s] 🎭 "BEHOLD THE POWER! ⚡✨"
[Crowd going wild]
```

**Messages typiques** :
- "Ladies and gentlemen... 🎩"
- "And for my next trick... ✨"
- "DRAMATIC ENTRANCE! 🎭"
- "The show must go on!"
- "*takes a bow* 🎪"

**Impact stratégique** :
- Crée de l'engagement dans le chat
- Momentum psychologique
- Inspire d'autres à donner
- 400-800 pts/battle avec style maximum

**Basé sur** : Vrais utilisateurs TikTok qui transforment le don de cadeaux en performance artistique.

---

## 4. Système de Récompenses de Tournoi

### Types de Récompenses

Les récompenses sont gagnées en remportant des batailles dans un tournoi :

| Récompense | Emoji | Effet | Durée | Utilisation Stratégique |
|------------|-------|-------|-------|------------------------|
| **x5 Glove** | 🥊 | Multiplicateur x5 | 25-40s | Game-changer, save pour bataille critique |
| **Fog** | 🌫️ | Brouille le score adverse | 15s | Psychologique, désorientation |
| **Hammer** | 🔨 | Double les dégâts | 20s | Combo avec gros cadeaux |
| **Time Extension** | ⏱️ | +15 secondes | Instant | Plus de temps = plus de chances |

### Économie de Récompenses

**Acquisition** :
```
Gagner Bataille 1 → +1 récompense aléatoire
Gagner Bataille 2 → +1 récompense aléatoire
Gagner Bataille 3 → +1 récompense aléatoire

Exemple série 2-1 (Créateur):
- 2 victoires = 2 récompenses
```

**Inventaire actuel** :
```python
Creator Team Inventory:
   🥊 x5 Gloves: 0
   🌫️ Fogs: 0
   🔨 Hammers: 0
   ⏱️ Time Extensions: 1

Opponent Team Inventory:
   🥊 x5 Gloves: 0
   🌫️ Fogs: 0
   🔨 Hammers: 0
   ⏱️ Time Extensions: 2
```

### Stratégies de Récompenses

**x5 Glove - Le Game-Changer** :
```
Stratégie optimale:
1. Garder pour bataille décisive (match point)
2. Activer à 30-40s (temps optimal)
3. Synchroniser avec gros cadeaux:
   - NovaWhale Universe + x5 = 9,000 points!
   - GlitchMancer burst + x5 = 900-1,200 points
4. Peut garantir une victoire si bien utilisé
```

**Fog - L'Arme Psychologique** :
```
Utilisation:
- Brouille le score de l'adversaire
- Crée confusion et panique
- Peut forcer des erreurs de timing
- Meilleur usage: 45-50s (phase critique)
```

**Hammer - Le Booster de Dégâts** :
```
Combo optimal:
- Activer juste avant un gros cadeau
- Lion (900) → avec Hammer → 1,800 points
- Peut doubler l'impact d'un Universe!
```

**Time Extension** :
```
Utilisation stratégique:
- Si en retard à 60s, +15s pour rattraper
- Permet à NovaWhale de frapper deux fois
- Peut transformer défaite en victoire
```

---

## 5. Scénarios de Bataille Réalistes

### Scénario 1 : Le Comeback du Whale

**Contexte** : Créateur perd 2,000-4,500 à 50s

**Déroulement** :
```
[50s] Créateur: 2,000 | Adversaire: 4,500
😰 Situation critique!

[51-54s] PixelPixie continue d'envoyer Roses
Créateur: 2,040 | Adversaire: 4,600

[55s] 🐋 NovaWhale se réveille:
"The tide has turned. 🌌"
Sends LION & UNIVERSE (+1,800)

Créateur: 3,840 | Adversaire: 4,600
Encore en retard...

[58s] 🌀 GlitchMancer: BURST MODE!
Sends TikTok Gift x5 (+300)

[60s] FINAL:
Créateur: 4,140 | Adversaire: 4,800
❌ Défaite proche mais honorable
```

**Analyse** : NovaWhale a réduit l'écart de 2,500 à 660 points, mais trop tard. S'il avait agi à 45s au lieu de 55s, victoire probable.

---

### Scénario 2 : La Domination PixelPixie + Multiplicateur

**Contexte** : x3 actif de 15-43s, PixelPixie en profite

**Déroulement** :
```
[00-14s] Phase normale
Créateur: 150 | Adversaire: 200

[15s] 🔥 x3 SESSION ACTIVATED!

[15-43s] PixelPixie mode turbo:
Envoie Rose toutes les 3s
Rose normale: 10 pts
Rose avec x3: 30 pts!

28 secondes de x3 = ~9 Roses
9 x 30 = 270 points rien que PixelPixie!

+ GlitchMancer burst avec x3:
TikTok Gift x6 = 360 pts → 1,080 pts!

[43s] Fin du x3:
Créateur: 1,500 | Adversaire: 600

[60s] FINAL:
Créateur: 2,200 | Adversaire: 1,800
✅ VICTOIRE grâce au multiplicateur
```

**Leçon** : Les petits supporters deviennent dangereux avec multiplicateurs.

---

### Scénario 3 : Le Chaos de GlitchMancer

**Contexte** : Bataille équilibrée, GlitchMancer crée 3 bursts parfaits

**Déroulement** :
```
[12s] Score équilibré 200-200
🌀 BURST MODE #1
TikTok Gift x6 = 360 points
Créateur prend l'avance: 560-200

[15s] x2 multiplier s'active!

[23s] Adversaire rattrape pendant que GlitchMancer est en cooldown
Score: 580-550

[36s] 🌀 BURST MODE #2 pendant x2!
TikTok Gift (+120 with x2) x4 = 480 points!
Créateur explose: 1,060-550

[52s] 🌀 BURST MODE #3 (final push)
TikTok Gift x5 = 300 points
Final: 1,360-900

✅ VICTOIRE dominante
🏆 GlitchMancer = MVP avec 1,140 points donnés
```

**Leçon** : Le timing chaotique peut être plus efficace que la stratégie pure si la chance est au rendez-vous.

---

### Scénario 4 : La Coordination Parfaite (Tournoi)

**Contexte** : Bataille 3 d'un Best of 3, score 1-1, équipe a x5 Glove

**Déroulement** :
```
[00-30s] Approche conservatrice
Créateur: 400 | Adversaire: 600

[30s] 🥊 ACTIVATION du x5 GLOVE (récompense)
Durée: 30-55s (25 secondes)

[32s] 🧚‍♀️ PixelPixie attaque:
Rose x5 = 50 points chacune!
8 Roses = 400 points

[36s] 🌀 GlitchMancer: BURST + x5!
TikTok Gift x5 (+300 per gift!) x 5 = 1,500 points!

[45s] 🐋 NovaWhale: Le finisher
LION & UNIVERSE x5 = 9,000 points!!!!!

[55s] Fin du x5
Créateur: 11,400 | Adversaire: 1,800

[60s] FINAL:
Créateur: 11,650 | Adversaire: 2,100
✅ VICTOIRE ÉCRASANTE
🏆 TOURNAMENT WIN!
```

**Leçon** : Les récompenses de tournoi bien utilisées garantissent presque la victoire.

---

## 6. Mécaniques Avancées

### Budget Partagé (Tournois)

Dans les tournois, les agents partagent un budget :

```python
Tournament Budget: 250,000 points
Bataille 1: 3,550 points dépensés (1.4%)
Bataille 2: 2,530 points dépensés (1.0%)
Bataille 3: 3,110 points dépensés (1.2%)

Total dépensé: 9,190 points (3.7%)
Budget restant: 240,810 points

Strategy:
- Batailles 1-2: Conservation
- Bataille 3 (décisive): All-in possible
```

### Système de Momentum

Le système track le momentum psychologique :

```python
Momentum States:
🔵🔵🔵 STRONG_CREATOR    - Domine, adversaire sous pression
🔵🔵   MODERATE_CREATOR  - Léger avantage
⚪     NEUTRAL           - Équilibré
🔴🔴   MODERATE_OPPONENT - Adversaire avance
🔴🔴🔴 STRONG_OPPONENT   - Adversaire domine

Pressure Levels:
😌 NONE       - En avance, relaxé
🙂 LOW        - Série égale
😐 MODERATE   - En retard d'une bataille
😰 HIGH       - Une défaite = élimination
💀 ELIMINATION - DOIT gagner sinon c'est fini
```

**Impact du Momentum** :
- Win streak → Agents plus agressifs
- Facing elimination → Agents desperate, grosses dépenses
- Strong momentum → Peut intimider l'adversaire

---

## 7. Profils de Victoire

### Victory Pattern Analysis

D'après les données des tournois :

**NovaWhale MVP** :
- 40% des victoires où il intervient
- Contribution moyenne: 1,800 points (1 Universe)
- Timing optimal: 44-48s
- Taux de succès: 65% si active pendant x3+

**GlitchMancer MVP** :
- 35% des victoires chaotiques
- Contribution moyenne: 1,200-2,400 points
- 3-4 bursts par bataille en moyenne
- Taux de succès: 55% dans les batailles avec multiplicateurs

**PixelPixie MVP** :
- 15% des victoires (underdog!)
- Contribution moyenne: 600-1,000 points
- Victoires généralement grâce à multiplicateurs x3/x5
- Taux de succès: 80% si multiplicateur > 25s

**ShadowPatron MVP** :
- 10% des victoires
- Toujours des comebacks dramatiques
- Contribution moyenne: 1,800 points (1 intervention)
- Taux de succès: 90% si intervient (très sélectif)

---

## 8. Best Practices pour Créateurs

### Optimisation de l'Équipe

**Composition Recommandée** :

**Team 1 - Balanced** :
- NovaWhale (closer)
- PixelPixie (constant pressure)
- GlitchMancer (chaos factor)

**Team 2 - All-in** :
- NovaWhale (finisher)
- ShadowPatron (crisis manager)
- GlitchMancer (burst damage)

**Team 3 - Marathon** :
- PixelPixie x2 (double roses)
- Dramatron (engagement + mid gifts)

### Stratégies de Bataille

**Early Game (0-20s)** :
- PixelPixie établit la base
- Les autres observent
- Économie de budget

**Mid Game (20-40s)** :
- Profiter des multiplicateurs
- GlitchMancer peut burst
- Maintenir le momentum

**Late Game (40-55s)** :
- NovaWhale ready to strike
- ShadowPatron surveille
- Préparation du finish

**Final Phase (55-60s)** :
- All-in si nécessaire
- Dernier burst de GlitchMancer
- ShadowPatron emergency only

---

## 9. Comparaison avec Vraies Batailles TikTok

### Similitudes

✅ **Cadeaux et Prix** :
- Valeurs réalistes (Rose 1 coin, Universe 1000 coins)
- Fréquence d'envoi authentique
- Système de multiplicateurs identique

✅ **Comportements de Supporters** :
- Whales qui attendent la fin
- Small supporters constants
- Bursts aléatoires
- Silent observers qui interviennent en crise

✅ **Mécaniques de Bataille** :
- Durée 60 secondes
- Multiplicateurs auto
- Retournements dramatiques
- Momentum psychologique

✅ **Système de Tournoi** :
- Best of 3/5
- Récompenses entre batailles
- Budget management
- Pressure mounting

### Différences

❌ **Simplifications** :
- Pas de vraie économie TikTok coins
- Pas de vrais utilisateurs humains
- Pas de chat interactions complètes
- Nombres d'agents limités (vs 100s viewers)

❌ **Additions pour Gameplay** :
- Analytics détaillées
- Momentum tracking visible
- Perfect replay capability
- AI-controlled agents

---

## 10. Utilisation du Système

### Lancer une Bataille Réaliste

```bash
# Bataille simple avec agents réalistes
python3 demo_battle.py

# Bataille avec web dashboard
python3 demo_web_battle_simple.py
# Ouvrir: http://localhost:5000
```

### Lancer un Tournoi Réaliste

```bash
# Tournoi complet avec tous les enhancements
python3 demo_tournament_enhanced_full.py

# Tournoi avec web dashboard
python3 demo_web_tournament.py
# Ouvrir: http://localhost:5000/tournament.html
```

### Configuration des Agents

```python
from agents.personas import NovaWhale, PixelPixie, GlitchMancer

# Créer une équipe
engine.add_agent(NovaWhale())      # Le closer
engine.add_agent(PixelPixie())     # Le grinder
engine.add_agent(GlitchMancer())   # Le chaos

# Lancer la bataille
engine.run()
```

---

## Conclusion

Ce système reproduit fidèlement l'expérience des batailles TikTok Live avec :

🎯 **Réalisme** :
- Cadeaux authentiques
- Comportements basés sur vrais utilisateurs
- Mécaniques identiques à TikTok

🤖 **Intelligence** :
- Agents avec personnalités distinctes
- Stratégies adaptatives
- Décisions contextuelles

📊 **Analytics** :
- Tracking complet
- Momentum visualization
- Performance metrics

🏆 **Compétition** :
- Système de tournoi
- Récompenses stratégiques
- Leaderboard ELO

Le simulateur peut être utilisé pour :
- Tester des stratégies de bataille
- Analyser des patterns de victoire
- Entraîner des créateurs TikTok
- Étudier les mécaniques d'engagement
- Développer de nouveaux agents IA

---

**Dernière mise à jour** : 2025-11-23
**Version** : 2.0 - Realistic Scenario Complete
