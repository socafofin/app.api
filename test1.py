import os
import sys
import hashlib
import logging
import subprocess
import requests
import time
import ctypes
import shutil
import json
import warnings
from pathlib import Path
from dotenv import load_dotenv
from PyQt5.QtCore import QSize, Qt, QPropertyAnimation, pyqtProperty, QTimer, QParallelAnimationGroup, QEasingCurve, QUrl, QRect, QEvent
from PyQt5.QtGui import QIcon, QPixmap, QColor, QDesktopServices
from PyQt5.QtWidgets import (QApplication, QWidget, QLineEdit, QPushButton, 
                             QVBoxLayout, QLabel, QMessageBox, QFrame, 
                             QStackedWidget, QHBoxLayout, QInputDialog, QProgressBar, QTextEdit, QDialog, QGraphicsOpacityEffect, QGraphicsDropShadowEffect, QProgressDialog)
from cryptography.fernet import Fernet

warnings.filterwarnings("ignore", category=DeprecationWarning)

def run_as_admin():
    try:
        if not ctypes.windll.shell32.IsUserAnAdmin():
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()
    except Exception as e:
        logging.error(f"Erro ao tentar executar como admin: {str(e)}")

# Adicionar mais informações nos logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s - %(message)s',
    handlers=[
        logging.FileHandler('spoofer.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

API_URL = "https://mgs-qpbo.onrender.com"
TIMEOUT = 10
RESOURCES_PATH = "resources"
LOGO_PATH = os.path.join(RESOURCES_PATH, "logo.png")
ICON_PATH = os.path.join(RESOURCES_PATH, "icon.ico")
BACKGROUND_PATH = os.path.join(RESOURCES_PATH, "background.png")
DISCORD_ICON = os.path.join(RESOURCES_PATH, "discord.ico")
_hwid_cache = None
DISCORD_LINK = 'https://discord.gg/Kt7Du56e'
CURRENT_VERSION = "3.1.0"
UPDATE_CHECK_INTERVAL = 300000 # Altere para seu link


load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    SECRET_KEY = Fernet.generate_key()
    with open(".env", "w") as f:
        f.write(f"SECRET_KEY={SECRET_KEY.decode()}\n")
cipher_suite = Fernet(SECRET_KEY)

def get_hwid():
    try:
        if hasattr(get_hwid, '_cache'):
            return get_hwid._cache
        result = subprocess.check_output('wmic csproduct get uuid').decode()
        hwid = result.split('\n')[1].strip()
        get_hwid._cache = hwid
        return hwid
    except Exception as e:
        logging.error(f"Erro ao obter HWID: {e}")
        return "HWID_ERROR"

def add_shadow_effect(widget):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(20)
    shadow.setColor(QColor(0, 0, 0, 160))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)

def create_fade_animation(widget, start=0.0, end=1.0, duration=500):
    fade_anim = QPropertyAnimation(widget, b"windowOpacity")
    fade_anim.setStartValue(start)
    fade_anim.setEndValue(end)
    fade_anim.setDuration(duration)
    fade_anim.setEasingCurve(QEasingCurve.InOutCubic)
    return fade_anim

def create_title_bar(self):
    title_bar = QFrame()
    title_bar.setFixedHeight(40)
    title_bar.setStyleSheet('''
        QFrame {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 #2b5876,
                stop: 1 #4e4376
            );
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        }
    ''')

    layout = QHBoxLayout(title_bar)
    layout.setContentsMargins(10, 0, 10, 0)

    title = QLabel("MILGRAU Spoofer")
    title.setStyleSheet('''
        QLabel {
            color: white;
            font-size: 14px;
            font-weight: bold;
        }
    ''')

    layout.addWidget(title)
    layout.addStretch()

    return title_bar

MODERN_STYLE = '''
    QWidget {
        background: qradialgradient(
            cx: 0.5, cy: 0.5, radius: 1,
            fx: 0.5, fy: 0.5,
            stop: 0 #1a0058,
            stop: 0.5 #000033,
            stop: 1 #000022
        );
        color: #ffffff;
        font-family: 'Segoe UI', Arial;
    }

    QFrame {
        background: rgba(26, 0, 88, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    QFrame:hover {
        border: 1px solid rgba(255, 255, 255, 0.2);
        background: rgba(26, 0, 88, 0.5);
    }
'''

# Adicionar efeitos hover mais elaborados
button_style = '''
    QPushButton {
        padding: 8px 15px;
        border: none;
        border-radius: 8px;
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #000080,
            stop: 1 #4B0082
        );
        color: white;
        font-weight: bold;
        font-size: 11px;
        transition: all 0.3s;
    }
    QPushButton:hover {
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 0,
            stop: 0 #4B0082,
            stop: 1 #000080
        );
        transform: scale(1.05);
    }
'''

class MainWindow(QWidget):

    def abrir_configuracoes_defender(self):
        try:
            # Comandos para desativar diferentes aspectos do Windows Defender
            comandos = [
                'powershell -Command "Set-MpPreference -DisableRealtimeMonitoring $true"',
                'powershell -Command "Set-MpPreference -DisableBehaviorMonitoring $true"',
                'powershell -Command "Set-MpPreference -DisableBlockAtFirstSeen $true"',
                'powershell -Command "Set-MpPreference -DisableIOAVProtection $true"',
                'powershell -Command "Set-MpPreference -DisablePrivacyMode $true"',
                'powershell -Command "Set-MpPreference -SignatureDisableUpdateOnStartupWithoutEngine $true"',
                'powershell -Command "Set-MpPreference -DisableArchiveScanning $true"',
                'powershell -Command "Set-MpPreference -DisableIntrusionPreventionSystem $true"',
                'powershell -Command "Set-MpPreference -DisableScriptScanning $true"'
            ]
            
            for comando in comandos:
                subprocess.run(comando, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
            # Abre as configurações do Windows Defender como backup
            subprocess.run('start ms-settings:windowsdefender', shell=True)
            return True
        except Exception as e:
            logging.error(f"Erro ao configurar Windows Defender: {str(e)}")
            return False
    def __init__(self):
        super().__init__()
        width = int(400 )  # 52% do original
        height = int(500 )  # 45% do original
        
        self.setWindowTitle('MILGRAU Spoofer')
        self.setGeometry(100, 100, width, height)
        self.setWindowIcon(QIcon(ICON_PATH))
        
        # Adicione estas duas linhas para travar o redimensionamento
        self.setFixedSize(width, height)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)  # Remove botões maximizar/minimizar
        
        self.setStyleSheet(MODERN_STYLE)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Criar o container para versões aqui
        bottom_container = QWidget()
        bottom_container.setFixedHeight(30)
        bottom_layout = QHBoxLayout(bottom_container)
        bottom_layout.setContentsMargins(10, 0, 10, 5)

        version_label = QLabel('V:3.1')
        gpt_label = QLabel('97,78%')

        label_style = """
            QLabel {
                color: rgb(0, 238, 255);
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }
        """
        version_label.setStyleSheet(label_style)
        gpt_label.setStyleSheet(label_style)

        bottom_layout.addWidget(version_label)
        bottom_layout.addStretch()
        bottom_layout.addWidget(gpt_label)

        # Ajuste do navbar
        navbar = QFrame()
        navbar.setStyleSheet("""
            QFrame {
                background: rgba(10, 10, 20, 0.85);
                border-bottom: 2px solid #000080;
                max-height: 35px;  /* Aumentado */
            }
        """)

        # Ajuste das margens do navbar
        navbar_layout = QHBoxLayout()
        navbar_layout.setContentsMargins(10, 5, 10, 5)  # Aumentado
        navbar_layout.setSpacing(8)  # Aumentado
        
        self.usuario = QLineEdit()
        self.usuario.setPlaceholderText('Usuário')
        self.senha = QLineEdit()
        self.senha.setPlaceholderText('Senha')
        self.senha.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton('LOGIN')
        self.btn_registrar = QPushButton('REGISTRAR')
        
        # Adiciona o botão do Discord primeiro
        self.btn_discord = QPushButton()
        self.btn_discord.setIcon(QIcon(DISCORD_ICON))
        self.btn_discord.setIconSize(QSize(50, 30))  # Aumenta o tamanho do ícone
        self.btn_discord.setFixedSize(60, 25)  # Aumenta largura para 70 e mantém altura 40
        self.btn_discord.setCursor(Qt.PointingHandCursor)
        self.btn_discord.setStyleSheet('''
            QPushButton {
            background-color: rgba(76, 0, 163, 0.6);
            border: 2px solid white;
            border-radius: 12px;
            padding: 4px;
            }
            QPushButton:hover {
            background-color: rgba(76, 0, 163, 0.6);
            border-color:rgb(83, 1, 138);
            }
        ''')

        # Adicione o efeito de brilho roxo
        glow_discord = QGraphicsDropShadowEffect()
        glow_discord.setBlurRadius(15)
        glow_discord.setColor(QColor('76, 0, 163, 0.6'))  # Roxo escuro
        glow_discord.setOffset(0, 0)
        self.btn_discord.setGraphicsEffect(glow_discord)

        
        # Adiciona os widgets ao layout na ordem correta
        navbar_layout.addWidget(self.usuario)
        navbar_layout.addWidget(self.senha)
        navbar_layout.addWidget(self.btn_login)
        navbar_layout.addWidget(self.btn_registrar)
        navbar_layout.addWidget(self.btn_discord)  # Adiciona o botão do Discord por último
        
        # Define o layout do navbar
        navbar.setLayout(navbar_layout)
        
        # Adiciona o navbar ao layout principal
        main_layout.addWidget(navbar, 0, Qt.AlignTop)  # Força o navbar no topo

        # Estilo dos elementos do navbar
        navbar_style = """
            QLineEdit {
                padding: 5px 8px;  /* Aumentado */
                border: 2px solid #000080;
                border-radius: 6px;  
                background: rgba(20, 20, 40, 0.7);
                color: #00ffff;
                font-size: 11px;  /* Aumentado */
                min-width: 65px;  /* Reduzido de 80px para 65px */
                max-height: 25px;  /* Aumentado */
            }
            QPushButton {
                padding: 5px 10px;  /* Aumentado */
                border-radius: 6px;
                font-size: 11px;  /* Aumentado */
                max-height: 25px;  /* Aumentado */
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #000080,
                    stop:1 #4B0082
                );
                color: white;
            }
        """
        
        for widget in [self.usuario, self.senha, self.btn_login, self.btn_registrar]:
            widget.setStyleSheet(navbar_style)

        main_layout.addWidget(navbar)

        if os.path.exists(LOGO_PATH):
            logo = QPixmap(LOGO_PATH)
            self.logo_label = QLabel()
            # Aumentando a largura para 400 (largura total da janela)
            self.logo_label.setPixmap(logo.scaled(450, 500, Qt.KeepAspectRatio))  # Aumentado de 300 para 400
            self.logo_label.setAlignment(Qt.AlignCenter)
            self.logo_label.setStyleSheet('''
                QLabel {
                    background: transparent;
                }
            ''')
            main_layout.insertWidget(1, self.logo_label)

        self.stack = QStackedWidget()
        
        self.welcome_page = QWidget()
        welcome_layout = QVBoxLayout()
        welcome_layout.setSpacing(5)
        
        self.login_text = QLabel('FAÇA O LOGIN PARA TER ACESSO')
        self.login_text.setAlignment(Qt.AlignCenter)
        self.login_text.setStyleSheet('''
            QLabel {
                color:rgb(0, 238, 255);
                font-size: 20px;
                font-weight: bold;
                background: transparent;
            }
        ''')
        # Adiciona efeito de brilho no texto de login
        glow_login = QGraphicsDropShadowEffect()
        glow_login.setBlurRadius(25)  # Aumentado o blur
        glow_login.setColor(QColor(0, 238, 255))  # Mesma cor do texto
        glow_login.setOffset(0, 0)
        self.login_text.setGraphicsEffect(glow_login)

        # Cria animação pulsante para o glow_login
        self.glow_animation_login = QPropertyAnimation(glow_login, b"blurRadius")
        self.glow_animation_login.setDuration(1500)  # 1.5 segundos por ciclo
        self.glow_animation_login.setStartValue(10)
        self.glow_animation_login.setEndValue(50)
        self.glow_animation_login.setLoopCount(-1)  # Loop infinito
        self.glow_animation_login.setEasingCurve(QEasingCurve.InOutQuad)

        self.login_text.setGraphicsEffect(glow_login)
        self.glow_animation_login.start()

        self.spoofer_text = QLabel('SPOOFER MILGRAU')
        self.spoofer_text.setAlignment(Qt.AlignCenter)
        self.spoofer_text.setStyleSheet("""
            QLabel {
                color: #b809a9;
                font-size: 27px;  /* Reduzido em 20% de 34px */
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                background: transparent;
                padding: 8px;  /* Reduzido em 20% */
                border: 2px solid #b809a9;
                border-radius: 5px;  /* Reduzido em 20% */
                margin: 0px;
            }
        """)

        # Efeito de brilho mais suave
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(40)  # Reduzido para mais suavidade
        glow.setColor(QColor('#4B0082'))  # Roxo escuro
        glow.setOffset(0, 0)
        self.spoofer_text.setGraphicsEffect(glow)

        # Animação mais suave
        self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
        self.glow_animation.setDuration(2000)  # Aumentado para 2 segundos
        self.glow_animation.setStartValue(15)
        self.glow_animation.setEndValue(25)  # Reduzido range para mais suavidade
        self.glow_animation.setLoopCount(-1)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutSine)  # Curva mais suave

        self.spoofer_text.setGraphicsEffect(glow)
        self.glow_animation.start()

        welcome_layout.addWidget(self.login_text)
        welcome_layout.addWidget(self.spoofer_text)
        self.welcome_page.setLayout(welcome_layout)

        self.stack.addWidget(self.welcome_page)
        
        self.spoofer_page = QWidget()
        
        self.stack.addWidget(self.spoofer_page)
        
        main_layout.addWidget(self.stack)
        self.setLayout(main_layout)
        
        self.btn_login.clicked.connect(self.fazer_login)
        self.btn_registrar.clicked.connect(self.registrar)
        self.usuario.returnPressed.connect(self.fazer_login)
        self.senha.returnPressed.connect(self.fazer_login)

         # Cria o botão redondo decorativo
        self.btn_decorative = QPushButton()
        self.btn_decorative.setIcon(QIcon('resources/icon.ico'))  # Usa o ícone do app
        self.btn_decorative.setIconSize(QSize(150, 150))  # Tamanho do ícone
        self.btn_decorative.setFixedSize(50, 50)  # Tamanho do botão
        self.btn_decorative.setCursor(Qt.PointingHandCursor)
        self.btn_decorative.setStyleSheet('''
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 25px;  /* Metade do tamanho para ficar circular */
                padding: 8px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #000080,
                    stop: 1 #4B0082
                );
            }
        ''')

        # Adiciona ao layout principal
        main_layout.addStretch()  # Empurra o botão para baixo

        # Cria um container para o botão com margens negativas para ajustar o posicionamento
        btn_container = QWidget()
        btn_container.setStyleSheet('background: transparent;')
        btn_layout = QVBoxLayout(btn_container)  # Mudado para QVBoxLayout
        btn_layout.setContentsMargins(-10, -10, -10, -10)  # Margens negativas para ajuste fino
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_decorative, alignment=Qt.AlignCenter)

        # Adicionar efeito de brilho rosa aos labels
        def add_pink_glow(widget):
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(15)
            glow.setColor(QColor('#ff1493'))  # Rosa forte
            glow.setOffset(0, 0)
            widget.setGraphicsEffect(glow)

        add_pink_glow(version_label)
        add_pink_glow(gpt_label)

        # Label da versão esquerda
        version_label = QLabel('V:3.1')
        version_label.setStyleSheet("""
            QLabel {
                color: #ff69b4;
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }
        """)

        # Container do ícone central
        self.btn_decorative.setFixedSize(50, 50)
        self.btn_decorative.setIconSize(QSize(100, 100))

        # Label da versão direita
        gpt_label = QLabel('97,78%')
        gpt_label.setStyleSheet("""
            QLabel {
                color: #ff69b4;
                font-weight: bold;
                font-size: 12px;
                background: transparent;
            }
        """)

        # Adiciona o container ao layout principal
        main_layout.addStretch()
        main_layout.addWidget(bottom_container)

        # Adicione um botão de spoof ao layout
        self.btn_spoof = QPushButton('SPOOFAR COM 1 CLICK')
        self.btn_spoof.setEnabled(False)  # Começa desabilitado
        self.btn_spoof.setStyleSheet(
            "QPushButton {"
            "    padding: 10px 20px;"
            "    border: none;"
            "    border-radius: 8px;"
            "    background: #330000;  /* Vermelho ainda mais escuro */"
            "    color: #ff3333;"
            "    font-weight: bold;"
            "}"
            "QPushButton:disabled {"
            "    background: #330000;"
            "    color: #ff3333;"
            "}"
            "QPushButton:disabled:hover {"
            "    background: #400000;"
            "}"
            "QPushButton:enabled {"
            "    background: qlineargradient("
            "        x1: 0, y1: 0, x2: 1, y2: 0,"
            "        stop: 0 #000080,"
            "        stop: 1 #4B0082"
            "    );"
            "    color: white;"
            "}"
        )
        # Conecte o botão à função iniciar_spoof
        self.btn_spoof.clicked.connect(self.iniciar_spoof)
        # Adicione o botão ao seu layout (ajuste conforme sua interface)
        main_layout.addWidget(self.btn_spoof)
        # Modifique o texto quando estiver desabilitado
        self.btn_spoof.installEventFilter(self)

        # Adicionando texto deslizante abaixo do navbar
        news_label = QLabel()
        news_text = "🔔 Bem-vindo ao MilGrau Spoofer - Sorteio de KEY no discord | 💫 Novo sistema anti-detecção! | 🎮 Suporte 24/7 no Discord | 🌟 Atualizações constantes"
        news_label.setText(news_text)
        news_label.setStyleSheet("""
            QLabel {
                color:rgb(0, 238, 255);
                font-size: 11px;
                font-weight: bold;
                background: transparent;
            }
        """)

        # Adiciona efeito de brilho rosa
        glow_effect = QGraphicsDropShadowEffect()
        glow_effect.setBlurRadius(30)
        glow_effect.setColor(QColor('#ff1493'))
        glow_effect.setOffset(0, 10)
        news_label.setGraphicsEffect(glow_effect)

        def update_animation():
            width = self.width()
            content_width = news_label.fontMetrics().width(news_text)
            
            self.news_animation = QPropertyAnimation(news_label, b"geometry")
            self.news_animation.setDuration(20000)
            self.news_animation.setStartValue(QRect(width, 35, content_width, 25))
            self.news_animation.setEndValue(QRect(-content_width, 35, content_width, 25))
            self.news_animation.setEasingCurve(QEasingCurve.Linear)
            self.news_animation.finished.connect(update_animation)  # Reconecta para loop infinito
            self.news_animation.start()

        # Adiciona o label após o navbar e inicia a animação
        main_layout.insertWidget(1, news_label)
        update_animation()
        
        self.init_update_button()

    def eventFilter(self, obj, event):
        if obj == self.btn_spoof and not obj.isEnabled():
            if event.type() == QEvent.Enter:
                obj.setText('BLOQUEADO')
            elif event.type() == QEvent.Leave:
                obj.setText('SPOOFAR COM 1 CLICK')
        return super().eventFilter(obj, event)
    def fazer_login(self):
        try:
            logging.info(f"Tentando login com usuário: {self.usuario.text()}, HWID: {get_hwid()}")
            
            # Verifica conexão com servidor
            try:
                requests.get(f"{API_URL}/ping", timeout=5)
            except requests.exceptions.RequestException:
                self.mostrar_erro("Servidor offline ou inacessível!")
                return False
                
            # Faz requisição de login
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
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.is_admin = data.get("isAdmin", False)
                    if not self.is_admin and not self.verificar_expiracao():
                        return False
                        
                    self.login_sucesso()
                    return True
                    
            self.mostrar_erro(response.json().get('message', 'Erro desconhecido'))
            return False
            
        except requests.exceptions.ConnectionError:
            self.mostrar_erro("Erro de conexão com servidor!")
            return False
        except Exception as e:
            logging.error(f"Erro no login: {str(e)}")
            self.mostrar_erro(f"Erro no login: {str(e)}")
            return False
    def registrar(self):
        # Criar diálogo de registro
        dialog = QDialog(self)
        dialog.setWindowTitle('Registro')
        dialog.setWindowFlags(dialog.windowFlags() | Qt.WindowContextHelpButtonHint)  # Adiciona o botão ?
        dialog.setStyleSheet('''
            QDialog {
                background-color: #1a0058;
            }
        ''')
        layout = QVBoxLayout()
        # Campos do formulário
        usuario_label = QLabel('Usuário:')
        senha_label = QLabel('Senha:')
        key_label = QLabel('Key de Ativação:')
        usuario_input = QLineEdit(self.usuario.text())
        senha_input = QLineEdit(self.senha.text())
        key_input = QLineEdit()
        senha_input.setEchoMode(QLineEdit.Password)
        # Estilo
        style = '''
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #000080;
                border-radius: 8px;
                background: rgba(20, 20, 40, 180);
                color: #00ffff;
                font-size: 10px;
            }
            QLineEdit:focus {
                border: 2px solid #00ffff;
                background: rgba(30, 30, 50, 180);
            }
        '''
        dialog.setStyleSheet(style)
        # Botão de confirmar
        btn_confirmar = QPushButton('Confirmar')
        btn_confirmar.setStyleSheet('''
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
        ''')
        # Adicionar widgets ao layout
        layout.addWidget(usuario_label)
        layout.addWidget(usuario_input)
        layout.addWidget(senha_label)
        layout.addWidget(senha_input)
        layout.addWidget(key_label)
        layout.addWidget(key_input)
        layout.addWidget(btn_confirmar)
        dialog.setLayout(layout)
        def fazer_registro():
            usuario = usuario_input.text()
            senha = senha_input.text()
            key = key_input.text()
            if not all([usuario, senha, key]):
                self.mostrar_erro('Todos os campos são obrigatórios!')
                return
            if len(senha) < 3:
                self.mostrar_erro('A senha deve ter no mínimo 3 caracteres!')
                return
            try:
                response = requests.post(
                    f"{API_URL}/register", 
                    json={
                        "username": usuario,
                        "password": hashlib.md5(senha.encode()).hexdigest(),
                        "hwid": get_hwid(),
                        "key": key
                    }, 
                    headers={'Content-Type': 'application/json'}, 
                    timeout=TIMEOUT
                )
                if response.status_code == 201:
                    self.mostrar_sucesso('Registro realizado com sucesso!')
                    dialog.accept()
                else:
                    data = response.json()
                    self.mostrar_erro(data.get('message', 'Erro ao registrar'))
            except Exception as e:
                self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')
        btn_confirmar.clicked.connect(fazer_registro)
        dialog.exec_()
    def login_sucesso(self):
        try:
            logging.info("Login bem-sucedido. Iniciando transição para tela de spoofer.")
            self._complete_login_transition()
                
        except Exception as e:
            logging.error(f"Erro na transição: {str(e)}")
            self.mostrar_erro(f"Erro na transição: {str(e)}")
    def _complete_login_transition(self):
        try:
            logging.info(f"Completando transição. Status admin: {self.is_admin}")
            
            # Desabilita campos de login
            self.usuario.setEnabled(False)
            self.senha.setEnabled(False)
            self.btn_login.setEnabled(False)
            self.btn_registrar.setEnabled(False)

            # Esconde a logo
            if hasattr(self, 'logo_label'):
                self.logo_label.hide()
            
            # Adiciona informações de expiração para usuários não-admin
            if not self.is_admin:
                try:
                    # Cria o QLabel para informações de expiração
                    expiration_info = QLabel()
                    expiration_info.setAlignment(Qt.AlignCenter)
                    
                    response = requests.post(
                        f"{API_URL}/check_expiration",
                        json={
                            "username": self.usuario.text(),
                            "password": hashlib.md5(self.senha.text().encode()).hexdigest(),
                            "hwid": get_hwid()
                        },
                        headers={'Content-Type': 'application/json'},
                        timeout=TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        remaining_days = int(data.get("remainingDays", 0))
                        remaining_hours = int(data.get("remainingHours", 0))
                        
                        if data.get("valid"):
                            expiration_info.setText(
                                f'<div style="text-align: center;">'
                                f'<span style="color: #00ff00;">🕒 Licença válida</span><br>'
                                f'<span style="color: #00ffff;">{remaining_days} dias e {remaining_hours} horas restantes</span><br>'
                                f'<span style="color: #ff69b4;">Expira em: {data.get("expirationDate", "N/A")}</span>'
                                f'</div>'
                            )
                        else:
                            expiration_info.setText(
                                '<span style="color: #ff0000;">⚠️ Licença expirada!</span>'
                            )
                        
                        expiration_info.setStyleSheet("""
                            QLabel {
                                background-color: rgba(0, 0, 0, 0.3);
                                border: 2px solid #000080;
                                border-radius: 8px;
                                padding: 12px;
                                font-size: 12px;
                                font-weight: bold;
                                margin: 5px;
                            }
                        """)
                        
                        # Adiciona efeito de brilho
                        glow = QGraphicsDropShadowEffect()
                        glow.setBlurRadius(15)
                        glow.setColor(QColor('#4B0082'))
                        glow.setOffset(0, 0)
                        expiration_info.setGraphicsEffect(glow)
                        
                        # Adiciona ao layout principal após o navbar
                        if self.layout():
                            # Remove widget antigo de expiração se existir
                            for i in range(self.layout().count()):
                                widget = self.layout().itemAt(i).widget()
                                if isinstance(widget, QLabel) and widget != self.logo_label:
                                    widget.deleteLater()
                            
                            # Adiciona novo widget de expiração
                            self.layout().insertWidget(1, expiration_info)
                            
                        logging.info(f"Informações de expiração atualizadas: {data}")
                
                except Exception as e:
                    logging.error(f"Erro ao obter informações de expiração: {str(e)}")
            
            # Continua com o resto do código original...
            if self.is_admin:
                admin_container = QFrame()
                admin_container.setStyleSheet('''
                    QFrame {
                        background-color: rgba(76, 0, 163, 0.2);
                        border: 2px solid #4B0082;
                        border-radius: 10px;
                        margin: 5px;
                        padding: 5px;
                    }
                ''')
                
                admin_layout = QHBoxLayout()
                admin_layout.setContentsMargins(5, 5, 5, 5)
                
                # Cria o botão gerar key com estilo personalizado
                self.btn_gerar_key = QPushButton('🔑 Gerar Key')
                self.btn_gerar_key.setStyleSheet('''
                    QPushButton {
                        padding: 8px 15px;
                        border: none;
                        border-radius: 8px;
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 0,
                            stop: 0 #000080,
                            stop: 1 #4B0082
                        );
                        color: white;
                        font-weight: bold;
                        font-size: 12px;
                        min-width: 100px;
                    }
                    QPushButton:hover {
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 0,
                            stop: 0 #4B0082,
                            stop: 1 #000080
                        );
                    }
                ''')
                
                # Adiciona efeito de brilho
                glow = QGraphicsDropShadowEffect()
                glow.setBlurRadius(15)
                glow.setColor(QColor('#4B0082'))
                glow.setOffset(0, 0)
                self.btn_gerar_key.setGraphicsEffect(glow)
                
                self.btn_gerar_key.clicked.connect(self.gerar_key)
                admin_layout.addWidget(self.btn_gerar_key)
                admin_container.setLayout(admin_layout)
                
                # Adiciona o container ao layout principal após o navbar
                if self.layout():
                    self.layout().insertWidget(1, admin_container)
                    
                logging.info("Container de admin adicionado com sucesso")
            
            # Inicializa página do spoofer
            self.init_spoofer_page()
            self.stack.setCurrentWidget(self.spoofer_page)
            
        except Exception as e:
            logging.error(f"Erro na transição: {str(e)}")
            self.mostrar_erro(f"Erro na transição: {str(e)}")
    def init_spoofer_page(self):
        try:
            logging.info(f"Inicializando tela de spoofer. Status de admin: {self.is_admin}")
            # Limpa o layout existente
            if self.spoofer_page.layout():
                old_layout = self.spoofer_page.layout()
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    widget = item.widget()
                    if widget is not None:
                        widget.setParent(None)
                QWidget().setLayout(old_layout)
            layout = QVBoxLayout()
            layout.setSpacing(10)
            layout.setContentsMargins(10, 5, 10, 5)
            # Remove o texto "LEIA PARA LIBERAR" da guia de botões e adiciona direto no layout
            info_label = QLabel('LEIA PARA LIBERAR')
            info_label.setAlignment(Qt.AlignCenter)
            info_label.setStyleSheet('''
                QLabel {
                    color: white;
                    font-size: 11px;
                    font-weight: bold;
                    background: transparent;
                    padding: 7px;
                }
            ''')
            # Container apenas para o botão de guia
            buttons_container = QFrame()
            buttons_container.setStyleSheet('''
                QFrame {
                    background-color: rgba(0, 0, 0, 0.3);
                    border: 2px solid #000080;
                    border-radius: 8px;
                    padding: 5px;
                }
            ''')
            buttons_layout = QVBoxLayout()
            buttons_layout.setSpacing(5)
            # Botão mais grosso
            self.btn_action = QPushButton('VERIFICAÇÃO PRÉ-SPOOFAR')
            self.btn_action.setStyleSheet('''
                QPushButton {
                    padding: 10px 15px;
                    border: none;
                    border-radius: 8px;
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #000080,
                        stop: 1 #4B0082
                    );
                    color: white;
                    font-weight: bold;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #4B0082,
                        stop: 1 #000080
                    );
                }
            ''')
            # Adiciona apenas o botão ao container
            buttons_layout.addWidget(self.btn_action)
            buttons_container.setLayout(buttons_layout)
            # Adiciona o texto e o container com o botão ao layout principal
            layout.addWidget(info_label)
            layout.addWidget(buttons_container)
            self.process_info = QTextEdit()
            self.process_info.setReadOnly(True)
            self.process_info.setStyleSheet("""
                QTextEdit {
                    background-color: rgba(10, 10, 31, 0.9);
                    border: 2px solid #2b5876;
                    border-radius: 17px;
                    padding: 10px;
                    color: white;
                    font-family: Consolas;
                    font-size: 10px;
                    min-height: 100px;  /* Aumentado */
                    max-height: 80px;  /* Aumentado */
                }
            """)
            layout.addWidget(self.process_info)
            
            # Adiciona espaço flexível antes da barra
            layout.addSpacing(5)
            
            # Adiciona a barra de progresso
            self.progress_bar = QProgressBar()
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 2px;
                    text-align: center;
                    background-color: #404040;
                    height: 2px;
                    margin-top: 2px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 0,
                        stop: 0 #32CD32,
                        stop: 1 #50C878
                    );
                    border-radius: 2px;
                }
            """)
            layout.addWidget(self.progress_bar)
            
            # Adiciona espaço após a barra
            layout.addSpacing(5)

            # Define o layout na página
            self.spoofer_page.setLayout(layout)
            self.btn_action.clicked.connect(self.abrir_guia)
            logging.info("Tela de spoofer inicializada com sucesso.")
        except Exception as e:
            logging.error(f"Erro ao inicializar tela de spoofer: {str(e)}")
            self.mostrar_erro(f"Erro ao inicializar tela de spoofer: {str(e)}")
        # Adiciona efeito de brilho nas colunas da tela de spoofer
        self.spoofer_page.setStyleSheet('''
            QWidget {
                background-color: #1a0058;
            }
            QFrame {
                border: 2px solid #000080;
                border-radius: 12px;
                padding: 8px;
                background-color: rgba(0, 0, 0, 0.3);
            }
        ''')
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(15)
        glow.setColor(QColor('#4B0082'))
        glow.setOffset(0, 0)
        
        # Crie uma animação para o efeito de brilho
        self.glow_animation = QPropertyAnimation(glow, b"blurRadius")
        self.glow_animation.setDuration(1500)
        self.glow_animation.setStartValue(15)
        self.glow_animation.setEndValue(25)
        self.glow_animation.setLoopCount(-1)
        self.glow_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        self.btn_action.setStyleSheet('''
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
        ''')
    def complete_button_transition(self):
        # Muda o texto do botão
        self.btn_action.setText("SPOOFAR COM 1 CLICK")
        # Cria animação de fade in
        fade_in = QPropertyAnimation(self.btn_action, b"windowOpacity")
        fade_in.setDuration(250)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.finished.connect(lambda: self.btn_action.setEnabled(True))
        fade_in.start()
    def gerar_key(self):
        logging.info(f"Tentando gerar key como admin. Status atual: {self.is_admin}")
        
        # Criar o diálogo aqui
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Gerar Key")
        dialog.setLabelText("Digite a quantidade de dias:")
        dialog.setInputMode(QInputDialog.IntInput)
        dialog.setIntRange(1, 365)
        dialog.setIntValue(30)  # Valor padrão
        
        dialog.setStyleSheet('''
            QInputDialog {
                background-color: #1a0058;
            }
            QLabel {
                color: white;
                font-size: 12px;
            }
            QLineEdit {
                padding: 5px;
                border: 2px solid #000080;
                border-radius: 8px;
                background: rgba(20, 20, 40, 180);
                color: #00ffff;
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
            }
        ''')

        if dialog.exec_() == QDialog.Accepted:
            dias = dialog.intValue()
            try:
                response = requests.post(
                    f"{API_URL}/generate_keys", 
                    json={
                        "quantidade": 1,
                        "duracao_dias": dias,
                        "generatedBy": self.usuario.text(),
                        "username": self.usuario.text(),
                        "password": hashlib.md5(self.senha.text().encode()).hexdigest(),
                        "hwid": get_hwid()
                    }, 
                    headers={
                        'Content-Type': 'application/json'
                    }, 
                    timeout=TIMEOUT
                )
                
                if response.status_code == 201:
                    data = response.json()
                    self.mostrar_sucesso(
                        f'Nova key gerada:\nKey: {data["key"]}\n'
                        f'Validade: {dias} dias'
                    )
                else:
                    data = response.json()
                    self.mostrar_erro(data.get('message', 'Erro ao gerar chave'))
                    
            except Exception as e:
                logging.error(f"Erro ao gerar key: {str(e)}")
                self.mostrar_erro(f'Erro ao conectar com o servidor: {str(e)}')
    def abrir_guia(self):
        try:
            # Cria e configura o diálogo
            check_dialog = QDialog(self)
            check_dialog.setWindowTitle("Verificação do Sistema")
            check_dialog.setFixedSize(400, 500)
            layout = QVBoxLayout(check_dialog)

            # Área de resultados com scroll
            results = QTextEdit()
            results.setReadOnly(True)
            layout.addWidget(results)

            # Container para botões
            buttons_container = QFrame()
            buttons_layout = QVBoxLayout(buttons_container)
            layout.addWidget(buttons_container)

            # Botão continuar sempre habilitado
            btn_continue = QPushButton("✨ Concordo e Desejo Continuar")
            btn_continue.setStyleSheet("""
                QPushButton {
                    padding: 8px 15px;
                    border: none;
                    border-radius: 8px;
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #000080, stop:1 #4B0082);
                    color: white;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #4B0082, stop:1 #000080);
                }
            """)
            
            # Botões de ação
            botoes_acao = {
                "FiveM": QPushButton("🎮 Fechar FiveM"),
                "Discord": QPushButton("📱 Fechar Discord"),
                "Antivírus": QPushButton("🛡️ Configurar Windows Defender"),
                "Logs Windows": QPushButton("🧹 Limpar Logs"),
                "Rastros FiveM": QPushButton("🗑️ Limpar Rastros")
            }

            for btn in botoes_acao.values():
                btn.setStyleSheet(btn_continue.styleSheet())
                buttons_layout.addWidget(btn)

            # Função para atualizar o status
            def atualizar_status():
                results.clear()
                results.append("<h3 style='color: #ff69b4; text-align: center;'>Verificação do Sistema</h3><br>")
                
                checks = {
                    "Administrador": ("✅" if ctypes.windll.shell32.IsUserAnAdmin() else "⚠️", "Admin"),
                    "FiveM": ("✅" if not self.verificar_processo_rodando("FiveM.exe") else "⚠️", "FiveM em execução"),
                    "Antivírus": ("✅" if not self.verificar_antivirus() else "⚠️", "Antivírus ativo"),
                    "Discord": ("✅" if not self.verificar_processo_rodando("Discord.exe") else "⚠️", "Discord em execução"),
                    "Processos Suspeitos": ("✅" if self.verificar_processos_suspeitos() else "⚠️", "Processos suspeitos"),
                    "Espaço em Disco": ("✅" if self.verificar_espaco_disco() else "⚠️", "Pouco espaço em disco"),
                    "Pasta FiveM": ("✅" if self.verificar_pasta_fivem() else "⚠️", "Pasta FiveM não encontrada"),
                    "Logs Windows": ("✅" if self.verificar_logs_limpos() else "⚠️", "Logs do Windows"),
                    "Rastros FiveM": ("✅" if self.verificar_rastros_limpos() else "⚠️", "Rastros do FiveM")
                }

                for item, (status, desc) in checks.items():
                    results.append(f'<span style="color: {"#00ff00" if status == "✅" else "#ff7f00"}">{status} {desc}</span><br>')

            # Conectar ações dos botões
            botoes_acao["FiveM"].clicked.connect(lambda: (
                subprocess.run('taskkill /F /IM "FiveM.exe"', shell=True),
                atualizar_status()
            ))
            
            botoes_acao["Discord"].clicked.connect(lambda: (
                subprocess.run('taskkill /F /IM "Discord.exe"', shell=True),
                atualizar_status()
            ))
            
            botoes_acao["Antivírus"].clicked.connect(lambda: (
                self.abrir_configuracoes_defender(),
                atualizar_status()
            ))
            
            botoes_acao["Logs Windows"].clicked.connect(lambda: (
                self.limpar_registros_windows(),
                atualizar_status()
            ))
            
            botoes_acao["Rastros FiveM"].clicked.connect(lambda: (
                self.verificar_rastros_fivem(),
                atualizar_status()
            ))

            # Botão continuar sempre habilita o botão de spoof
            btn_continue.clicked.connect(lambda: (
                self.btn_spoof.setEnabled(True),
                check_dialog.accept()
            ))

            layout.addWidget(btn_continue)
            
            # Mostra o diálogo primeiro
            check_dialog.show()
            
            # Inicia a verificação inicial após mostrar o diálogo
            QTimer.singleShot(100, atualizar_status)

        except Exception as e:
            logging.error(f"Erro na verificação: {str(e)}")
            self.mostrar_erro(f"Erro ao verificar sistema: {str(e)}")
    def animate_progress(self, target_value):
        # Cria uma animação suave para a barra de progresso
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(1000)  # 1 segundo de duração
        self.progress_animation.setStartValue(self.progress_bar.value())
        self.progress_animation.setEndValue(target_value)
        self.progress_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_animation.start()
    def iniciar_spoof(self):
        try:
            # Limpa o texto anterior
            self.process_info.clear()
            self.progress_bar.setValue(0)
    
            # Inicia o processo
            self.process_info.append('<span style="color: #00ffff;">Iniciando processo de spoof...</span><br>')
            self.animate_progress(20)
    
            # Verifica HWID.exe
            hwid_path = os.path.join(os.path.dirname(__file__), "HWID.exe")
            if not os.path.exists(hwid_path):
                self.process_info.append('<span style="color: #ff0000;">❌ ERRO AO LIMPAR O HWID! CONTACTE O SUPORTE VIA DISCORD!</span>')
                return
    
            # Executa HWID.exe
            self.process_info.append('<span style="color: #00ffff;">Executando HWID.exe...</span>')
            self.animate_progress(40)
            
            process = subprocess.Popen(
                [hwid_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
    
            out, err = process.communicate()
            
            if process.returncode != 0:
                self.process_info.append(f'<span style="color: #ff0000;">❌ Erro: {err.decode()}</span>')
                return
    
            # Processo completo
            self.animate_progress(100)
            self.process_info.append('<span style="color: #00ff00;">✅ Spoof concluído com sucesso!</span>')
            self.mostrar_sucesso("Spoof realizado com sucesso!\nReinicie o computador.")
    
        except Exception as e:
            self.process_info.append(f'<span style="color: #ff0000;">❌ Erro: {str(e)}</span>')
            logging.error(f"Erro ao executar spoof: {str(e)}")
    def show_completion_effects(self):
        # Efeito de brilho na barra de progresso
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor('#4B0082'))
        self.progress_bar.setGraphicsEffect(glow)
        
        # Criar e aplicar o efeito de opacidade
        opacity_effect = OpacityEffect(self.process_info)
        self.process_info.setGraphicsEffect(opacity_effect)
        
        # Criar a animação usando o efeito de opacidade
        fade_animation = QPropertyAnimation(opacity_effect, b"opacity")
        fade_animation.setDuration(1000)
        fade_animation.setStartValue(0.7)
        fade_animation.setEndValue(1.0)
        fade_animation.start()
        
        # Atualiza o status final
        self.process_info.append(
            '<div style="text-align: center; margin-top: 20px;">'
            '<span style="color: #00ff00; font-size: 18px;">✨ Processo concluído com sucesso! ✨</span>'
            '</div>'
        )
    def play_completion_sound(self):
        QSound.play("resources/complete.wav")  # Adicione um arquivo de som
    def update_status_icon(self, text_len, icon, color):
        cursor = self.process_info.textCursor()
        cursor.movePosition(cursor.End)
        cursor.movePosition(cursor.Left, cursor.KeepAnchor, 1)
        # Adiciona o ícone com animação de fade e pulso
        cursor.insertHtml(
            f'<span style="color: {color}; '
            f'animation: fadeIn 0.5s ease-in-out, pulse 1s infinite;">{icon}</span>'
        )
        # Anima a barra de progresso até 100%
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
            }
            QMessageBox QLabel {
                color: #00ffff;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #000080,
                    stop: 1 #4B0082
                );
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 8px;
                min-width: 80px;
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

    def mostrar_erro(self, mensagem):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle('Erro')
        msg.setText(mensagem)
        msg.setStyleSheet('''
            QMessageBox {
                background-color: #1a0058;
            }
            QMessageBox QLabel {
                color: #ff3333;
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
                padding: 8px 20px;
                border-radius: 8px;
            }
        ''')
        msg.exec_()

    def check_resources(self):
        missing = []
        for path in [LOGO_PATH, ICON_PATH, BACKGROUND_PATH]:
            if not os.path.exists(path):
                missing.append(os.path.basename(path))
        
        if missing:
            logging.warning(f"Arquivos de recursos faltando: {', '.join(missing)}")
            self.mostrar_erro(f"Arquivos de recursos faltando:\n{', '.join(missing)}")

    def confirmar_registro(self):
        usuario = self.usuario.text()
        senha = self.senha.text()
        key = self.key.text()  # Você precisa adicionar o campo key no seu layout

        if not all([usuario, senha, key]):
            self.mostrar_erro('Todos os campos são obrigatórios!')
            return False

        if len(senha) < 3:
            self.mostrar_erro('A senha deve ter no mínimo 3 caracteres!')
            return False

        try:
            # Validar a key antes do registro
            if not self.validar_key(key):
                self.mostrar_erro('Key de ativação inválida!')
                return False
            return True
        except Exception as e:
            self.mostrar_erro(f'Erro ao validar key: {str(e)}')
            return False

    def validar_key(self, key):
        try:
            response = requests.post(
                f"{API_URL}/validate_key", 
                json={
                    "chave": key,
                    "username": self.usuario.text(),
                    "hwid": get_hwid()
                }, 
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            logging.info(f"Validação de key: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            logging.error(f"Erro ao validar key: {str(e)}")
            return False

    def verificar_expiracao(self):
        try:
            if self.is_admin:
                logging.info("Usuário é admin, ignorando verificação de expiração")
                return True
                
            response = requests.post(
                f"{API_URL}/check_expiration",
                json={
                    "username": self.usuario.text(),
                    "password": hashlib.md5(self.senha.text().encode()).hexdigest(),
                    "hwid": get_hwid()
                }, 
                headers={'Content-Type': 'application/json'},
                timeout=TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                is_valid = data.get("valid", False)
                expiration_date = data.get("expirationDate")
                remaining_days = data.get("remainingDays", 0)
                
                if is_valid:
                    logging.info(f"Licença válida. Dias restantes: {remaining_days}")
                    return True
                else:
                    logging.warning("Licença expirada ou inválida")
                    self.mostrar_erro(
                        f"Sua licença expirou em: {expiration_date}\n"
                        "Por favor, renove sua licença."
                    )
                    return False
                    
            logging.error(f"Erro ao verificar expiração: {response.status_code}")
            self.mostrar_erro("Erro ao verificar validade da licença")
            return False
                
        except Exception as e:
            logging.error(f"Erro ao verificar expiração: {str(e)}")
            self.mostrar_erro(f"Erro ao verificar expiração: {str(e)}")
            return False

    def verificar_ambiente(self):
        try:
            checks = {
                "Administrador": ctypes.windll.shell32.IsUserAnAdmin(),
                "FiveM fechado": not self.verificar_processo_rodando("FiveM.exe"),
                "Antivírus": not self.verificar_antivirus(),
                "Espaço em disco": self.verificar_espaco_disco(),
                "Conexão internet": self.verificar_conexao(),
                "Pasta FiveM": self.verificar_pasta_fivem(),
                "Discord": "⚠️ Recomendado fechar" if self.verificar_processo_rodando("Discord.exe") else "✅ Fechado"
            }
            
            return all(value is True for value in checks.values() if isinstance(value, bool))
                
        except Exception as e:
            logging.error(f"Erro ao verificar ambiente: {e}")
            return False

    def verificar_processo_rodando(self, processo_nome):
        try:
            output = subprocess.check_output('tasklist', shell=True, encoding='cp437')
            return processo_nome.lower() in output.lower()
        except Exception as e:
            logging.error(f"Erro ao verificar processo {processo_nome}: {str(e)}")
            return False

    def verificar_antivirus(self):
        try:
            # Verifica Windows Defender de forma mais simples
            cmd = 'powershell.exe "Get-MpPreference | Select-Object DisableRealtimeMonitoring"'
            output = subprocess.check_output(cmd, shell=True).decode()
            # Se DisableRealtimeMonitoring for True, significa que está desativado
            return "True" in output
        except:
            # Em caso de erro, assume que está ativado
            return True

    def verificar_espaco_disco(self):
        try:
            espaco_livre = shutil.disk_usage("C:").free
            espaco_gb = espaco_livre / (1024**3)
            return espaco_gb > 10
        except:
            return False

    def verificar_processos_suspeitos(self):
        processos_suspeitos = [
            "Process Hacker.exe", 
            "ProcessHacker.exe",
            "procexp.exe",  # Process Explorer
            "autoruns.exe",
            "Wireshark.exe",
            "dumpcap.exe",
            "procmon.exe",  # Process Monitor
            "filemon.exe",
            "regmon.exe",
            "dbgview.exe",  # Debug View
            "HxD.exe",      # Hex Editor
            "cheatengine-x86_64.exe",
            "cheatengine-i386.exe",
            "ida64.exe",    # IDA Pro
            "ollydbg.exe"   # OllyDbg
        ]
        
        for processo in processos_suspeitos:
            if self.verificar_processo_rodando(processo):
                return False
        return True

    def verificar_conexao(self):
        try:
            requests.get("https://google.com", timeout=5)
            return True
        except:
            return False

    def verificar_pasta_fivem(self):
        try:
            fivem_path = os.path.expandvars(r"%LocalAppData%\FiveM")
            return os.path.exists(fivem_path)
        except:
            return False

    def verificar_rastros_fivem(self):
        try:
            fivem_paths = [
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\logs"),
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\crashes"),
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\data\cache"),
                os.path.expandvars(r"%AppData%\CitizenFX")
            ]
            
            for path in fivem_paths:
                if os.path.exists(path):
                    try:
                        shutil.rmtree(path, ignore_errors=True)
                        logging.info(f"Removido: {path}")
                    except:
                        continue
            return True
        except Exception as e:
            logging.error(f"Erro ao limpar rastros do FiveM: {str(e)}")
            return False

    def limpar_registros_windows(self):
        try:
            # Executa os comandos com elevação e sem fechar as janelas
            comandos = [
                'powershell -Command "Start-Process wevtutil -ArgumentList \'cl System\' -Verb RunAs -WindowStyle Hidden"',
                'powershell -Command "Start-Process wevtutil -ArgumentList \'cl Application\' -Verb RunAs -WindowStyle Hidden"',
                'powershell -Command "Start-Process wevtutil -ArgumentList \'cl Security\' -Verb RunAs -WindowStyle Hidden"',
                'ipconfig /flushdns',
                'netsh winsock reset'
            ]
            
            for comando in comandos:
                subprocess.run(comando, shell=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                time.sleep(0.5)  # Pequena pausa entre comandos
                
            logging.info("Logs do Windows limpos com sucesso")
            return True
        except Exception as e:
            logging.error(f"Erro ao limpar logs do Windows: {str(e)}")
            return False

    def verificar_logs_limpos(self):
        try:
            # Verifica se existem logs do Windows
            return not any([
                os.path.exists(r"C:\Windows\System32\winevt\Logs\Application.evtx"),
                os.path.exists(r"C:\Windows\System32\winevt\Logs\Security.evtx"),
                os.path.exists(r"C:\Windows\System32\winevt\Logs\System.evtx")
            ])
        except:
            return False

    def verificar_rastros_limpos(self):
        try:
            fivem_paths = [
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\logs"),
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\crashes"),
                os.path.expandvars(r"%LocalAppData%\FiveM\FiveM.app\data\cache")
            ]
            return not any(os.path.exists(path) for path in fivem_paths)
        except:
            return False

    def init_update_button(self):
        """Inicializa o botão de atualização"""
        self.btn_update = QPushButton("⬇️ Nova Versão Disponível")
        self.btn_update.setStyleSheet('''
            QPushButton {
                padding: 8px 15px;
                border: none;
                border-radius: 8px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #32CD32,
                    stop: 1 #228B22
                );
                color: white;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #228B22,
                    stop: 1 #32CD32
                );
            }
        ''')
        self.btn_update.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/MilGrauSpoofer/releases")))
        self.btn_update.hide()
        
        if self.layout():
            self.layout().insertWidget(1, self.btn_update)
        
        self.check_for_update()
    
    def check_for_update(self):
        """Verifica se há atualização disponível"""
        try:
            response = requests.post(
                f"{API_URL}/check_updates",
                json={"version": CURRENT_VERSION},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["needs_update"]:
                    self.btn_update.show()
                    
        except Exception as e:
            logging.error(f"Erro ao verificar updates: {str(e)}")

def main():
    try:
        run_as_admin()  # Força execução como admin
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {str(e)}")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        logging.error(f"Erro ao iniciar aplicação: {str(e)}")