import requests
import json
import hashlib
from datetime import datetime
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QPushButton, 
                            QVBoxLayout, QLabel, QMessageBox, QFrame, QProgressBar, QCheckBox, QStackedWidget, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon, QMovie, QFontDatabase
from PyQt5.QtCore import QPropertyAnimation, QPoint, QEasingCurve
import math
from PyQt5.QtCore import pyqtProperty
import subprocess
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='spoofer.log'
)

# Configurações da API
API_URL = "https://mgs-qpbo.onrender.com"  # Ajuste conforme sua configuração

# Adicione constantes no início do arquivo
ADMIN_CREDENTIALS = {"adm1": "adm1"}
USER_CREDENTIALS = {"test1": "test1"}
VALID_KEYS = ['MGSP-2024', 'CYBER-2024', 'HACK-2024']

def get_hwid():
    try:
        result = subprocess.check_output('wmic csproduct get uuid').decode()
        return result.split('\n')[1].strip()
    except:
        return "HWID_ERROR"

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
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet('''
            QWidget {
                background: #1a0058;  /* Roxo escuro */
            }
        ''')
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Navbar
        navbar = QFrame()
        navbar.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border-bottom: 2px solid #000080;  /* Azul escuro */
            }
        ''')
        navbar_layout = QHBoxLayout()
        navbar_layout.setContentsMargins(10, 5, 10, 5)
        # Adicione um stretch no início para centralizar
        navbar_layout.addStretch(1)

        # Campos de login na navbar
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText('Usuário')
        self.senha = QLineEdit()
        self.senha.setPlaceholderText('Senha')
        self.senha.setEchoMode(QLineEdit.Password)

        # Botões na navbar
        self.btn_login = QPushButton('LOGIN')
        self.btn_registrar = QPushButton('REGISTRAR')
        
        # Estilo dos elementos da navbar
        navbar_style = '''
            QLineEdit {
                padding: 8px;
                border: 2px solid #000080;  /* Azul escuro */
                border-radius: 8px;
                background: rgba(20, 20, 40, 180);
                color: #00ffff;
                font-size: 12px;
                max-width: 150px;
            }
            QLineEdit:focus {
                border: 2px solid #00ffff;
                background: rgba(30, 30, 50, 180);
            }
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #000080,  /* Azul escuro */
                    stop: 1 #4B0082  /* Roxo escuro */
                );
                color: white;
                font-weight: bold;
                font-size: 12px;
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
        # Adicione outro stretch no final para centralizar
        navbar_layout.addStretch(1)

        navbar.setLayout(navbar_layout)
        main_layout.addWidget(navbar)

        # Stack Widget para conteúdo
        self.stack = QStackedWidget()
        
        # Página inicial (antes do login)
        self.welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(5)
        
        # Adiciona os textos iniciais
        self.login_text = QLabel('FAÇA O LOGIN PARA TER ACESSO')
        self.login_text.setAlignment(Qt.AlignCenter)
        self.login_text.setStyleSheet('''
            QLabel {
                color: #FFFFFF;
                font-size: 16px;
                font-weight: bold;
                background: transparent;
            }
        ''')

        self.spoofer_text = QLabel('SPOOFER MILGRAU')
        self.spoofer_text.setAlignment(Qt.AlignCenter)
        self.spoofer_text.setStyleSheet('''
            QLabel {
                color: #00ffff;
                font-size: 32px;
                font-family: 'Cyberpunk', 'Orbitron', sans-serif;
                font-weight: bold;
                background: transparent;
                padding: 20px;
            }
        ''')
        
        welcome_layout.addWidget(self.login_text)
        welcome_layout.addWidget(self.spoofer_text)
        self.welcome_page.setLayout(welcome_layout)
        
        # Página do Spoofer
        self.spoofer_page = QWidget()
        
        self.stack.addWidget(self.welcome_page)
        self.stack.addWidget(self.spoofer_page)
        
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        # Inicia a animação da borda
        self.anim = QPropertyAnimation(self, b"progress")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setLoopCount(-1)
        self.anim.valueChanged.connect(self.update_border)
        self.anim.start()

        # Conexões
        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_registrar.clicked.connect(self.registrar)
        self.usuario.returnPressed.connect(self.fazer_login)
        self.senha.returnPressed.connect(self.fazer_login)

    def fazer_login(self):
        usuario = self.usuario.text()
        senha = self.senha.text()
        hwid = get_hwid()

        try:
            response = requests.post(f"{API_URL}/login", json={
                "username": usuario,
                "password": hashlib.md5(senha.encode()).hexdigest(),
                "hwid": hwid
            }, verify=True, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.is_admin = data.get("isAdmin", False)
                    self.login_sucesso()
                else:
                    self.mostrar_erro(data.get("message", "Erro ao fazer login"))
            else:
                self.mostrar_erro('Usuário ou senha inválidos!')
        except Exception as e:
            self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')

    def login_sucesso(self):
        # Oculta os textos iniciais
        self.login_text.hide()
        self.spoofer_text.hide()
        
        # Desativa campos de login
        self.usuario.setEnabled(False)
        self.senha.setEnabled(False)
        self.btn_login.setEnabled(False)
        self.btn_registrar.setEnabled(False)

        # Mostra a página do spoofer
        self.stack.setCurrentWidget(self.spoofer_page)
        
        # Inicializa a página do spoofer
        self.init_spoofer_page()

    def init_spoofer_page(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Container principal
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
        
        # Área dos botões no final do container
        buttons_container = QHBoxLayout()
        buttons_container.setSpacing(10)
        
        # Estilo comum para todos os botões
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
        
        # Botões comuns
        self.btn_guia = QPushButton('GUIA DE DESVINCULAÇÃO')
        self.btn_spoof = QPushButton('SPOOFAR COM 1 CLICK')
        self.btn_guia.setStyleSheet(btn_style)
        self.btn_spoof.setStyleSheet(btn_style)
        
        # Botão exclusivo para admin
        if self.is_admin:
            self.btn_key = QPushButton('GERAR KEY')
            self.btn_key.setStyleSheet(btn_style)
            self.btn_key.clicked.connect(self.gerar_key)
        
        # Conecta os eventos
        self.btn_guia.clicked.connect(self.abrir_guia)
        self.btn_spoof.clicked.connect(self.iniciar_spoof)
        self.btn_spoof.setEnabled(False)  # Começa desativado
        
        # Adiciona os botões ao container
        buttons_container.addWidget(self.btn_guia)
        buttons_container.addWidget(self.btn_spoof)
        if self.is_admin:
            buttons_container.addWidget(self.btn_key)
        
        spoofer_layout.addStretch()
        spoofer_layout.addLayout(buttons_container)
        
        container.setLayout(spoofer_layout)
        layout.addWidget(container)
        self.spoofer_page.setLayout(layout)

    def mostrar_registro(self):
        self.tela_registro = TelaRegistro()
        self.tela_registro.show()

    def abrir_tela_inicial(self, is_admin):
        self.loading.deleteLater()
        self.tela_inicial = TelaInicial(is_admin)
        self.tela_inicial.show()
        self.close()

    def abrir_discord(self):
        import webbrowser
        webbrowser.open('https://discord.gg/seuservidor')  # Substitua com seu link do Discord

    def registrar(self):
        self.tela_registro = TelaRegistro()
        self.tela_registro.show()

    def mostrar_carregamento(self):
        self.loading = QProgressBar()
        self.loading.setTextVisible(False)
        self.loading.setFixedHeight(3)  # Altura muito pequena para parecer uma linha
        self.loading.setStyleSheet('''
            QProgressBar {
                border: none;
                background: rgba(255, 255, 255, 0.1);
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #ff00ff,
                    stop: 1 #00ffff
                );
            }
        ''')
        self.loading.setRange(0, 0)  # Modo indeterminado
        self.layout().insertWidget(1, self.loading)

    def ativar_spoof(self, state):
        self.btn_spoof.setEnabled(state == Qt.Checked)

    def iniciar_spoof(self):
        # Cria e mostra a janela de spoofing
        self.tela_spoof = TelaSpoofer()
        self.tela_spoof.show()

    def update_process(self):
        if self.current_step < len(self.progress_labels):
            # Atualiza o ícone e a cor do label atual
            self.progress_labels[self.current_step].setStyleSheet('color: #00ffff;')
            self.progress_labels[self.current_step].setText(f'✓ {self.progress_labels[self.current_step].text()[2:]}')
            self.progress_bar.setValue((self.current_step + 1) * 20)
            self.current_step += 1
            
            if self.current_step == len(self.progress_labels):
                QTimer.singleShot(1000, self.finish_process)

    def finish_process(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Sucesso')
        msg.setText('Processo de spoofing concluído com sucesso!')
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
                color: #00ff99;
            }
            QPushButton {
                background: #ff00ff;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()
        self.close()

    def abrir_guia(self):
        # Mostra o guia na mesma janela
        msg = QMessageBox()
        msg.setWindowTitle('Guia de Desvinculação')
        msg.setText('''
🔹 Passo 1: Faça backup dos seus dados importantes
🔹 Passo 2: Desligue o antivírus
🔹 Passo 3: Execute o programa como administrador
🔹 Passo 4: Aguarde o processo completar
🔹 Passo 5: Reinicie o computador
                font-size: 14px;
            }
        ''')
        
        # Checkbox para liberar o botão de spoof
        checkbox = QCheckBox('Li e concordo com os termos acima')
        checkbox.setStyleSheet('color: #00ffff;')
        msg.setCheckBox(checkbox)
        checkbox.stateChanged.connect(lambda state: self.ativar_spoof(state))
        
        msg.exec_()

    def update_border(self, value):
        if hasattr(self, 'spoofer_text') and self.spoofer_text:
            angle = value * 360
            self.spoofer_text.setStyleSheet(f'''
                QLabel {{
                    color: #00ffff;
                    font-size: 32px;
                    font-family: 'Cyberpunk', 'Orbitron', sans-serif;
                    font-weight: bold;
                    background: transparent;
                    padding: 20px;
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

    def confirmar_registro(self):
        usuario = self.usuario.text()
        senha = self.senha.text()
        key = self.key.text()

        if not all([usuario, senha, key]):
            self.mostrar_erro('Todos os campos são obrigatórios!')
            return False

        if len(senha) < 3:
            self.mostrar_erro('A senha deve ter no mínimo 3 caracteres!')
            return False

        if key not in VALID_KEYS:
            self.mostrar_erro('Key de ativação inválida!')
            return False

        return True

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

    def gerar_key(self):
        try:
            response = requests.post(f"{API_URL}/generate_keys", json={
                "quantidade": 1,
                "duracao_dias": 30,
                "generatedBy": self.usuario.text()
            }, verify=True, timeout=5)

            if response.status_code == 201:
                data = response.json()
                key = data.get('key')
                msg = QMessageBox()
                msg.setWindowTitle('Key Gerada')
                msg.setText(f'Nova key gerada:\n{key}')
                msg.setStyleSheet('''
                    QMessageBox {
                        background-color: #1a0058;
                        color: #00ff99;
                    }
                ''')
                msg.exec_()
            else:
                self.mostrar_erro('Erro ao gerar key')
        except Exception as e:
            self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')

    def validar_key(self, key):
        try:
            response = requests.post(f"{API_URL}/validate_key", json={
                "chave": key,
                "username": self.usuario.text(),
                "hwid": get_hwid()
            }, verify=True, timeout=5)
            return response.status_code == 200
        except:
            return False

    def verificar_expiracao(self):
        try:
            response = requests.get(f"{API_URL}/check_expiration", json={
                "username": self.usuario.text(),
                "hwid": get_hwid()
            }, verify=True, timeout=5)
            return response.json().get("expired", True)
        except:
            return True

class TelaInicial(QWidget):
    def __init__(self, is_admin=False):
        super().__init__()
        self.is_admin = is_admin
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MG Spoofer - Menu Principal')
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet('''
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0a0047,
                    stop: 0.5 #1a0058,
                    stop: 1 #380080
                );
            }
            QLabel {
                color: #00ffff;
                font-size: 32px;
                font-weight: bold;
                background: transparent;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #ff00ff,
                    stop: 1 #00ffff
                );
                color: white;
                border: none;
                padding: 15px;
                border-radius: 10px;
                font-size: 16px;
                font-weight: bold;
                margin: 10px;
                min-width: 200px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #00ffff,
                    stop: 1 #ff00ff
                );
            }
        ''')

        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Título
        titulo = QLabel('MENU DO SPOOFER')
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)

        # Container para os botões
        container = QFrame()
        container.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border: 2px solid #00ffff;
                border-radius: 15px;
                padding: 20px;
            }
        ''')
        
        btn_layout = QVBoxLayout()

        # Botão Guia (agora primeiro)
        self.btn_guia = QPushButton('GUIA DE DESVINCULAÇÃO')
        self.btn_guia.clicked.connect(self.abrir_guia)
        btn_layout.addWidget(self.btn_guia)

        # Botão Spoofar (inicialmente desativado)
        self.btn_spoof = QPushButton('SPOOFAR COM 1 CLICK')
        self.btn_spoof.setEnabled(False)  # Começa desativado
        self.btn_spoof.setStyleSheet('''
            QPushButton:disabled {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #666666,
                    stop: 1 #888888
                );
                color: #CCCCCC;
            }
        ''')
        self.btn_spoof.clicked.connect(self.spoofar)
        btn_layout.addWidget(self.btn_spoof)

        # Botão Gerar Key (apenas para admin)
        if self.is_admin:
            self.btn_key = QPushButton('GERAR KEY')
            self.btn_key.setStyleSheet('''
                QPushButton {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #ff0000,
                        stop: 1 #ff00ff
                    );
                }
            ''')
            self.btn_key.clicked.connect(self.gerar_key)
            btn_layout.addWidget(self.btn_key)

        # Botão Sair
        self.btn_sair = QPushButton('SAIR')
        self.btn_sair.clicked.connect(self.sair)
        btn_layout.addWidget(self.btn_sair)

        container.setLayout(btn_layout)
        layout.addWidget(container)
        self.setLayout(layout)

    def spoofar(self):
        self.tela_spoofer = TelaSpoofer()
        self.tela_spoofer.show()

    def abrir_guia(self):
        self.tela_guia = TelaGuia(self)
        self.tela_guia.show()

    def gerar_key(self):
        import random
        import string
        
        key = 'MGSP-' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
        
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Key Gerada')
        msg.setText(f'Nova key gerada:\n{key}')
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
                color: #00ff99;
            }
            QPushButton {
                background: #ff00ff;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()

    def sair(self):
        self.close()

# Adicione esta nova classe após a TelaInicial
class TelaSpoofer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MG Spoofer - Processo')
        self.setGeometry(100, 100, 600, 400)
        self.setStyleSheet('''
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0a0047,
                    stop: 0.5 #1a0058,
                    stop: 1 #380080
                );
            }
            QLabel {
                color: #00ffff;
                font-size: 14px;
                margin: 5px;
            }
            QProgressBar {
                border: 2px solid #00ffff;
                border-radius: 5px;
                text-align: center;
                background-color: rgba(10, 10, 20, 180);
            }
            QProgressBar::chunk {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #ff00ff,
                    stop: 1 #00ffff
                );
            }
        ''')

        layout = QVBoxLayout()
        
        # Container principal
        container = QFrame()
        container.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border: 2px solid #00ffff;
                border-radius: 15px;
                padding: 20px;
            }
        ''')
        
        container_layout = QVBoxLayout()

        # Título do processo
        self.titulo = QLabel('PROCESSO DE SPOOFING')
        self.titulo.setStyleSheet('font-size: 24px; font-weight: bold; text-align: center;')
        self.titulo.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(self.titulo)

        # Labels para as etapas
        self.etapas = [
            'Iniciando processo de spoofing...',
            'Verificando sistema...',
            'Limpando registros...',
            'Alterando identificadores...',
            'Finalizando processo...'
        ]
        
        self.labels = []
        for etapa in self.etapas:
            label = QLabel(f'⌛ {etapa}')
            label.setStyleSheet('color: #808080;')  # Inicialmente cinza
            self.labels.append(label)
            container_layout.addWidget(label)

        # Loading circular
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        container_layout.addWidget(self.progress)

        container.setLayout(container_layout)
        layout.addWidget(container)
        self.setLayout(layout)

        # Iniciar processo
        self.current_step = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_process)
        self.timer.start(1000)  # Atualiza a cada segundo
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

    def update_process(self):
        if self.current_step < len(self.labels):
            # Atualiza o ícone e a cor do label atual
            self.labels[self.current_step].setStyleSheet('color: #00ffff;')
            self.labels[self.current_step].setText(f'✓ {self.etapas[self.current_step]}')
            self.progress.setValue((self.current_step + 1) * 20)
            self.current_step += 1
            
            if self.current_step == len(self.labels):
                QTimer.singleShot(1000, self.finish_process)

    def finish_process(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle('Sucesso')
        msg.setText('Processo de spoofing concluído com sucesso!')
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
                color: #00ff99;
            }
            QPushButton {
                background: #ff00ff;
                color: white;
                border: none;
                padding: 6px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()
        self.close()

# Adicione esta nova classe após TelaSpoofer
class TelaGuia(QWidget):
    def __init__(self, tela_inicial):
        super().__init__()
        self.tela_inicial = tela_inicial
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MG Spoofer - Guia')
        self.setGeometry(100, 100, 700, 500)
        self.setStyleSheet('''
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #0a0047,
                    stop: 0.5 #1a0058,
                    stop: 1 #380080
                );
            }
            QLabel {
                color: #00ffff;
                font-size: 14px;
                margin: 5px;
            }
            QCheckBox {
                color: #00ffff;
                font-size: 14px;
                spacing: 10px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #00ffff;
                border-radius: 5px;
                background: rgba(10, 10, 20, 180);
            }
            QCheckBox::indicator:checked {
                background: #ff00ff;
            }
        ''')

        layout = QVBoxLayout()
        
        # Container principal
        container = QFrame()
        container.setStyleSheet('''
            QFrame {
                background: rgba(10, 10, 20, 180);
                border: 2px solid #00ffff;
                border-radius: 15px;
                padding: 20px;
            }
        ''')
        
        container_layout = QVBoxLayout()

        # Título
        titulo = QLabel('GUIA DE DESVINCULAÇÃO')
        titulo.setStyleSheet('font-size: 24px; font-weight: bold;')
        titulo.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(titulo)

        # Texto do guia
        guia_texto = QLabel('''
            🔹 Passo 1: Faça backup dos seus dados importantes
            🔹 Passo 2: Desligue o antivírus
            🔹 Passo 3: Execute o programa como administrador
            🔹 Passo 4: Aguarde o processo completar
            🔹 Passo 5: Reinicie o computador
            
            ⚠️ ATENÇÃO: Este processo é irreversível!
        ''')
        guia_texto.setWordWrap(True)
        guia_texto.setStyleSheet('font-size: 16px; padding: 20px;')
        container_layout.addWidget(guia_texto)

        # Checkbox de confirmação
        self.checkbox = QCheckBox('Li e concordo com os termos acima')
        self.checkbox.stateChanged.connect(self.ativar_spoof)
        container_layout.addWidget(self.checkbox)

        container.setLayout(container_layout)
        layout.addWidget(container)
        self.setLayout(layout)

    def ativar_spoof(self, state):
        # Ativa o botão de spoof na tela inicial
        self.tela_inicial.btn_spoof.setEnabled(state == Qt.Checked)

class TelaRegistro(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('MG Spoofer - Registro')
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet('''
            QWidget {
                background: #1a0058;
            }
        ''')

        layout = QVBoxLayout()
        
        # Campos de registro
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText('Usuário')
        self.senha = QLineEdit()
        self.senha.setPlaceholderText('Senha')
        self.senha.setEchoMode(QLineEdit.Password)
        self.key = QLineEdit()
        self.key.setPlaceholderText('Key de Ativação')

        # Botão de registro
        self.btn_registrar = QPushButton('REGISTRAR')
        self.btn_registrar.clicked.connect(self.fazer_registro)

        # Estilo dos campos
        style = '''
            QLineEdit {
                padding: 8px;
                border: 2px solid #000080;
                border-radius: 8px;
                background: rgba(20, 20, 40, 180);
                color: #00ffff;
                font-size: 12px;
            }
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
            }
        '''
        
        for widget in [self.usuario, self.senha, self.key, self.btn_registrar]:
            widget.setStyleSheet(style)
            layout.addWidget(widget)

        self.setLayout(layout)

    def fazer_registro(self):
        usuario = self.usuario.text()
        senha = self.senha.text()
        key = self.key.text()
        hwid = get_hwid()  # Adiciona HWID

        try:
            response = requests.post(f"{API_URL}/register", json={
                "username": usuario,
                "password": hashlib.md5(senha.encode()).hexdigest(),
                "key": key,
                "hwid": hwid  # Inclui HWID no registro
            }, verify=True, timeout=5)

            if response.status_code == 201:
                QMessageBox.information(self, 'Sucesso', 'Registro realizado com sucesso!')
                self.close()
            else:
                data = response.json()
                QMessageBox.warning(self, 'Erro', data.get('message', 'Erro ao registrar'))
        except Exception as e:
            QMessageBox.critical(self, 'Erro', f'Erro ao conectar com o servidor: {str(e)}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    tela = MainWindow()
    tela.show()
    sys.exit(app.exec_())