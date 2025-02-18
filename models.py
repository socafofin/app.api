import os
from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    keys = db.relationship('Key', backref='user')

    def __init__(self, username, password):
        self.username = username
        self.password = password  # Lembre-se de hashear a senha AQUI

class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    hwid = db.Column(db.String(255), nullable=True)
    expiration_time = db.Column(db.DateTime, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    @staticmethod
    def generate_key():
        return str(uuid.uuid4())