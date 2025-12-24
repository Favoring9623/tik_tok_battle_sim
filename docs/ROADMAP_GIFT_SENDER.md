# Roadmap: TikTok Gift Sender Platform

## Vision
Plateforme complète d'envoi automatisé de cadeaux TikTok avec interface web, planification intelligente et modèle d'abonnement.

---

## Phase 1: Fondations (Core)
**Objectif**: Stabiliser et étendre les fonctionnalités de base

### 1.1 Multi-Cadeaux
- [ ] Catalogue de tous les cadeaux TikTok (nom, prix, position)
- [ ] Détection automatique des cadeaux disponibles sur un live
- [ ] Script générique `send_gift.py --gift "Rose" --qty 100`
- [ ] Support cadeaux barre principale + panneau "More"

### 1.2 Session Persistante
- [ ] Mode daemon: navigateur reste ouvert entre envois
- [ ] API locale (Flask/FastAPI) pour contrôler le navigateur
- [ ] Reconnexion automatique si déconnecté
- [ ] File d'attente des envois (queue system)

### 1.3 Robustesse
- [ ] Gestion des erreurs (stream offline, cadeau indisponible)
- [ ] Retry automatique avec backoff exponentiel
- [ ] Logging complet (fichier + console)
- [ ] Tests unitaires et d'intégration

**Livrables Phase 1**:
- `core/gift_sender_daemon.py` - Service persistant
- `core/gift_catalog.py` - Catalogue des cadeaux
- `api/gift_api.py` - API REST locale

---

## Phase 2: Interface Web
**Objectif**: Dashboard utilisateur pour contrôle visuel

### 2.1 Backend API
- [ ] Endpoints REST:
  - `POST /api/send` - Envoyer des cadeaux
  - `GET /api/status` - État du sender
  - `GET /api/balance` - Solde coins
  - `GET /api/streams` - Streams favoris
  - `POST /api/stop` - Arrêter envoi en cours
- [ ] WebSocket pour progression temps réel
- [ ] Authentification utilisateur (JWT)

### 2.2 Frontend Dashboard
- [ ] Page principale:
  - Input: @username du streamer
  - Dropdown: sélection cadeau
  - Slider: quantité (1 - 10,000)
  - Slider: vitesse CPS (1 - 12)
  - Bouton: Envoyer / Arrêter
- [ ] Barre de progression en temps réel
- [ ] Historique des envois
- [ ] Affichage solde coins

### 2.3 UX/UI
- [ ] Design dark mode (style TikTok)
- [ ] Notifications toast (succès/erreur)
- [ ] Responsive (mobile-friendly)
- [ ] Raccourcis clavier

**Livrables Phase 2**:
- `web/backend/gift_api.py` - API complète
- `web/frontend/public/gift-sender.html` - Dashboard
- `web/frontend/public/css/gift-sender.css` - Styles

---

## Phase 3: Intelligence & Stratégie
**Objectif**: Optimisation automatique des envois

### 3.1 Détection Multiplicateurs
- [ ] Lire le multiplicateur actif (x1, x2, x5, x6)
- [ ] Détecter Bonus Hour automatiquement
- [ ] Détecter Double Blast
- [ ] API: `GET /api/multiplier/@username`

### 3.2 Stratégies d'Envoi
- [ ] Mode "Économie": petits cadeaux uniquement
- [ ] Mode "Points Max": gros cadeaux pendant multiplicateurs
- [ ] Mode "Battle": réponse aux adversaires
- [ ] Mode "Qualification": atteindre X points minimum

### 3.3 Monitoring Balance
- [ ] Lecture solde en temps réel
- [ ] Alerte seuil bas (configurable)
- [ ] Arrêt automatique si solde insuffisant
- [ ] Estimation coût avant envoi

### 3.4 Analytics
- [ ] Dashboard statistiques:
  - Total cadeaux envoyés (jour/semaine/mois)
  - Coins dépensés
  - Points générés
  - Streamers supportés
- [ ] Export CSV/JSON

**Livrables Phase 3**:
- `core/multiplier_detector.py` - Détection multiplicateurs
- `core/send_strategies.py` - Stratégies d'envoi
- `core/balance_monitor.py` - Surveillance solde
- `web/frontend/public/analytics.html` - Dashboard stats

---

## Phase 4: Planification (Scheduler)
**Objectif**: Envois programmés et automatisés

### 4.1 Scheduler Core
- [ ] Planifier envoi à heure précise
- [ ] Envois récurrents (quotidien, hebdomadaire)
- [ ] Conditions de déclenchement:
  - Heure spécifique
  - Multiplicateur actif
  - Streamer en live
- [ ] Persistance des tâches (SQLite)

### 4.2 Presets Bonus Hour
- [ ] Preset "Live Fest Bonus Hour":
  - Déclenche à 02:00 Paris (x6)
  - Envoie X Fest Pop automatiquement
- [ ] Preset "Double Blast":
  - Détecte activation
  - Envoie cadeaux programmés

### 4.3 Interface Scheduler
- [ ] Calendrier visuel des envois planifiés
- [ ] Création/modification/suppression de tâches
- [ ] Notifications avant exécution
- [ ] Historique des exécutions

**Livrables Phase 4**:
- `core/scheduler.py` - Moteur de planification
- `core/presets.py` - Presets prédéfinis
- `web/frontend/public/scheduler.html` - Interface planning

---

## Phase 5: Multi-Comptes & Collaboration
**Objectif**: Support équipes et agences

