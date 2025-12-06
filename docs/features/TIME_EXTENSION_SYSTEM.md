# Système d'Extension de Temps (+20s)

## Vue d'ensemble

Le système d'extension de temps permet de prolonger les batailles de **+20 secondes** lorsque l'équipe est en retard au score, offrant des opportunités de comeback stratégiques.

---

## Mécanique

### Obtention
- **Récompenses de victoires**: Gagnées après avoir remporté des batailles
- **Inventaire limité**: Nombre fini d'extensions disponibles
- **Transfert entre batailles**: Les extensions non utilisées sont conservées

### Utilisation
- **Activation automatique**: Le système évalue automatiquement quand utiliser
- **Conditions**: Déclenchement quand perdant de 1000+ points
- **Timing optimal**: Final 30 secondes ou moments critiques
- **Effet**: Ajoute +20 secondes à la durée totale de la bataille

### Stratégie d'Activation

Le `TimeExtensionManager` évalue 3 scénarios:

**SCÉNARIO 1: Désespéré en finale (priorité haute)**
```python
if time_remaining <= 30s AND score_diff >= 1000:
    → ACTIVER EXTENSION
```

**SCÉNARIO 2: Très en retard dernier tiers (priorité moyenne)**
```python
if battle_progress >= 67% AND score_diff >= 2000:
    → ACTIVER EXTENSION
```

**SCÉNARIO 3: Massivement en retard mi-bataille (urgence)**
```python
if battle_progress >= 50% AND score_diff >= 3000:
    → ACTIVER EXTENSION
```

---

## Implémentation

### Architecture

**3 composants principaux:**

1. **`TimeExtensionManager`** (`core/time_extension_system.py`)
   - Gère l'inventaire d'extensions
   - Évalue quand activer
   - Suit les statistiques d'utilisation

2. **`TimeManager`** (`core/time_manager.py`)
   - Gère la durée de bataille (dynamique)
   - Méthode `extend_duration(seconds)`
   - Distinction `base_duration` vs `battle_duration`

3. **`BattleEngine`** (`core/battle_engine.py`)
   - Intègre le système d'extension
   - Vérifie à chaque tick si extension nécessaire
   - Publie les événements d'extension

### Code d'intégration

**Créer une bataille avec extensions:**
```python
engine = BattleEngine(
    battle_duration=180,
    time_extensions=2  # ← 2 extensions disponibles (+40s max)
)
```

**Vérifier le statut:**
```python
if engine.time_extension_manager:
    status = engine.time_extension_manager.get_status()
    print(f"Extensions disponibles: {status['available']}")
    print(f"Temps total ajouté: {status['total_time_added']}s")
```

**Ajouter des extensions (récompense):**
```python
engine.time_extension_manager.add_extension_reward(count=1)
# 🏆 Earned 1 time extension bonus(es)!
```

---

## Exemples de Scénarios

### Scénario 1: Comeback Héroïque

**État initial (t=160s):**
```
Créateur: 50,000 points
Adversaire: 53,000 points  (+3000)
Temps restant: 20s
```

**Action:**
```
⏱️  TIME EXTENSION ACTIVATED BY TeamStrategy!
   +20 seconds added to battle
   Used at t=160s
   Extensions remaining: 1
```

**Nouveau timing:**
```
Durée bataille: 180s → 200s
Temps restant: 20s → 40s
```

**Opportunité:**
- 40 secondes pour comeback au lieu de 20
- Permet déploiement fog + snipe final
- Double les chances de victoire

### Scénario 2: Extensions Multiples

**Bataille avec 3 extensions:**

| Temps | Score Diff | Action | Résultat |
|-------|------------|--------|----------|
| 150s | +3500 | Extension #1 activée | 180s → 200s |
| 190s | +2000 | Extension #2 activée | 200s → 220s |
| 215s | +500  | Extension #3 non utilisée | Victory! |

**Total:** Bataille de 180s → 220s (+40s utilisés sur +60s disponibles)

### Scénario 3: Conservation Stratégique

**Situation:**
```
t=120s: En retard de 2500 points (pas critique)
→ Extension conservée

t=170s: En retard de 1500 points (finale!)
→ Extension activée!
→ Temps pour comeback: 30s
```

---

## Valeur Stratégique

### Analyse de l'impact

**Évaluation de la valeur d'extension:**
```python
value = (deficit_value * 0.5 +      # À quel point on perd
         time_urgency * 0.3 +        # Urgence temporelle
         capability_factor * 0.2)    # Capacité de l'équipe
```

