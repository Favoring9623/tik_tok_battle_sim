# GPT Setup Guide 🤖

Guide complet pour configurer l'intelligence GPT-4 dans le TikTok Battle Simulator.

---

## Table des Matières

1. [Prérequis](#prérequis)
2. [Obtenir une Clé API OpenAI](#obtenir-une-clé-api-openai)
3. [Configuration de la Clé](#configuration-de-la-clé)
4. [Vérification](#vérification)
5. [Demos Disponibles](#demos-disponibles)
6. [Troubleshooting](#troubleshooting)

---

## Prérequis

### 1. Package OpenAI

```bash
# Installer le package OpenAI
pip install openai

# OU si vous utilisez un virtualenv
source .venv/bin/activate  # Activer le virtualenv
pip install openai
```

### 2. Package python-dotenv (Recommandé)

Pour utiliser un fichier `.env` (méthode recommandée):

```bash
pip install python-dotenv
```

---

## Obtenir une Clé API OpenAI

### Étape 1: Créer un Compte OpenAI

1. Allez sur https://platform.openai.com/signup
2. Créez un compte (email + mot de passe)
3. Vérifiez votre email

### Étape 2: Générer une Clé API

1. Connectez-vous sur https://platform.openai.com/
2. Cliquez sur votre profil (coin supérieur droit)
3. Sélectionnez **"View API keys"**
4. Cliquez **"Create new secret key"**
5. Donnez un nom à votre clé (ex: "TikTok_Battle_Sim")
6. **COPIEZ LA CLÉ IMMÉDIATEMENT** (vous ne pourrez plus la revoir!)

⚠️ **IMPORTANT**: Votre clé commence par `sk-` et fait environ 50 caractères.

### Étape 3: Ajouter du Crédit (si nécessaire)

- OpenAI offre parfois un crédit gratuit pour nouveaux comptes
- Sinon, ajoutez au minimum $5 de crédit dans **Billing**
- GPT-4 coûte environ $0.03 par bataille (très raisonnable!)

---

## Configuration de la Clé

### ✅ Méthode 1: Fichier .env (RECOMMANDÉ)

**Avantages:**
- Sécurisé (ne jamais commit le .env dans git!)
- Automatique (pas besoin d'export à chaque session)
- Facile à modifier

**Instructions:**

1. **Créer le fichier `.env` à la racine du projet:**

```bash
cd /home/quantum-edge/IdeaProjects/tik_tok_battle_sim
echo "OPENAI_API_KEY=sk-votre-vraie-cle-ici" > .env
```

2. **Vérifier que `.env` est dans `.gitignore`:**

```bash
# Ajouter .env au .gitignore s'il n'y est pas déjà
echo ".env" >> .gitignore
```

3. **Structure du fichier `.env`:**

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**C'est tout!** Le code charge automatiquement `.env` via `python-dotenv`.

---

### Méthode 2: Variable d'Environnement

**Avantages:**
- Rapide pour tester
- Pas de fichier supplémentaire

**Inconvénients:**
- À refaire à chaque nouvelle session terminal
- Limité à la session courante

**Instructions:**

```bash
# Définir la variable pour la session actuelle
export OPENAI_API_KEY='sk-votre-vraie-cle-ici'

# Lancer votre demo
python3 demo_gpt_personas.py
```

**Pour rendre permanent (bash):**

```bash
# Ajouter à votre ~/.bashrc
echo 'export OPENAI_API_KEY="sk-votre-vraie-cle-ici"' >> ~/.bashrc
source ~/.bashrc
```

**Pour rendre permanent (zsh):**

```bash
# Ajouter à votre ~/.zshrc
echo 'export OPENAI_API_KEY="sk-votre-vraie-cle-ici"' >> ~/.zshrc
source ~/.zshrc
```

---

### Méthode 3: Directement dans le Code (NON RECOMMANDÉ)

⚠️ **DANGEREUX** - Ne jamais commit une clé API dans le code!

```python
# NE FAITES CECI QUE POUR DES TESTS LOCAUX
from extensions.gpt_intelligence import GPTDecisionEngine

engine = GPTDecisionEngine(api_key="sk-votre-cle-ici")
```

---

## Vérification

### Test 1: Vérifier que Python voit la Clé

```bash
python3 -c "import os; key = os.getenv('OPENAI_API_KEY'); print('✅ Clé trouvée!' if key else '❌ Pas de clé'); print(f'Longueur: {len(key) if key else 0} caractères')"
```

**Résultat attendu:**
```
✅ Clé trouvée!
Longueur: 51 caractères
```

### Test 2: Vérifier l'Initialisation GPT

```bash
python3 -c "from extensions.gpt_intelligence import GPTDecisionEngine; engine = GPTDecisionEngine(); print('✅ GPT disponible!' if engine.is_available() else '❌ GPT indisponible')"
```

**Résultat attendu:**
```
✅ GPT disponible!
```

### Test 3: Test Complet (API Call)

```python
# test_gpt.py
from extensions.gpt_intelligence import GPTDecisionEngine

engine = GPTDecisionEngine()

if engine.is_available():
    print("✅ GPT Engine initialisé!")

    # Test simple
    decision = engine.decide_action(
        agent_name="TestAgent",
        personality="You are a test agent. Be brief.",
        battle_state={
            "time": 30,
            "phase": "MID",
            "creator_score": 1000,
            "opponent_score": 800,
            "score_diff": -200,
            "time_remaining": 30
        },
        agent_state={
            "emotion": "CALM",
            "total_donated": 0,
            "budget": 5000
        }
    )

    print(f"✅ Décision GPT: {decision}")
else:
    print("❌ GPT non disponible - vérifier la clé API")
```

```bash
python3 test_gpt.py
```

---

## Demos Disponibles

### 1. GPT Tournament Agents 🏆

Agents spécialisés pour les tournois avec 4 personnalités distinctes:

```bash
python3 demo_gpt_tournament.py
```

**Agents:**
- 🔥 Aggressive - High-risk, reward hunting
- 🛡️ Defensive - Conservative, efficient
- ⚖️ Balanced - Adaptive, context-aware
- 🎯 Tactical - Precision timing

**Documentation:** Voir `GPT_AGENTS.md`

### 2. GPT Persona Agents 🎭

Les agents originaux avec intelligence GPT:

```bash
python3 demo_gpt_personas.py
```

**Agents:**
- 🐋 NovaWhale - Strategic whale
- 🧚‍♀️ PixelPixie - Enthusiastic cheerleader
- 🌀 GlitchMancer - Chaotic burst-mode
- 👤 ShadowPatron - Silent crisis intervener
- 🎭 Dramatron - Theatrical performer

---

## Troubleshooting

### ❌ Problème: "OPENAI_API_KEY not set"

**Causes possibles:**
1. Clé non définie
2. Virtualenv non activé
3. Fichier `.env` mal placé ou mal formaté

**Solutions:**

```bash
# 1. Vérifier si la clé existe
echo $OPENAI_API_KEY

# 2. Si vide, créer .env
echo "OPENAI_API_KEY=sk-votre-cle" > .env

# 3. Vérifier que python-dotenv est installé
pip install python-dotenv

# 4. Tester
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

---

### ❌ Problème: "Rate limit exceeded"

**Cause:** Trop de requêtes GPT trop rapidement.

**Solutions:**

1. **Augmenter l'intervalle entre appels:**

```python
# Dans votre code
agent = create_gpt_tournament_agent("balanced")
agent.gpt_call_interval = 10  # 10 secondes entre appels (au lieu de 4-5)
```

2. **Utiliser fallback mode pour tests:**

```python
# Les agents utilisent automatiquement fallback si GPT indisponible
# Pas besoin de modifier le code
```

3. **Attendre quelques minutes** puis réessayer

---

### ❌ Problème: "Invalid API key"

**Causes:**
1. Clé copiée incorrectement
2. Clé révoquée
3. Espaces ou caractères invisibles dans la clé

**Solutions:**

```bash
# 1. Vérifier la clé (afficher sans espaces)
python3 -c "import os; key = os.getenv('OPENAI_API_KEY'); print(repr(key))"

# Si vous voyez des espaces ou \n:
# 2. Nettoyer le .env
echo "OPENAI_API_KEY=sk-votre-cle-propre" > .env

# 3. Re-tester
python3 test_gpt.py
```

---

### ❌ Problème: "Insufficient quota"

**Cause:** Crédit OpenAI épuisé.

**Solution:**

1. Allez sur https://platform.openai.com/account/billing
2. Vérifiez votre crédit restant
3. Ajoutez du crédit si nécessaire ($5-10 suffisent)

---

### ❌ Problème: "JSON parse error"

**Cause:** GPT retourne un format invalide.

**Solutions:**

1. **Essayer gpt-4-turbo** (meilleur pour JSON):

```python
from extensions.gpt_intelligence import GPTDecisionEngine

engine = GPTDecisionEngine(model="gpt-4-turbo")
```

2. **Vérifier version openai:**

```bash
pip install --upgrade openai
```

3. **L'agent utilise automatiquement fallback** - pas de panique!

---

### ❌ Problème: "ModuleNotFoundError: No module named 'openai'"

**Solution:**

```bash
# Assurez-vous d'être dans le bon environnement
source .venv/bin/activate  # Si vous utilisez virtualenv

# Installer openai
pip install openai

# Vérifier
pip list | grep openai
```

---

## Coûts et Usage

### Estimation des Coûts GPT-4

**GPT-4 Pricing (Janvier 2025):**
- Input: ~$0.03 / 1K tokens
- Output: ~$0.06 / 1K tokens

**Par bataille (60-180s):**
- Input: ~500-1000 tokens
- Output: ~200-400 tokens
- **Coût: ~$0.02 - $0.05 par bataille**

**Budget recommandé:**
- 10 batailles: ~$0.50
- 100 batailles: ~$3-5
- Tournoi complet (3-5 batailles): ~$0.15

### Optimiser les Coûts

**1. Utiliser GPT-3.5-Turbo (moins cher):**

```python
engine = GPTDecisionEngine(model="gpt-3.5-turbo")  # ~10x moins cher
```

**2. Augmenter gpt_call_interval:**

```python
agent.gpt_call_interval = 10  # Moins d'appels = moins de coûts
```

**3. Mode fallback pour tests:**

```bash
# Ne définissez pas OPENAI_API_KEY pour tester gratuitement
unset OPENAI_API_KEY
python3 demo_gpt_tournament.py  # Utilisera fallback
```

---

## Sécurité de la Clé API

### ✅ BONNES PRATIQUES:

1. **Toujours utiliser `.env`** (jamais hardcoder dans le code)
2. **Ajouter `.env` au `.gitignore`**
3. **Ne JAMAIS commit une clé dans git**
4. **Révoquer les clés compromises immédiatement**

### ⚠️ Si Vous Avez Commit une Clé par Erreur:

```bash
# 1. Révoquer la clé immédiatement sur platform.openai.com
# 2. Générer une nouvelle clé
# 3. Retirer du git history (si public):
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

---

## Résumé Rapide

### Setup en 3 Minutes ⚡

```bash
# 1. Installer les dépendances
pip install openai python-dotenv

# 2. Créer .env avec votre clé
echo "OPENAI_API_KEY=sk-votre-cle-openai" > .env

# 3. Tester
python3 demo_gpt_personas.py
```

**C'est tout! Vos agents sont maintenant intelligents! 🧠**

---

## Support

### Problèmes Persistants?

1. Vérifiez les logs de l'application
2. Consultez la [documentation OpenAI](https://platform.openai.com/docs)
3. Vérifiez que votre compte OpenAI est actif
4. Essayez avec `gpt-3.5-turbo` (plus stable, moins cher)

### Demos Sans GPT

Tous les demos fonctionnent en **fallback mode** sans clé API:
- Logique rule-based basique
- Pas de coûts
- Bon pour tester le système

**Les agents GPT offrent:**
- Décisions vraiment intelligentes
- Comportements plus naturels et variés
- Adaptation au contexte de bataille
- Personnalités beaucoup plus riches

---

**Bon combat avec vos agents GPT! 🤖🎉**
