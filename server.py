# server.py
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

    with app.app_context():
    db.create_all()


app = Flask(__name__)

# Configuração do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://spoofer_db_user:2AEikVNcLBxCEkFU1152uSSzX4Nj7Na4@dpg-cuoi7s52ng1s73e9j6p0-a/spoofer_db'
db = SQLAlchemy(app)

# Modelo para armazenar as chaves e HWIDs
class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    hwid = db.Column(db.String(200), nullable=False)

# Rota para ativar uma chave
@app.route('/ativar', methods=['POST'])
def ativar():
    try:
        data = request.json
        key = data.get('key')
        hwid = data.get('hwid')

        if not key or not hwid:
            return jsonify({'success': False, 'message': 'Chave ou HWID ausente!'}), 400

        existing_key = Key.query.filter_by(key=key).first()
        if existing_key:
            return jsonify({'success': False, 'message': 'Chave já ativada!'})

        new_key = Key(key=key, hwid=hwid)
        db.session.add(new_key)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Chave ativada com sucesso!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500

# Rota para validar uma chave
@app.route('/validar', methods=['POST'])
def validar():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')

    # Verificar se a chave existe e se o HWID corresponde
    existing_key = Key.query.filter_by(key=key).first()
    if not existing_key:
        return jsonify({'success': False, 'message': 'Chave inválida!'})
    if existing_key.hwid != hwid:
        return jsonify({'success': False, 'message': 'Chave vinculada a outro computador!'})
    return jsonify({'success': True, 'message': 'Chave válida!'})

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))  # Usa a porta do Render ou 5000 como padrão
    app.run(host='0.0.0.0', port=port)