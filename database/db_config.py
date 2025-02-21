import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.DATABASE_URL = os.getenv("DATABASE_URL")
        return cls._instance
    
    def get_connection(self):
        try:
            conn = psycopg2.connect(self.DATABASE_URL)
            return conn
        except Exception as e:
            print(f"Erro ao conectar ao banco: {e}")
            return None

# Instância global
db = Database()
get_connection = db.get_connection