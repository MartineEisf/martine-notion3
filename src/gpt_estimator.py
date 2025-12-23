"""
Estimateur de temps via GPT (OpenAI)
Utilise l'historique + description pour prédire les durées
"""
import requests
import json
import re
from typing import Dict, List, Optional

class GPTEstimator:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
    
    def estimate_task_time(
        self, 
        task_name: str,
        task_description: str,
        project_context: str,
        historical_tasks: List[Dict],
        task_content: str = ""
    ) -> Optional[float]:
        """
        Estime le temps nécessaire pour une tâche
        Returns: temps en minutes (float) ou None si erreur
        """
        
        # Construire le contexte historique
        history_str = self._format_history(historical_tasks)
        
        # Prompt pour GPT
        system_prompt = "Tu es un assistant de gestion de projet expert en estimation de temps."
        user_prompt = f"""CONTEXTE DU PROJET:
{project_context}

HISTORIQUE DES TÂCHES SIMILAIRES:
{history_str}

TÂCHE À ESTIMER:
Nom: {task_name}
Description: {task_description}

CONTENU DÉTAILLÉ DE LA TÂCHE (Page Notion):
{task_content if task_content else "Aucun contenu détaillé disponible."}

INSTRUCTIONS:
1. Analyse l'historique des tâches similaires
2. Prends en compte la complexité décrite dans la description ET le contenu détaillé
3. Estime le temps nécessaire de manière RÉALISTE (les humains sous-estiment souvent)
4. Réponds UNIQUEMENT avec un nombre entier de minutes (ex: 120 pour 2h)
5. Ne réponds QUE le nombre, rien d'autre. Pas de texte avant ni après.

ESTIMATION EN MINUTES:"""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 50
                },
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Erreur GPT API ({response.status_code}): {response.text}")
                return None
            
            result = response.json()
            text = result["choices"][0]["message"]["content"].strip()
            
            # Extraire le nombre
            match = re.search(r'\d+', text)
            if match:
                minutes = float(match.group())
                return minutes
            else:
                print(f"⚠️ Réponse GPT non parsable: {text}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur estimation: {e}")
            return None
    
    def _format_history(self, tasks: List[Dict]) -> str:
        """Formate l'historique pour le prompt"""
        if not tasks:
            return "Aucune tâche similaire trouvée dans l'historique."
        
        lines = []
        for task in tasks[:10]:  # Limiter à 10 tâches max
            nom = task.get("nom", "Sans nom")
            temps = task.get("temps_reel", 0)
            desc = task.get("description", "")[:100]  # Tronquer
            lines.append(f"- {nom}: {temps} min ('{desc}')")
        
        return "\n".join(lines)
    
    def batch_estimate(
        self,
        tasks_to_estimate: List[Dict],
        all_tasks_history: List[Dict],
        project_name: str = "Projet EISF"
    ) -> Dict[str, float]:
        """
        Estime plusieurs tâches en batch
        Returns: Dict[task_id -> estimated_minutes]
        """
        estimates = {}
        
        for i, task in enumerate(tasks_to_estimate, 1):
            task_id = task.get("id")
            task_name = task.get("nom", "Tâche sans nom")
            task_desc = task.get("description", "")
            task_content = task.get("content", "")
            
            print(f"🤖 Estimation {i}/{len(tasks_to_estimate)}: {task_name}")
            
            # Filtrer l'historique (tâches similaires du même projet)
            similar_tasks = [
                t for t in all_tasks_history
                if t.get("projet") == task.get("projet") and t.get("temps_reel", 0) > 0
            ]
            
            estimated_time = self.estimate_task_time(
                task_name=task_name,
                task_description=task_desc,
                project_context=f"Projet: {project_name}",
                historical_tasks=similar_tasks,
                task_content=task_content
            )
            
            if estimated_time:
                estimates[task_id] = estimated_time
                print(f"  ✅ {estimated_time} min estimées")
            else:
                print(f"  ⚠️ Échec estimation")
        
        return estimates
