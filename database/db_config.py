import os
import psycopg2
from dotenv import load_dotenv
import logging

load_dotenv()

DB_CONFIG = {
    'host': 'dpg-cuoi7s52ng1s73e9j6p0-a.singapore-postgres.render.com',
    'database': 'spoofer_db',
    'user': 'spoofer_db_user',
    'password': '2c9cad1e831b9de3941b2a96a4df85f92b98',
    'port': '5432'
}

class Database:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Construa a URL corretamente
            cls._instance.DATABASE_URL = (
                f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
                f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
                f"/{DB_CONFIG['database']}?sslmode=require"
            )
        return cls._instance
    
    def get_connection(self):
        try:
            conn = psycopg2.connect(
                self.DATABASE_URL,
                connect_timeout=10,
                keepalives=1,
                keepalives_idle=30,
                keepalives_interval=10,
                keepalives_count=5
            )
            return conn
        except Exception as e:
            logging.error(f"Erro de conexão: {e}")
            return None

    def test_key_table(self):
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            # Corrigido para usar a tabela security_keys ao invés de keys
            cur.execute("SELECT * FROM security_keys LIMIT 1")
            result = cur.fetchone()
            print("Conexão com tabela security_keys OK!")
            cur.close()
            conn.close()
            return True
        except Exception as e:
            print(f"Erro ao testar tabela security_keys: {e}")
            return False

    def init_tables(self):
        """Inicializa as tabelas necessárias"""
        try:
            conn = self.get_connection()
            if not conn:
                return False
                
            cur = conn.cursor()
            
            # Cria tabela security_keys se não existir
            cur.execute("""
                CREATE TABLE IF NOT EXISTS security_keys (
                    id SERIAL PRIMARY KEY,
                    secret_key BYTEA NOT NULL,
                    encryption_key BYTEA NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_security_keys_created_at 
                ON security_keys(created_at);
            """)
            
            conn.commit()
            cur.close()
            conn.close()
            print("Tabelas inicializadas com sucesso!")
            return True
        except Exception as e:
            print(f"Erro ao inicializar tabelas: {e}")
            return False

# Instância global
db = Database()
get_connection = db.get_connection

# Teste completo
if __name__ == "__main__":
    db.init_tables()  # Cria as tabelas se não existirem
    db.test_key_table()