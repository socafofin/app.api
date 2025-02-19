from flask import Flask, request, jsonify
import secrets
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Nome do arquivo users.json
USERS_FILE = 'users.json'

# Função para carregar usuários do arquivo JSON
def carregar_usuarios():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {"admin": {"key": "admin_key", "hwid": None}}

# Função para salvar usuários no arquivo JSON
def salvar_usuarios(usuarios):
    with open(USERS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=4)

usuarios = carregar_usuarios()

# Função para gerar uma chave segura
def gerar_chave_acesso():
    return secrets.token_urlsafe(32)

@app.route('/generate_keys', methods=['POST'])
def generate_keys():
    quantidade = request.json.get('quantidade')
    tempo_expiracao = request.json.get('tempo_expiracao')

    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify({"success": False, "message": "Quantidade inválida."}), 400
    if not isinstance(tempo_expiracao, int) or tempo_expiracao <= 0:
        return jsonify({"success": False, "message": "Tempo de expiração inválido."}), 400

    chaves_geradas = []
    for _ in range(quantidade):
        chave = gerar_chave_acesso()
        usuarios[chave] = {"hwid": None}  # Inicializa com HWID None
        chaves_geradas.append(chave)
    salvar_usuarios(usuarios)
    return jsonify({"success": True, "message": f"{quantidade} chaves geradas.", "chaves": chaves_geradas})


@app.route('/login', methods=['POST'])
def login():
    chave_acesso = request.json.get('key')
    hwid = request.json.get('hwid')

    if not chave_acesso or not hwid:
        return jsonify({"success": False, "message": "Chave de acesso e HWID são necessários."}), 400

    if chave_acesso == usuarios["admin"]["key"]:
        return jsonify({"success": True, "message": "Login de admin bem-sucedido!", "usuario": "socafofoh"})

    if chave_acesso in usuarios:
        if usuarios[chave_acesso]["hwid"] is None:
            usuarios[chave_acesso]["hwid"] = hwid
            salvar_usuarios(usuarios)
            return jsonify({"success": True, "message": "Login bem-sucedido e HWID registrado!", "usuario": "user_standard"})
        elif usuarios[chave_acesso]["hwid"] == hwid:
            return jsonify({"success": True, "message": "Login bem-sucedido!", "usuario": "user_standard"})
        else:
            return jsonify({"success": False, "message": "Chave já registrada para outro computador."}), 401
    else:
        return jsonify({"success": False, "message": "Chave de acesso inválida."}), 401

if __name__ == '__main__':
    app.run(debug=True)