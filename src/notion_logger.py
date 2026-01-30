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
        url = "https://api.notion.com/v1/pages"
        data = {
            "parent": {"database_id": self.database_id},
            "properties": {
                "Fecha": {"date": {"start": datetime.now().isoformat()}},
                "Accion": {"select": {"name": action}},
                "Precio": {"number": float(price)},
                "Sentimiento": {"select": {"name": sentiment.upper()}},
                "Confianza ML": {"number": float(confidence)},
                "Profit Acumulado": {"number": float(profit)}
            }
        }
        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code == 200:
            print("✅ Dashboard de Notion actualizado.")
        else:
            print(f"❌ Error Notion: {response.text}")