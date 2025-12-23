# 📚 Guide Utilisateur - Martine IA

Guide complet d'utilisation de Martine IA pour l'estimation automatique des temps.

## Table des Matières

1. [Installation](#installation)
2. [Configuration](#configuration)
3. [Utilisation Quotidienne](#utilisation-quotidienne)
4. [Fonctionnalités Avancées](#fonctionnalités-avancées)
5. [Automatisation](#automatisation)
6. [Résolution de Problèmes](#résolution-de-problèmes)

---

## 📦 Installation

### 1. Prérequis

- **Python 3.8 ou supérieur**
  - Vérifiez : `python --version`
  - Téléchargez sur [python.org](https://www.python.org/downloads/)

- **Compte Notion**
  - Créez une intégration sur [notion.so/my-integrations](https://www.notion.so/my-integrations)
  - Notez votre token d'intégration

- **Clé API OpenAI**
  - Créez une clé sur [platform.openai.com](https://platform.openai.com/api-keys)

### 2. Installation des Dépendances

```bash
cd martine-notion3
pip install -r requirements.txt
```

---

## ⚙️ Configuration

### 1. Fichier `.env`

Créez un fichier `.env` à la racine du projet :

```env
# Notion API
NOTION_TOKEN=ntn_votre_token_ici
DATABASE_TACHES=id_de_votre_base

# GPT API
GPT_API_KEY=sk-votre_cle_openai
GPT_MODEL=gpt-4o
```

### 2. Configuration Notion

#### a) Partager votre base avec l'intégration

1. Ouvrez votre base Tâches dans Notion
2. Cliquez sur `•••` (en haut à droite)
3. Sélectionnez `Connexions` → `Ajouter une connexion`
4. Choisissez votre intégration

#### b) Récupérer l'ID de la base

L'URL de votre base ressemble à :
```
https://notion.so/workspace/29a59135c882804c9a49e74c9d45562f?v=...
                          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                          C'est l'ID de votre base
```

### 3. Colonnes Notion

Le script crée automatiquement ces colonnes :

| Colonne | Type | Description |
|---------|------|-------------|
| `⏱️ Temps estimé IA (min)` | Number | Estimation en minutes |
| `⏱️ Temps réel agrégé (min)` | Number | Temps réel passé |
| `📊 Écart (%)` | Percent | Différence estimé/réel |
| `🔄 Hash contenu` | Text | Détection des changements |

---

## 🎯 Utilisation Quotidienne

### Lancement Simple

```bash
python src/main.py
```

### Ce que fait le script

1. **Vérification** : Crée les colonnes si nécessaire
2. **Lecture** : Récupère toutes vos tâches Notion
3. **Filtrage** : Exclut les statuts "Infos", "Backlog", "Plateforme"
4. **Estimation** :
   - Nouvelles tâches → estimation
   - Contenu modifié → ré-estimation automatique
5. **Sauvegarde** : Écrit dans Notion + log JSON

### Sortie Console

```
============================================================
🧠 MARTINE IA - Estimation automatique des temps
============================================================

🔧 Vérification des colonnes...
✅ Colonnes prêtes

🔍 Recherche des tâches à estimer...
   📄 Créer documentation (nouvelle)
   📄 Refactoring API (contenu modifié)
📝 2 tâches à estimer (1 ré-estimation)

📚 Chargement de l'historique...
📊 15 tâches historiques chargées

🤖 Lancement des estimations GPT...
🤖 Estimation 1/2: Créer documentation
  ✅ 120.0 min estimées
🤖 Estimation 2/2: Refactoring API
  ✅ 240.0 min estimées

💾 Mise à jour Notion...
✅ 2/2 estimations enregistrées
📝 Log sauvegardé: logs/estimations_20251223_143000.json

============================================================
✅ TRAITEMENT TERMINÉ
============================================================
```

---

## 🚀 Fonctionnalités Avancées

### Ré-estimation Automatique

Le système détecte automatiquement les changements :

1. **Calcul du hash** : Empreinte MD5 de `nom + description + contenu`
2. **Comparaison** : Hash actuel vs hash stocké
3. **Action** : Si différent → ré-estimation automatique

**Exemple :**
```
Jour 1 : Tâche "API REST" → estimée à 180 min
Jour 2 : Vous ajoutez des détails dans la description
Jour 3 : Script détecte le changement → ré-estime à 240 min
```

### Filtrage des Statuts

Par défaut, le script **exclut** :
- `Infos`
- `Backlog`
- `Plateforme`

Pour modifier, éditez `src/main.py` ligne 95 :
```python
excluded_status = ["Infos", "Backlog", "Plateforme"]
```

### Logs JSON

Chaque exécution crée un log :
```
logs/estimations_20251223_143000.json
```

Contenu :
```json
{
  "29a59135-c882-8024-84e7-d27fb886feb2": 120.0,
  "29a59135-c882-8029-97db-f3b2af48f46f": 240.0
}
```

---

## ⏰ Automatisation

### Windows - Planificateur de Tâches

#### 1. Créer un fichier batch

`run_martine.bat` :
```batch
@echo off
cd /d "C:\Users\[VOTRE_NOM]\Desktop\OUTILS\martine-notion3"
python src/main.py
pause
```

#### 2. Planifier l'exécution

1. Ouvrez `Planificateur de tâches`
2. `Créer une tâche de base`
3. **Nom** : "Martine IA - Estimation quotidienne"
4. **Déclencheur** : Tous les jours à 8h00
5. **Action** : Démarrer un programme → `run_martine.bat`

### macOS/Linux - Cron

Ajoutez à votre crontab (`crontab -e`) :
```bash
0 8 * * * cd /path/to/martine-notion3 && python src/main.py
```

---

## 🆘 Résolution de Problèmes

### Erreur : "API token is invalid"

**Cause** : Token Notion incorrect ou expiré

**Solution** :
1. Vérifiez votre `.env`
2. Régénérez le token sur [notion.so/my-integrations](https://www.notion.so/my-integrations)
3. Partagez la base avec l'intégration

### Erreur : "property does not exist"

**Cause** : Colonnes manquantes dans Notion

**Solution** :
1. Vérifiez que `setup_columns()` n'est pas commenté (ligne 204 de `main.py`)
2. Relancez le script

### Erreur : Quota GPT épuisé

**Cause** : Limite gratuite atteinte

**Solution** :
1. Attendez le rechargement du quota (minuit heure US)
2. Passez à un plan payant OpenAI
3. Changez de modèle dans `.env` : `GPT_MODEL=gpt-3.5-turbo`

### Encodage UTF-8 (Windows)

**Symptôme** : Erreurs avec les émojis

**Solution** : Déjà corrigé dans `main.py` (ligne 11-12)
```python
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
```

### Aucune tâche à estimer

**Causes possibles** :
1. Toutes les tâches ont déjà une estimation
2. Statuts exclus ("Infos", "Backlog", "Plateforme")

**Solution** :
- Effacez `⏱️ Temps estimé IA (min)` pour forcer une ré-estimation
- Vérifiez les statuts de vos tâches

---

## 📊 Bonnes Pratiques

### 1. Descriptions Détaillées

Plus la description est précise, meilleure est l'estimation :

❌ **Mauvais** : "Faire API"
✅ **Bon** : "Créer endpoint REST /users avec authentification JWT et validation des données"

### 2. Utiliser le Contenu de Page

Ajoutez des détails dans le contenu de la page Notion :
- Sous-tâches
- Contraintes techniques
- Dépendances

### 3. Vérifier les Estimations

Comparez régulièrement `⏱️ Temps estimé IA` vs `⏱️ Temps réel` pour améliorer la précision.

### 4. Historique

Le système apprend de vos tâches passées. Plus vous avez de tâches avec temps réel, meilleures sont les estimations.

---

## 🔄 Workflow Recommandé

```
1. Créer tâche dans Notion
   ↓
2. Ajouter description détaillée
   ↓
3. Lancer python src/main.py
   ↓
4. Vérifier estimation dans Notion
   ↓
5. Travailler sur la tâche
   ↓
6. Saisir temps réel
   ↓
7. Comparer avec estimation (colonne Écart %)
```

---

## 📞 Support

- **Issues GitHub** : Pour bugs et suggestions
- **Documentation** : Ce guide + README.md
- **Logs** : Consultez `logs/` pour le débogage

---

## 🎓 Exemples d'Utilisation

### Exemple 1 : Nouvelle Tâche

```
Tâche Notion :
- Nom : "Implémenter système de cache Redis"
- Description : "Ajouter cache Redis pour les requêtes API fréquentes"
- Statut : "À faire"

Résultat :
⏱️ Temps estimé IA (min) : 180
```

### Exemple 2 : Modification de Contenu

```
Jour 1 :
- Tâche : "Créer dashboard"
- Estimation : 120 min

Jour 2 :
- Vous ajoutez : "Avec graphiques temps réel et export PDF"
- Script détecte changement
- Nouvelle estimation : 240 min
```

### Exemple 3 : Forcer Ré-estimation

```
1. Dans Notion, effacez la valeur de "⏱️ Temps estimé IA (min)"
2. Lancez python src/main.py
3. La tâche est ré-estimée
```

---

**Version** : 1.0  
**Dernière mise à jour** : 23 décembre 2024
