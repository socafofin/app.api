from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, timedelta
import secrets

app = Flask(__name__)

# Configuração do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://spoofer_db_user:2AEikVNcLBxCEkFU1152uSSzX4Nj7Na4@dpg-cuoi7s52ng1s73e9j6p0-a/spoofer_db'
db = SQLAlchemy(app)

# Modelo para armazenar as chaves e HWIDs
class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    hwid = db.Column(db.String(200), nullable=False)
    expiration_time = db.Column(db.DateTime, nullable=False)  # Nova coluna para expiração

# Rota raiz (/) para testes
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Servidor está funcionando!"}), 200

# Rota para gerar uma nova chave com data de expiração
@app.route('/gerar_chave', methods=['POST'])
def gerar_chave():
    data = request.json
    expiration_date = data.get('expiration_date')  # Data de expiração fornecida pelo cliente
    duration_days = data.get('duration_days', None)  # Alternativa: duração em dias

    if not expiration_date and not duration_days:
        return jsonify({'success': False, 'message': 'Você deve fornecer uma data de expiração ou duração em dias.'})

    # Gerar uma nova chave aleatória
    new_key = secrets.token_hex(8).upper()

    # Calcular a data de expiração
    if expiration_date:
        try:
            expiration_time = datetime.fromisoformat(expiration_date)  # Converte string ISO para datetime
        except ValueError:
            return jsonify({'success': False, 'message': 'Formato de data inválido. Use ISO 8601 (ex.: 2023-12-31T23:59:59).'})
    else:
        expiration_time = datetime.now() + timedelta(days=duration_days)

    # Salvar a chave no banco de dados
    new_key_record = Key(key=new_key, hwid="", expiration_time=expiration_time)
    db.session.add(new_key_record)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Chave gerada com sucesso!',
        'key': new_key,
        'expiration_time': expiration_time.strftime('%d/%m/%Y %H:%M:%S')
    })

# Rota para ativar uma chave
@app.route('/ativar', methods=['POST'])
def ativar():
    try:
        # Verifica se o cabeçalho Content-Type é application/json
        if not request.is_json:
            return jsonify({"erro": "Formato inválido. Esperado JSON."}), 400

        # Obtém os dados JSON da requisição
        data = request.json
        chave = data.get('chave')

        # Busca a chave no banco de dados
        key_record = Key.query.filter_by(key=chave).first()
        if not key_record:
            return jsonify({"erro": "Chave não encontrada"}), 404

        # Verifica se a chave expirou
        if datetime.now() > key_record.expiration_time:
            return jsonify({"erro": "Chave expirada"}), 400

        # Verifica se a chave já foi ativada (HWID preenchido)
        if key_record.hwid:
            return jsonify({"erro": "Chave já ativada"}), 400

        # Ativa a chave (define o HWID)
        hwid = data.get('hwid')
        if not hwid:
            return jsonify({"erro": "HWID não fornecido"}), 400

        key_record.hwid = hwid
        db.session.commit()

        return jsonify({
            "mensagem": "Chave ativada com sucesso!",
            "expiration_time": key_record.expiration_time.strftime('%d/%m/%Y %H:%M:%S')
        }), 200

    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

if __name__ == '__main__':
    # Usa a porta definida pela variável de ambiente PORT ou 5000 como padrão
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)