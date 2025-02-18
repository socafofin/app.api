import os
import json
import time
import requests
import webbrowser
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime
import subprocess
import random
from cryptography.fernet import Fernet

# Configurações
SERVER_URL = "https://spoofer-db.onrender.com"  # Substitua pelo seu endpoint no Render
DISCORD_LINK = "https://discord.gg/9Z5m4zk9"
LOGO_PATH = "logo.png"
BACKGROUND_PATH = "background.png"

# Gerar ou carregar chave de criptografia
ENCRYPTION_KEY = b'rc1eTMbV4GISlk8z9p1hB--IVtksRBVkfB4bjYqk1Ug='  # Substitua por sua própria chave válida
cipher_suite = Fernet(ENCRYPTION_KEY)

# Função para obter identificadores únicos do hardware (HWID)
def obter_identificadores_hardware():
    try:
        # Obter UUID da placa-mãe
        uuid = subprocess.check_output("wmic csproduct get UUID", shell=True).decode().split("\n")[1].strip()

        # Obter Serial Number do disco rígido
        serial_number = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True).decode().split("\n")[1].strip()

        # Obter MAC Address
        mac_output = subprocess.check_output("getmac /fo csv /nh", shell=True).decode()
        mac_address = mac_output.split(",")[0].strip().strip('"')  # Remove aspas extras
        mac_address = mac_address.replace("-", ":").upper()  # Formata o MAC Address

        return f"{uuid}-{serial_number}-{mac_address}"
    except Exception as e:
        print(f"Erro ao obter identificadores de hardware: {e}")
        return None

# Funções para comunicação com o servidor
def ativar_chave_com_servidor(key, hwid):
    try:
        # Usar POST em vez de GET
        response = requests.post(f"{SERVER_URL}/ativar", json={"key": key, "hwid": hwid})
        data = response.json()
        return data["success"], data["message"]
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return False, "Erro ao conectar ao servidor."

def validar_chave_com_servidor(key, hwid):
    try:
        # Usar POST em vez de GET
        response = requests.post(f"{SERVER_URL}/validar", json={"key": key, "hwid": hwid})
        data = response.json()
        return data["success"], data["message"]
    except Exception as e:
        print(f"Erro ao conectar ao servidor: {e}")
        return False, "Erro ao conectar ao servidor."

# 🎨 Classe para Interface Visual
class VisualManager:
    @staticmethod
    def carregar_fundo(frame):
        try:
            bg = Image.open(BACKGROUND_PATH)
            bg = bg.resize((700, 500), Image.Resampling.LANCZOS)
            bg_image = ImageTk.PhotoImage(bg)
            label_fundo = tk.Label(frame, image=bg_image)
            label_fundo.place(relwidth=1, relheight=1)
            frame.background_image = bg_image  # Mantém a referência
        except Exception as e:
            print(f"Erro ao carregar o fundo: {e}")
            frame.configure(bg="#121212")

    @staticmethod
    def carregar_logo(frame):
        try:
            logo = Image.open(LOGO_PATH)
            logo = logo.resize((150, 150), Image.Resampling.LANCZOS)
            logo_image = ImageTk.PhotoImage(logo)
            label_logo = tk.Label(frame, image=logo_image, bg="#1E1E1E")
            label_logo.image = logo_image  # Mantém a referência
            label_logo.pack(pady=10)
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            tk.Label(frame, text="Logo", fg="#00D4FF", bg="#1E1E1E", font=("Arial", 14, "bold")).pack(pady=10)

# 🔐 Classe para Gerenciamento de Registro
class RegisterScreen:
    @staticmethod
    def registrar():
        usuario = simpledialog.askstring("Registro", "Escolha um nome de usuário:")
        senha = simpledialog.askstring("Registro", "Crie uma senha:", show="*")
        key = simpledialog.askstring("Registro", "Digite sua KEY de acesso:")

        # Validar a chave com o servidor
        success, message = ativar_chave_com_servidor(key, obter_identificadores_hardware())
        if not success:
            messagebox.showerror("Erro", f"⚠️ {message}")
            return None

        messagebox.showinfo("Sucesso", "✅ Conta criada com sucesso!")
        return usuario

