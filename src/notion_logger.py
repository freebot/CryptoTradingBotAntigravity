import requests
import os
from datetime import datetime

class NotionLogger:
    def __init__(self):
        self.token = os.getenv("NOTION_TOKEN")
        self.database_id = os.getenv("NOTION_DATABASE_ID")
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def log_trade(self, action, price, sentiment, confidence, profit):
        if not self.token or not self.database_id:
            print("❌ Error: Faltan NOTION_TOKEN o NOTION_DATABASE_ID")
            return
            
        url = "https://api.notion.com/v1/pages"
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Name": {"title": [{"text": {"content": f"Trade {action} @ {datetime.now().strftime('%Y-%m-%d %H:%M')}"}}]},
                "Fecha": {"date": {"start": datetime.now().isoformat()}},
                "Accion": {"select": {"name": action}},
                "Precio": {"number": float(price)},
                "Sentimiento": {"select": {"name": sentiment}},
                "Confianza ML": {"number": float(confidence)},
                "Profit Acumulado": {"number": float(profit)}
            }
        }
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            print("✅ ¡Registro publicado en Notion exitosamente!")
        else:
            print(f"❌ Error al publicar en Notion: {response.status_code}")
            try:
                print(f"Respuesta de Notion: {response.json()}")
            except:
                print(f"Respuesta de Notion: {response.text}")