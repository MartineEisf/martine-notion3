"""
Client Notion pour Martine IA
Gère toutes les interactions avec l'API Notion
"""
import requests
import os
from typing import Dict, List, Optional
from datetime import datetime

class NotionClient:
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        self.base_url = "https://api.notion.com/v1"
    
    def query_database(self, database_id: str, filter_obj: Optional[Dict] = None) -> List[Dict]:
        """Récupère toutes les pages d'une database"""
        url = f"{self.base_url}/databases/{database_id}/query"
        all_results = []
        has_more = True
        start_cursor = None
        
        while has_more:
            payload = {"page_size": 100}
            if filter_obj:
                payload["filter"] = filter_obj
            if start_cursor:
                payload["start_cursor"] = start_cursor
            
            response = requests.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"❌ Erreur query DB {database_id}: {response.text}")
                break
            
            data = response.json()
            all_results.extend(data.get("results", []))
            has_more = data.get("has_more", False)
            start_cursor = data.get("next_cursor")
        
        return all_results
    
    def get_property_value(self, page: Dict, prop_name: str) -> any:
        """Extrait la valeur d'une propriété Notion (gère tous les types)"""
        props = page.get("properties", {})
        prop = props.get(prop_name, {})
        prop_type = prop.get("type")
        
        if not prop_type:
            return None
        
        # Title
        if prop_type == "title":
            titles = prop.get("title", [])
            return titles[0].get("plain_text", "") if titles else ""
        
        # Rich text
        if prop_type == "rich_text":
            texts = prop.get("rich_text", [])
            return texts[0].get("plain_text", "") if texts else ""
        
        # Number
        if prop_type == "number":
            return prop.get("number")
        
        # Select
        if prop_type == "select":
            select = prop.get("select")
            return select.get("name") if select else None
        
        # Multi-select
        if prop_type == "multi_select":
            return [item.get("name") for item in prop.get("multi_select", [])]
        
        # Date
        if prop_type == "date":
            date_obj = prop.get("date")
            return date_obj.get("start") if date_obj else None
        
        # Relation
        if prop_type == "relation":
            return [rel.get("id") for rel in prop.get("relation", [])]
        
        # Formula
        if prop_type == "formula":
            formula = prop.get("formula", {})
            formula_type = formula.get("type")
            return formula.get(formula_type) if formula_type else None
        
        # Rollup
        if prop_type == "rollup":
            rollup = prop.get("rollup", {})
            rollup_type = rollup.get("type")
            if rollup_type == "number":
                return rollup.get("number")
            elif rollup_type == "array":
                return rollup.get("array", [])
        
        return None
    
    def update_page(self, page_id: str, properties: Dict) -> bool:
        """Met à jour les propriétés d'une page"""
        url = f"{self.base_url}/pages/{page_id}"
        payload = {"properties": properties}
        
        response = requests.patch(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Erreur update page {page_id}: {response.text}")
            return False
        
        return True
    
    def create_page(self, database_id: str, properties: Dict) -> Optional[str]:
        """Crée une nouvelle page dans une database"""
        url = f"{self.base_url}/pages"
        payload = {
            "parent": {"database_id": database_id},
            "properties": properties
        }
        
        response = requests.post(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Erreur create page: {response.text}")
            return None
        
        return response.json().get("id")
    
    def get_database_schema(self, database_id: str) -> Dict:
        """Récupère le schéma d'une database (colonnes existantes)"""
        url = f"{self.base_url}/databases/{database_id}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            print(f"❌ Erreur get schema: {response.text}")
            return {}
        
        return response.json().get("properties", {})
    
    def add_property_to_database(self, database_id: str, prop_name: str, prop_config: Dict) -> bool:
        """Ajoute une colonne à une database"""
        url = f"{self.base_url}/databases/{database_id}"
        payload = {
            "properties": {
                prop_name: prop_config
            }
        }
        
        response = requests.patch(url, headers=self.headers, json=payload)
        
        if response.status_code != 200:
            print(f"❌ Erreur add property '{prop_name}': {response.text}")
            return False
        
        print(f"✅ Colonne '{prop_name}' ajoutée")
        return True