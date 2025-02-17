from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configuração do banco de dados PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/dbname'
db = SQLAlchemy(app)

# Modelo para armazenar as chaves e HWIDs
class Key(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    hwid = db.Column(db.String(200), nullable=False)

# Rota para ativar uma chave
@app.route('/ativar', methods=['POST'])
def ativar():
    data = request.json
    key = data.get('key')
    hwid = data.get('hwid')

    # Verificar se a chave já foi ativada
    existing_key = Key.query.filter_by(key=key).first()
    if existing_key:
        return jsonify({'success': False, 'message': 'Chave já ativada!'})

    # Salvar a chave e o HWID no banco de dados
    new_key = Key(key=key, hwid=hwid)
    db.session.add(new_key)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Chave ativada com sucesso!'})

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
    app.run(debug=True)