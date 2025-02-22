import os
import sys
import hashlib
import logging
import subprocess
import requests
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QPushButton, 
                           QVBoxLayout, QLabel, QMessageBox, QFrame, 
                           QCheckBox, QStackedWidget, QHBoxLayout, QInputDialog)
from PyQt5.QtCore import Qt, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QIcon, QPixmap

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spoofer.log'),
        logging.StreamHandler()
    ]
)

API_URL = "https://mgs-qpbo.onrender.com"  # Ajuste para corresponder ao servidor local
TIMEOUT = 5
RESOURCES_PATH = "resources"
LOGO_PATH = os.path.join(RESOURCES_PATH, "logo.png")
ICON_PATH = os.path.join(RESOURCES_PATH, "icon.ico")
BACKGROUND_PATH = os.path.join(RESOURCES_PATH, "background.png")
_hwid_cache = None

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key()
    with open(".env", "w") as f:
        f.write(f"SECRET_KEY={SECRET_KEY.decode()}\n")
cipher_suite = Fernet(SECRET_KEY)

def get_hwid():
    global _hwid_cache
    if _hwid_cache is None:
        try:
            result = subprocess.check_output('wmic csproduct get uuid').decode()
            _hwid_cache = result.split('\n')[1].strip()
        except:
            _hwid_cache = "HWID_ERROR"
    return _hwid_cache

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self._progress = 0.0
        self.is_admin = False
        self.initUI()

    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = value
        self.update_border(value)

    def initUI(self):
        self.setWindowTitle('MG Spoofer')
        self.setGeometry(100, 100, 480, 360)
        self.setStyleSheet('''
            QWidget {
                background: #1a0058;
            }
        ''')
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        navbar = QFrame()
        navbar.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border-bottom: 2px solid #000080;
            }
        ''')
        navbar_layout = QHBoxLayout()
        navbar_layout.setContentsMargins(10, 5, 10, 5)
        navbar_layout.addStretch(1)

        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText('Usuário')
        self.senha = QLineEdit()
        self.senha.setPlaceholderText('Senha')
        self.senha.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton('LOGIN')
        self.btn_registrar = QPushButton('REGISTRAR')
        
        navbar_style = '''
            QLineEdit {
                padding: 5px;
                border: 2px solid #000080;
                border-radius: 8px;
                background: rgba(20, 20, 40, 180);
                color: #00ffff;
                font-size: 10px;
                max-width: 90px;
            }
            QLineEdit:focus {
                border: 2px solid #00ffff;
                background: rgba(30, 30, 50, 180);
            }
            QPushButton {
                padding: 5px 10px;
                border: none;
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #000080,
                    stop: 1 #4B0082
                );
                color: white;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4B0082,
                    stop: 1 #000080
                );
            }
        '''
        
        for widget in [self.usuario, self.senha, self.btn_login, self.btn_registrar]:
            widget.setStyleSheet(navbar_style)
                
        navbar_layout.addWidget(self.usuario)
        navbar_layout.addWidget(self.senha)
        navbar_layout.addWidget(self.btn_login)
        navbar_layout.addWidget(self.btn_registrar)
        navbar_layout.addStretch(1)
        navbar.setLayout(navbar_layout)
        main_layout.addWidget(navbar)

        self.stack = QStackedWidget()
        
        self.welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(5)
        
        self.login_text = QLabel('FAÇA O LOGIN PARA TER ACESSO')
        self.login_text.setAlignment(Qt.AlignCenter)
        self.login_text.setStyleSheet('''
            QLabel {
                color: #FFFFFF;
                font-size: 10px;
                font-weight: bold;
                background: transparent;
            }
        ''')
        self.spoofer_text = QLabel('SPOOFER MILGRAU')
        self.spoofer_text.setAlignment(Qt.AlignCenter)
        self.spoofer_text.setStyleSheet('''
            QLabel {
                color: #00ffff;
                font-size: 20px;
                font-family: 'Cyberpunk', 'Orbitron', sans-serif;
                font-weight: bold;
                background: transparent;
                padding: 12px;
            }
        ''')
        
        welcome_layout.addWidget(self.login_text)
        welcome_layout.addWidget(self.spoofer_text)
        self.welcome_page.setLayout(welcome_layout)

        self.spoofer_page = QWidget()
        navbar_layout = QHBoxLayout()
        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.spoofer_page)
        
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        self.anim = QPropertyAnimation(self, b"progress")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self.update_border)
        self.anim.start()

        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_registrar.clicked.connect(self.registrar)
        self.usuario.returnPressed.connect(self.fazer_login)
        self.senha.returnPressed.connect(self.fazer_login)

    def fazer_login(self):
        try:
            logging.info(f"Tentando login com usuário: {self.usuario.text()}, HWID: {get_hwid()}")
            response = requests.post(
                f"{API_URL}/login",
                json={
                    "username": self.usuario.text(),
                    "password": hashlib.md5(self.senha.text().encode()).hexdigest(),
                    "hwid": get_hwid()
                },
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )

            logging.info(f"Resposta do servidor: {response.status_code} - {response.text}")

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.is_admin = data.get("isAdmin", False)
                    self.mostrar_sucesso("Login realizado com sucesso!")
                    return True
        
            self.mostrar_erro(f"Erro: {response.json().get('message', 'Erro desconhecido')}")
            return False

        except requests.exceptions.RequestException as e:
            self.mostrar_erro(f"Erro de conexão: {str(e)}")
            return False

    def registrar(self):
        usuario = self.usuario.text()
        senha = self.senha.text()
        hwid = get_hwid()

        try:
            response = requests.post(f"{API_URL}/register", json={
                "username": usuario,
                "password": hashlib.md5(senha.encode()).hexdigest(),
                "hwid": hwid
            }, headers={'Content-Type': 'application/json'}, timeout=TIMEOUT)

            if response.status_code == 201:
                self.mostrar_sucesso('Registro realizado com sucesso!')
            else:
                data = response.json()
                self.mostrar_erro(data.get('message', 'Erro ao registrar'))
        except Exception as e:
            self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')

    def login_sucesso(self):
        self.login_text.hide()
        self.spoofer_text.hide()
        self.usuario.setEnabled(False)
        self.senha.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.btn_registrar.setEnabled(False)
        self.stack.setCurrentWidget(self.spoofer_page)
        self.init_spoofer_page()

    def init_spoofer_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        container = QFrame()
        container.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border: 2px solid #000080;
                border-radius: 15px;
                padding: 20px;
            }
        ''')
        
        spoofer_layout = QVBoxLayout()
        
        buttons_container = QHBoxLayout()
        buttons_container.setSpacing(10)
        
        btn_style = '''
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #000080,
                    stop: 1 #4B0082
                );
                color: white;
                border: none;
                padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
                min-width: 200px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #4B0082,
                    stop: 1 #000080
                );
            }
            QPushButton:disabled {
                background: #333333;
                color: #666666;
            }
        '''
        
        self.btn_guia = QPushButton('GUIA DE DESVINCULAÇÃO')
        self.btn_spoof = QPushButton('SPOOFAR COM 1 CLICK')
        self.btn_guia.setStyleSheet(btn_style)
        self.btn_spoof.setStyleSheet(btn_style)

        if self.is_admin:
            self.btn_key = QPushButton('GERAR KEY')
            self.btn_key.setStyleSheet(btn_style)
            self.btn_key.clicked.connect(self.gerar_key)
        
        self.btn_guia.clicked.connect(self.abrir_guia)
        self.btn_spoof.clicked.connect(self.iniciar_spoof)
        self.btn_spoof.setEnabled(False)
        
        buttons_container.addWidget(self.btn_guia)
        buttons_container.addWidget(self.btn_spoof)
        if self.is_admin:
            buttons_container.addWidget(self.btn_key)
        
        spoofer_layout.addStretch()
        spoofer_layout.addLayout(buttons_container)
        container.setLayout(spoofer_layout)
        layout.addWidget(container)
        self.spoofer_page.setLayout(layout)

        if os.path.exists(LOGO_PATH):
            logo = QPixmap(LOGO_PATH)
            logo_label = QLabel()
            logo_label.setPixmap(logo.scaled(150, 150, Qt.KeepAspectRatio))
            layout.addWidget(logo_label)
        if os.path.exists(BACKGROUND_PATH):
            self.setStyleSheet(f'''
                QWidget {{
                    background-image: url({BACKGROUND_PATH});
                    background-position: center;
                    background-repeat: no-repeat;
                }}
            ''')

    def mostrar_erro(self, mensagem):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle('Erro')
        msg.setText(mensagem)
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
                color: #ff00ff;
            }
            QPushButton {
                background: #ff00ff;
                color: black;
                border: none;
                padding: 6px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()

    def mostrar_sucesso(self, mensagem):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Sucesso')
        msg.setText(mensagem)
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
                color: #00ff99;
            }
            QPushButton {
                background: #00ffff;
                color: black;
                border: none;
                padding: 6px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()
        self.login_sucesso()

    def gerar_key(self):
        try:
            duracao, ok = QInputDialog.getInt(
                self, 'Duração da Key',
                'Digite a quantidade de dias de validade:',
                30, 1, 365, 1
            )
            
            if not ok:
                return
    
            response = requests.post(
                f"{API_URL}/generate_keys",
                json={
                    "quantidade": 1,
                    "duracao_dias": duracao,
                    "generatedBy": self.usuario.text()
                },
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
    
            if response.status_code == 201:
                data = response.json()
                self.mostrar_sucesso(
                    f'Nova key gerada:\nKey: {data["key"]}\n'
                    f'Validade: {duracao} dias'
                )
            else:
                self.mostrar_erro("Erro ao gerar key")
    
        except Exception as e:
            self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')

    def abrir_guia(self):
        msg = QMessageBox()
        msg.setWindowTitle('Guia de Desvinculação')
        msg.setText('''
🔹 Passo 1: Faça backup dos seus dados importantes
🔹 Passo 2: Desligue o antivírus
🔹 Passo 3: Execute o programa como administrador
🔹 Passo 4: Aguarde o processo completar
🔹 Passo 5: Reinicie o computador
        ''')
        
        checkbox = QCheckBox('Li e concordo com os termos acima')
        checkbox.setStyleSheet('color: #00ffff;')
        msg.setCheckBox(checkbox)
        checkbox.stateChanged.connect(lambda state: self.btn_spoof.setEnabled(state == Qt.Checked))
        msg.exec_()

    def iniciar_spoof(self):
        try:
            # Aqui você pode adicionar a lógica para iniciar o processo de spoofing
            self.mostrar_sucesso("Spoofing iniciado com sucesso!")
        except Exception as e:
            self.mostrar_erro(f"Erro ao iniciar spoof: {str(e)}")

    def update_border(self, value):
        if hasattr(self, 'spoofer_text') and self.spoofer_text:
            angle = value * 360
            self.spoofer_text.setStyleSheet(f'''
                QLabel {{
                    color: #00ffff;
                    font-size: 20px;
                    font-family: 'Cyberpunk', 'Orbitron', sans-serif;
                    font-weight: bold;
                    background: transparent;
                    padding: 12px;
                    border: 8px solid transparent;
                    border-radius: 15px;
                    border-image: none;
                    border: 8px solid qconicalgradient(
                        cx:0.5, cy:0.5, angle:{angle},
                        stop:0 rgba(255, 0, 255, 255),
                        stop:0.25 rgba(0, 255, 255, 255),
                        stop:0.5 rgba(255, 0, 255, 255),
                        stop:0.75 rgba(0, 255, 255, 255),
                        stop:1 rgba(255, 0, 255, 255)
                    );
                }}
            ''')

if __name__ == '__main__':
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spoofer.log'),
                logging.StreamHandler()
            ]
        )

        load_dotenv()
        
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        window = MainWindow()
        window.setWindowIcon(QIcon(ICON_PATH))
        window.show()
        
        sys.exit(app.exec_())
        
    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {e}")
        sys.exit(1)