### 5.1 Multi-Comptes TikTok
- [ ] Gestion plusieurs sessions TikTok
- [ ] Switch entre comptes
- [ ] Envois parallèles depuis plusieurs comptes
- [ ] Isolation des sessions (cookies séparés)

### 5.2 Gestion Équipe
- [ ] Rôles: Admin, Manager, Sender
- [ ] Permissions par rôle
- [ ] Audit log des actions
- [ ] Quotas par utilisateur

### 5.3 API Publique
- [ ] Documentation OpenAPI/Swagger
- [ ] Rate limiting
- [ ] Webhooks (notifications événements)
- [ ] SDK Python/JavaScript

**Livrables Phase 5**:
- `core/multi_account.py` - Gestion multi-comptes
- `core/team_manager.py` - Gestion équipe
- `api/public_api.py` - API publique
- `docs/API.md` - Documentation

---

## Phase 6: Monétisation
**Objectif**: Modèle économique viable

### 6.1 Système d'Abonnements
```
┌─────────────┬─────────┬─────────────┬──────────────┐
│ Tier        │ Prix    │ Clics/mois  │ Features     │
├─────────────┼─────────┼─────────────┼──────────────┤
│ Free        │ 0€      │ 100         │ Basic        │
│ Basic       │ 9.99€   │ 10,000      │ + Scheduler  │
│ Premium     │ 29.99€  │ 100,000     │ + Analytics  │
│ Unlimited   │ 99.99€  │ Illimité    │ + API + Team │
│ Enterprise  │ Custom  │ Illimité    │ + Support    │
└─────────────┴─────────┴─────────────┴──────────────┘
```

### 6.2 Paiements
- [ ] Intégration Stripe
- [ ] Gestion abonnements (upgrade/downgrade)
- [ ] Factures automatiques
- [ ] Période d'essai (7 jours Premium)

### 6.3 Packs de Clics
- [ ] Achat one-time (pas d'abonnement)
- [ ] Packs: 1K, 5K, 10K, 50K clics
- [ ] Pas d'expiration

**Livrables Phase 6**:
- `core/subscription.py` - Gestion abonnements
- `api/stripe_webhooks.py` - Intégration paiement
- `web/frontend/public/pricing.html` - Page tarifs
- `web/frontend/public/billing.html` - Gestion compte

---

## Phase 7: Mobile & Extensions
**Objectif**: Accessibilité maximale

### 7.1 Application Mobile (PWA)
- [ ] Progressive Web App
- [ ] Notifications push
- [ ] Mode hors-ligne (queue)
- [ ] Installation home screen

### 7.2 Extension Navigateur
- [ ] Chrome/Firefox extension
- [ ] Overlay sur TikTok.com
- [ ] Bouton quick-send
- [ ] Raccourcis personnalisables

### 7.3 Bot Telegram/Discord
- [ ] Commandes: `/send @user 100 "Fest Pop"`
- [ ] Notifications envois
- [ ] Status en temps réel

**Livrables Phase 7**:
- PWA mobile
- Extension Chrome/Firefox
- Bot Telegram
- Bot Discord

---

## Priorités & Timeline

```
Phase 1 ████████████░░░░░░░░ Fondations     [PRIORITÉ HAUTE]
Phase 2 ████████░░░░░░░░░░░░ Interface Web  [PRIORITÉ HAUTE]
Phase 3 ██████░░░░░░░░░░░░░░ Intelligence   [PRIORITÉ MOYENNE]
Phase 4 ██████░░░░░░░░░░░░░░ Scheduler      [PRIORITÉ MOYENNE]
Phase 5 ████░░░░░░░░░░░░░░░░ Multi-Comptes  [PRIORITÉ BASSE]
Phase 6 ████░░░░░░░░░░░░░░░░ Monétisation   [PRIORITÉ BASSE]
Phase 7 ██░░░░░░░░░░░░░░░░░░ Mobile/Ext     [FUTURE]
```

---

## Stack Technique

| Composant | Technologie |
|-----------|-------------|
| Automation | Playwright (Python) |
| Backend API | FastAPI |
| Frontend | HTML/CSS/JS (Vanilla) |
| Database | SQLite → PostgreSQL |
| Queue | Redis (optionnel) |
| Scheduler | APScheduler |
| Paiements | Stripe |
| Auth | JWT + bcrypt |

---

## Métriques de Succès

### Phase 1-2 (MVP)
- [ ] 1000 cadeaux envoyés sans erreur
- [ ] Interface web fonctionnelle
- [ ] 10 utilisateurs beta

### Phase 3-4 (Product)
- [ ] Détection multiplicateurs 95% fiable
- [ ] 50 utilisateurs actifs
- [ ] 100K cadeaux/mois

### Phase 5-6 (Business)
- [ ] 10 clients payants
- [ ] MRR > 500€
- [ ] Churn < 5%

---

## Risques & Mitigation

| Risque | Impact | Mitigation |
|--------|--------|------------|
| TikTok change l'UI | Haut | Sélecteurs flexibles, tests réguliers |
| Détection bot | Haut | Délais aléatoires, comportement humain |
| Rate limiting | Moyen | Respecter limites, backoff |
| Ban compte | Haut | Multi-comptes, avertissements |

---

## Prochaines Étapes

1. **Immédiat**: Finaliser Phase 1.1 (Multi-Cadeaux)
2. **Cette semaine**: Phase 1.2 (Session Persistante)
3. **Prochaine semaine**: Phase 2.1-2.2 (Interface Web)

---

*Dernière mise à jour: Décembre 2024*
