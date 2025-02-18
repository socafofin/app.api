import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ***MUITO IMPORTANTE: Substitua esta URL pela sua URL de banco de dados REAL***
SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or 'postgresql://spoofer_db_user:2AEikVNcLBxCEkFU1152uSSzX4Nj7Na4@dpg-cuoi7s52ng1s73e9j6p0-a.frankfurt-postgres.render.com/spoofer_db'

app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configuração SSL para PostgreSQL (Render.com requer conexões seguras)
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "connect_args": {
        "sslmode": "require"
    }
}

db = SQLAlchemy(app)

class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    hwid = db.Column(db.String(255), nullable=True)
    expiration_time = db.Column(db.DateTime, nullable=False)