# 🎮 Classe do Botão de Registrar
class RegisterButton:
    def __init__(self, frame, command):
        self.frame = frame
        self.command = command
        self.criar_botao()

    def criar_botao(self):
        tk.Button(self.frame, text="📝 Registrar", fg="black", bg="#55FFD9", font=("Arial", 12, "bold"),
                  command=self.command, width=25, height=1, relief="ridge", bd=3).pack(pady=10)

# 🎨 Classe do Menu Principal
class MainMenu:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        self.tela_login()

    def tela_login(self):
        self.login_frame = tk.Frame(self.root, bg="#1E1E1E")
        self.login_frame.pack(fill="both", expand=True)
        VisualManager.carregar_fundo(self.login_frame)
        VisualManager.carregar_logo(self.login_frame)
        tk.Label(
            self.login_frame,
            text="MILGRAU SHOP - SPOOFER 1 CLICK",
            fg="#00D4FF",
            bg="#1E1E1E",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)
        tk.Button(
            self.login_frame,
            text="🔑 Login",
            fg="white",
            bg="#00D4FF",
            font=("Arial", 12, "bold"),
            command=self.fazer_login,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)
        RegisterButton(self.login_frame, self.fazer_registro)
        tk.Button(
            self.login_frame,
            text="💬 Suporte no Discord",
            fg="white",
            bg="#5865F2",
            font=("Arial", 12, "bold"),
            command=InfoManager.abrir_discord,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)

    def fazer_login(self):
        usuario = simpledialog.askstring("Login", "Digite seu nome de usuário:")
        senha = simpledialog.askstring("Login", "Digite sua senha:", show="*")
        success, message = validar_chave_com_servidor(usuario, obter_identificadores_hardware())
        if not success:
            messagebox.showerror("Erro", f"⚠️ {message}")
            return
        messagebox.showinfo("Sucesso", "✅ Login realizado com sucesso!")
        self.app.usuario_logado = usuario
        self.root.destroy()
        self.app.abrir_tela_spoofing()

    def fazer_registro(self):
        usuario = RegisterScreen.registrar()
        if usuario:
            self.fazer_login()