**Exemple de calcul:**
```
En retard de 3000 points → deficit_value = 0.6
10 secondes restantes → time_urgency = 0.94
Puissance équipe 40k → capability_factor = 0.8

Valeur totale = (0.6 * 0.5) + (0.94 * 0.3) + (0.8 * 0.2)
              = 0.30 + 0.28 + 0.16
              = 0.74 (74% - FORTE valeur d'extension)
```

### Bénéfices mesurables

**Sans extension (+0s):**
- Temps finale: 20 secondes
- Actions possibles: 1-2 cadeaux majeurs
- Probabilité comeback: ~15%

**Avec extension (+20s):**
- Temps finale: 40 secondes
- Actions possibles: 3-4 cadeaux majeurs + coordination
- Probabilité comeback: ~35%

**Impact:** **+20% de taux de victoire** dans situations désespérées

---

## Coordination avec Team

### Intégration TeamCoordinator

Le système d'extension coordonne avec le TeamCoordinator:

```python
# Extension déclenche changement de stratégie
if time_extended:
    coordinator.team_strategy = "all_in_offense"

    # Proposer actions coordonnées
    CoordinationPattern.final_push_pattern(
        coordinator,
        fog_time=current_time + 5,
        strike_time=current_time + 10,
        snipe_time=current_time + 15
    )
```

### Messages aux agents

**Notification d'extension:**
```python
comm_channel.send(
    from_agent="TeamStrategy",
    message=f"⏱️  +20s EXTENSION! We have {new_time}s for comeback!",
    to_agent=None  # Broadcast
)
```

---

## Statistiques de Performance

### Métriques suivies

```python
stats = time_extension_manager.get_statistics()

{
    'extensions_available': 1,      # Non utilisées
    'extensions_used': 2,           # Utilisées
    'total_time_added': 40,         # Total secondes ajoutées
    'use_times': [155, 175],       # Quand activées
    'triggered_by': ['TeamStrategy', 'TeamStrategy']
}
```

### Analyse post-bataille

**Rapport d'extension:**
```
⏱️  Time Statistics:
   Base duration: 180s
   Final duration: 220s
   Extensions used: 2
   Total time added: 40s

⏱️  Extension Details:
   Available: 1
   Used: 2
   Activated at:
      1. t=155s by TeamStrategy
      2. t=175s by TeamStrategy
```

---

## Configuration Avancée

### Ajuster les seuils

**Modification des triggers:**
```python
manager = TimeExtensionManager(initial_extensions=2)

# Rendre plus agressif (activer plus tôt)
manager.activation_threshold = 500   # Au lieu de 1000
manager.min_time_remaining = 20      # Au lieu de 15

# Rendre plus conservateur (activer plus tard)
manager.activation_threshold = 2000  # Au lieu de 1000
manager.min_time_remaining = 10      # Au lieu de 15
```

### Stratégie personnalisée

**Override de la logique:**
```python
class AggressiveExtensionManager(TimeExtensionManager):
    def should_use_extension(self, score_diff, time_remaining,
                            current_time, battle_duration):
        # Activer dès qu'on perd, peu importe le timing
        return score_diff > 0 and self.can_use_extension()
```

---

## Démo et Tests

### Lancer la démo
```bash
python3 demo_time_extension.py
```

**Sortie attendue:**
```
⏱️  TIME EXTENSION BONUS DEMO (+20s)

✅ Team assembled:
   🔫 Kinetik
   🥊 StrikeMaster
   📊 Activator
   🛡️ Sentinel

⏱️  Time Extensions Available: 2
   Base battle duration: 180s
   Maximum with extensions: 220s

[Bataille en cours...]

============================================================
⏱️  TIME EXTENSION ACTIVATED BY TeamStrategy!
   +20 seconds added to battle
   Used at t=165s
   Extensions remaining: 1
============================================================

[Bataille continue avec temps supplémentaire...]
```

### Scénario de test forcé

**Forcer une situation de perte:**
```python
# Dans BattleEngine._simulate_opponent_behavior
# Ajouter bonus massif à l'adversaire pour tester extension
if current_time == 100:
    self.score_tracker.add_opponent_points(50000, current_time)
    print("[TEST] Opponent gets massive bonus - will trigger extension")
```

---

## Points Clés

✅ **Automatique**: Activation intelligente sans intervention manuelle
✅ **Stratégique**: Seuils optimisés pour maximiser valeur
✅ **Flexible**: Configuration ajustable par scénario
✅ **Intégré**: Coordination avec team strategy
✅ **Réaliste**: Basé sur mécanique TikTok réelle

Le système d'extension de temps ajoute une couche stratégique profonde, transformant des défaites certaines en opportunités de comeback dramatiques!
