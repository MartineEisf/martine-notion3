"""
MARTINE IA - Script Principal
Lit Notion, estime via Gemini, met à jour les temps
"""
import os
import sys
import json
from datetime import datetime

# Forcer l'encodage UTF-8 pour Windows (pour les émojis)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
# Cherche d'abord dans le dossier parent (racine du projet)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
load_dotenv(env_path, override=True)

# Ajouter le dossier courant au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from notion_client import NotionClient
from gpt_estimator import GPTEstimator

# Configuration depuis variables d'environnement (.env)
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DB_PROJETS = os.getenv("DATABASE_PROJETS")
DB_TACHES = os.getenv("DATABASE_TACHES")
DB_SAISIES = os.getenv("DATABASE_SAISIES_TEMPS")
GPT_KEY = os.getenv("GPT_API_KEY")
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")

# Vérifier que les variables essentielles sont définies
if not NOTION_TOKEN:
    raise ValueError("❌ NOTION_TOKEN manquant dans le fichier .env")
if not GPT_KEY:
    raise ValueError("❌ GPT_API_KEY manquant dans le fichier .env")

# Initialiser clients
notion = NotionClient(NOTION_TOKEN)
gpt = GPTEstimator(GPT_KEY, GPT_MODEL)

def setup_columns():
    """Ajoute les colonnes manquantes si nécessaire"""
    print("\n🔧 Vérification des colonnes...")
    
    # Colonnes à ajouter dans Tâches
    taches_schema = notion.get_database_schema(DB_TACHES)
    
    if "⏱️ Temps estimé IA (min)" not in taches_schema:
        notion.add_property_to_database(
            DB_TACHES,
            "⏱️ Temps estimé IA (min)",
            {"number": {"format": "number"}}
        )
    
    if "⏱️ Temps réel agrégé (min)" not in taches_schema:
        notion.add_property_to_database(
            DB_TACHES,
            "⏱️ Temps réel agrégé (min)",
            {"number": {"format": "number"}}
        )
    
    if "📊 Écart (%)" not in taches_schema:
        notion.add_property_to_database(
            DB_TACHES,
            "📊 Écart (%)",
            {"number": {"format": "percent"}}
        )
    
    print("✅ Colonnes prêtes")

def aggregate_real_times():
    """Agrège les temps réels depuis les saisies temps"""
    print("\nℹ️ Agrégation des temps réels DÉSACTIVÉE (car bases différentes)")
    return {}

def get_tasks_to_estimate():
    """Récupère les tâches sans estimation IA"""
    print("\n🔍 Recherche des tâches à estimer...")
    
    # Filtrer : pas encore d'estimation IA ET statut != "Terminé"
    taches = notion.query_database(DB_TACHES)
    to_estimate = []
    for tache in taches:
        statut = notion.get_property_value(tache, "Statut")
        temps_estime = notion.get_property_value(tache, "⏱️ Temps estimé IA (min)")
        
        # Filtres utilisateur :
        # - Exclure : "Infos", "Backlog", "Plateforme"
        # - Inclure : "Terminé", "Abandonné", "Archives" (et les autres comme "À faire", "En cours")
        excluded_status = ["Infos", "Backlog", "Plateforme"]
        
        if statut not in excluded_status and (temps_estime is None or temps_estime == 0):
            # Récupérer le contenu détaillé de la page
            print(f"   📄 Lecture du contenu pour : {notion.get_property_value(tache, 'Nom')}")
            content = notion.get_page_content(tache["id"])
            
            to_estimate.append({
                "id": tache["id"],
                "nom": notion.get_property_value(tache, "Nom"),
                "description": notion.get_property_value(tache, "Description") or "",
                "projet": notion.get_property_value(tache, "Projet/Tlt") or [],
                "content": content
            })
    
    print(f"📝 {len(to_estimate)} tâches à estimer")
    return to_estimate

def get_historical_tasks():
    """Récupère l'historique des tâches terminées avec temps réel"""
    print("\n📚 Chargement de l'historique...")
    
    taches = notion.query_database(DB_TACHES)
    
    history = []
    for tache in taches:
        temps_reel = notion.get_property_value(tache, "⏱️ Temps réel agrégé (min)")
        statut = notion.get_property_value(tache, "Statut")
        
        if temps_reel and temps_reel > 0:
            history.append({
                "id": tache["id"],
                "nom": notion.get_property_value(tache, "Nom"),
                "description": notion.get_property_value(tache, "Description") or "",
                "temps_reel": temps_reel,
                "projet": notion.get_property_value(tache, "Projet/Tlt") or [],
                "statut": statut
            })
    
    print(f"📊 {len(history)} tâches historiques chargées")
    return history

def run_estimations():
    """Lance les estimations IA"""
    print("\n🤖 Lancement des estimations GPT...")
    
    tasks_to_estimate = get_tasks_to_estimate()
    if not tasks_to_estimate:
        print("✅ Toutes les tâches sont déjà estimées")
        return
    
    historical_tasks = get_historical_tasks()
    
    # Batch estimation
    estimates = gpt.batch_estimate(
        tasks_to_estimate=tasks_to_estimate,
        all_tasks_history=historical_tasks,
        project_name="EISF Alternance"
    )
    
    # Mettre à jour Notion
    print("\n💾 Mise à jour Notion...")
    updated = 0
    for task_id, estimated_minutes in estimates.items():
        success = notion.update_page(task_id, {
            "⏱️ Temps estimé IA (min)": {"number": estimated_minutes}
        })
        if success:
            updated += 1
    
    print(f"✅ {updated}/{len(estimates)} estimations enregistrées")
    
    # Sauvegarder log
    log_path = f"logs/estimations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(estimates, f, indent=2, ensure_ascii=False)
    print(f"📝 Log sauvegardé: {log_path}")

def calculate_deviations():
    """Calcule les écarts estimé vs réel"""
    print("\n📊 Calcul des écarts...")
    
    taches = notion.query_database(DB_TACHES)
    
    updated = 0
    for tache in taches:
        estime = notion.get_property_value(tache, "⏱️ Temps estimé IA (min)")
        reel = notion.get_property_value(tache, "⏱️ Temps réel agrégé (min)")
        
        if estime and reel and estime > 0:
            ecart_pourcent = ((reel - estime) / estime)
            
            success = notion.update_page(tache["id"], {
                "📊 Écart (%)": {"number": ecart_pourcent}
            })
            if success:
                updated += 1
    
    print(f"✅ {updated} écarts calculés")

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🧠 MARTINE IA - Estimation automatique des temps")
    print("=" * 60)
    
    try:
        # 1. Setup colonnes
        # setup_columns() # Desactivé temporairement
        
        # 2. Agréger temps réels
        # aggregate_real_times() # Desactivé car bases différentes
        
        # 3. Estimer via IA
        run_estimations()
        
        # 4. Calculer écarts
        # calculate_deviations() # Desactivé
        
        print("\n" + "=" * 60)
        print("✅ TRAITEMENT TERMINÉ")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()