# 🎨 Classe do Menu do Spoofer
class SpooferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MILGRAU SHOP - SPOOFER 1 CLICK")
        self.root.geometry("700x500")
        # Carrega APENAS o fundo (sem a logo aqui)
        VisualManager.carregar_fundo(self.root)
        # Inicializa o menu principal
        self.main_menu = MainMenu(root, self)

    def abrir_tela_spoofing(self):
        spoof_window = tk.Tk()
        spoof_window.title("Menu do Spoofer")
        spoof_window.geometry("700x500")
        spoof_frame = tk.Frame(spoof_window, bg="#1E1E1E")
        spoof_frame.pack(fill="both", expand=True)
        # Carregar APENAS o fundo (sem o logo)
        VisualManager.carregar_fundo(spoof_frame)
        tk.Label(
            spoof_frame,
            text="Tela de Spoofer",
            fg="#00D4FF",
            bg="#1E1E1E",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)
        # Botão Guia de Desvinculação (em primeiro lugar)
        tk.Button(
            spoof_frame,
            text="📖 Guia de Desvinculação",
            fg="white",
            bg="#FFA500",
            font=("Arial", 12, "bold"),
            command=self.mostrar_guia,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)
        # Botão Spoofar
        tk.Button(
            spoof_frame,
            text="🚀 Spoofar com Um Clique",
            fg="white",
            bg="#FF4500",
            font=("Arial", 12, "bold"),
            command=self.spoofar_completo,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)
        # Botão Voltar ao Menu
        tk.Button(
            spoof_frame,
            text="Voltar ao Menu",
            fg="white",
            bg="#00D4FF",
            font=("Arial", 12, "bold"),
            command=spoof_window.destroy,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)
        spoof_window.mainloop()

    def spoofar_completo(self):
        # Função para gerar um novo MAC Address aleatório
        def gerar_mac():
            return "02:" + ":".join(["%02x" % random.randint(0, 255) for _ in range(5)])

        # Função para alterar MAC Address
        def mudar_mac():
            try:
                novo_mac = gerar_mac()
                interface = "Wi-Fi"  # Altere para "Ethernet" se necessário
                subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=disable"], check=True)
                subprocess.run(["netsh", "interface", "set", "interface", interface, "admin=enable"], check=True)
                messagebox.showinfo("Sucesso", f"✅ MAC Address alterado para: {novo_mac}")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Falha ao mudar MAC Address: {e}")

        # Função para limpar cache e logs do FiveM
        def limpar_cache_fivem():
            try:
                caminhos = [
                    os.path.expandvars(r"%localappdata%\FiveM\FiveM.app\cache"),
                    os.path.expandvars(r"%localappdata%\FiveM\logs"),
                    os.path.expandvars(r"%appdata%\CitizenFX"),
                ]
                for caminho in caminhos:
                    if os.path.exists(caminho):
                        shutil.rmtree(caminho, ignore_errors=True)
                messagebox.showinfo("Sucesso", "✅ Cache e logs do FiveM removidos!")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Falha ao limpar cache: {e}")

        # Função para criar novo usuário do Windows
        def criar_novo_usuario():
            try:
                novo_usuario = "SpoofUser"
                senha = "Spoof1234"
                subprocess.run(["net", "user", novo_usuario, senha, "/add"], check=True)
                messagebox.showinfo("Sucesso", f"✅ Novo usuário criado: {novo_usuario} | Senha: {senha}")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Falha ao criar novo usuário: {e}")

        # Função para mudar o endereço IP
        def mudar_ip():
            try:
                resposta = requests.get("https://api64.ipify.org?format=json").json()
                ip_antigo = resposta["ip"]
                # Reiniciando conexão de rede
                subprocess.run(["ipconfig", "/release"], check=True)
                subprocess.run(["ipconfig", "/flushdns"], check=True)
                subprocess.run(["ipconfig", "/renew"], check=True)
                time.sleep(5)  # Aguarda mudança de IP
                resposta = requests.get("https://api64.ipify.org?format=json").json()
                ip_novo = resposta["ip"]
                if ip_antigo != ip_novo:
                    messagebox.showinfo("Sucesso", f"✅ IP alterado com sucesso! Novo IP: {ip_novo}")
                else:
                    messagebox.showinfo("Atenção", "⚠️ O IP não mudou. Tente usar uma VPN.")
            except Exception as e:
                messagebox.showerror("Erro", f"❌ Falha ao mudar IP: {e}")

        # Executar todas as funções de spoofing
        mudar_mac()
        limpar_cache_fivem()
        mudar_ip()
        criar_novo_usuario()
        messagebox.showinfo("Concluído", "✅ Spoofing concluído! Reinicie o PC antes de abrir o FiveM.")

    def mostrar_guia(self):
        guia_texto = """DESVINCULAÇÕES
DESVINCULAR CONTA WINDOWS
Passo 1: Pressione a tecla Win e clique no seu usuário.
Passo 2: Selecione Change account settings.
Passo 3: Verifique se há um e-mail abaixo do seu nome.
Passo 4: Se houver um e-mail, mude para uma Conta Local.
Passo 5: Vá em E-mails e Contas e remova a conta de e-mail.
DESVINCULAR FIVEM DO DISCORD
Passo 1: Abra o Discord.
Passo 2: Vá até as Configurações.
Passo 3: Clique em Aplicativos Autorizados.
Passo 4: Procure por "FiveM".
Passo 5: Se encontrar, remova a autorização clicando em "Desautorizar".
:Sinfo: Quando você entrar no FiveM novamente, não autorize o Discord, caso seja solicitado.
DESVINCULAR EPIC
Passo 1: Acesse o aplicativo da Epic Games.
Passo 2: Vá em perfil.
Passo 3: Clique em sair (Sign Out).
DESVINCULAR STEAM
Passo 1: Acesse o aplicativo da Steam.
Passo 2: Vá em perfil.
Passo 3: Clique em sair (Sign Out).
DESINSTALAR A RIOT VANGUARD
Passo 1: Baixe e instale o Revo Uninstaller.
Passo 2: Abra o Revo Uninstaller.
Passo 3: Encontre o Vanguard na lista de programas e desinstale-o completamente."""
        messagebox.showinfo("Guia de Desvinculação", guia_texto)

# 🆘 Classe para Suporte
class InfoManager:
    @staticmethod
    def abrir_discord():
        webbrowser.open(DISCORD_LINK)

# Iniciar Aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = SpooferApp(root)
    root.mainloop()