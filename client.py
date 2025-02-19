import os
import json
import time
import requests
import webbrowser
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
from datetime import datetime, timedelta
import subprocess
import random
import shutil
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import base64
import ast
import secrets  # Importar a biblioteca secrets para geração de chaves seguras
import uuid  # Importar a biblioteca uuid para geração de UUIDs (opcional, mas útil)

load_dotenv()

# Configurações (usando variáveis de ambiente):
# SERVER_URL CORRIGIDO: Agora DEVE ser o endereço HTTP/HTTPS do SEU SERVIDOR WEB no Render.com!
SERVER_URL = os.environ.get("SERVER_URL") or "http://localhost:5000"  # <--- VALOR PADRÃO PARA TESTES LOCAIS! ALTERE PARA "https://seu-app.onrender.com" EM PRODUÇÃO!
DISCORD_LINK = os.environ.get("DISCORD_LINK") or "https://discord.gg/9Z5m4zk9"
LOGO_PATH = os.environ.get("LOGO_PATH") or "logo.png"
BACKGROUND_PATH = os.environ.get("BACKGROUND_PATH") or "background.png"

# Chave de criptografia (lida da variável de ambiente)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")
print("ENCRYPTION_KEY (lido do .env):", ENCRYPTION_KEY, type(ENCRYPTION_KEY))

if ENCRYPTION_KEY is None:
    raise ValueError("A variável de ambiente ENCRYPTION_KEY não está definida.")

# Usar ast.literal_eval para converter a string literal em bytes
ENCRYPTION_KEY_BYTES = ast.literal_eval(ENCRYPTION_KEY)
print("ENCRYPTION_KEY_BYTES:", ENCRYPTION_KEY_BYTES, type(ENCRYPTION_KEY_BYTES))
print("TAMANHO DE ENCRYPTION_KEY_BYTES (em bytes):", len(ENCRYPTION_KEY_BYTES))  # ADICIONE ESTA LINHA!

# Codifique a chave para URL-safe Base64
ENCRYPTION_KEY_ENCODED = base64.urlsafe_b64encode(ENCRYPTION_KEY_BYTES)
print("ENCRYPTION_KEY_ENCODED:", ENCRYPTION_KEY_ENCODED, type(ENCRYPTION_KEY_ENCODED))

cipher_suite = Fernet(ENCRYPTION_KEY_ENCODED)

# Função para obter identificadores únicos do hardware (HWID)
def obter_identificadores_hardware():
    try:
        # Obter UUID da placa-mãe
        uuid_hw = subprocess.check_output("wmic csproduct get UUID", shell=True).decode().split("\n")[1].strip()

        # Obter Serial Number do disco rígido
        serial_number = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True).decode().split("\n")[1].strip()

        # Obter MAC Address
        mac_output = subprocess.check_output("getmac /fo csv /nh", shell=True).decode()
        mac_address = mac_output.split(",")[0].strip().strip('"')  # Remove aspas extras
        mac_address = mac_address.replace("-", ":").upper()  # Formata o MAC Address

        return f"{uuid_hw}-{serial_number}-{mac_address}"
    except Exception as e:
        print(f"Erro ao obter identificadores de hardware: {e}")
        return None

# Funções para comunicação com o servidor (CORRIGIDAS para usar SERVER_URL HTTP!)
def ativar_chave_com_servidor(key, hwid, usuario):  # MODIFICADO: Aceita 'usuario'
    try:
        # URL CORRIGIDA: Usa SERVER_URL (HTTP/HTTPS) e endpoint /register
        response = requests.post(f"{SERVER_URL}/register", json={"key": key, "hwid": hwid, "username": usuario})  # MODIFICADO: Envia 'usuario' como 'username'
        response.raise_for_status()  # Verifica se houve erros HTTP na resposta
        data = response.json()
        return data["success"], data["message"]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao servidor (ativar_chave_com_servidor): {e}") # Mensagem de erro mais descritiva
        if e.response is not None:
            print(f"Resposta de erro do servidor (ativar_chave_com_servidor): {e.response.status_code} - {e.response.text}")
        return False, "Erro ao conectar ao servidor para registro." # Mensagem de erro mais clara
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da resposta (ativar_chave_com_servidor): {e}") # Mensagem de erro mais descritiva
        return False, "Erro ao processar resposta do servidor (JSON inválido no registro)." # Mensagem de erro mais clara

def validar_chave_com_servidor(usuario, hwid):  # MODIFICADO: 'key' agora é 'usuario' para login
    try:
        # URL CORRIGIDA: Usa SERVER_URL (HTTP/HTTPS) e endpoint /validate_key (corrigido no server.py)
        response = requests.post(f"{SERVER_URL}/validate_key", json={"key": usuario, "hwid": hwid})  # MODIFICADO: Envia 'usuario' como 'key'
        response.raise_for_status()  # Verifica se houve erros HTTP na resposta
        data = response.json()
        return data["success"], data["message"]
    except requests.exceptions.RequestException as e:
        print(f"Erro ao conectar ao servidor (validar_chave_com_servidor): {e}") # Mensagem de erro mais descritiva
        if e.response is not None:
            print(f"Resposta de erro do servidor (validar_chave_com_servidor): {e.response.status_code} - {e.response.text}")
        return False, "Erro ao conectar ao servidor para login." # Mensagem de erro mais clara
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON da resposta (validar_chave_com_servidor): {e}") # Mensagem de erro mais descritiva
        return False, "Erro ao processar resposta do servidor (JSON inválido no login)." # Mensagem de erro mais clara

# Função para testar a conexão com o servidor (CORRIGIDA para usar SERVER_URL HTTP!)
def testar_conexao_servidor():
    try:
        # URL CORRIGIDA: Usa SERVER_URL (HTTP/HTTPS) e endpoint /ping
        response = requests.get(f"{SERVER_URL}/ping", timeout=5)  # Timeout para evitar travamentos
        response.raise_for_status()  # Lança exceção para erros HTTP (4xx, 5xx)
        data = response.json()
        if data.get("status") == "ok":
            messagebox.showinfo("Conexão", "✅ Conexão com o servidor estabelecida com sucesso!")
        else:
            messagebox.showerror("Erro de Conexão", f"⚠️ Resposta do servidor inesperada: {data}")
    except requests.exceptions.RequestException as e:
        messagebox.showerror("Erro de Conexão", f"❌ Falha ao conectar com o servidor: {e}") # Mensagem de erro mais clara
        print(f"Erro detalhado ao testar_conexao_servidor: {e}") # Log detalhado para debugging
    except json.JSONDecodeError as e:
        messagebox.showerror("Erro de Conexão", f"❌ Resposta do servidor inválida (não é JSON): {e}") # Mensagem de erro mais clara
        print(f"Erro JSON ao testar_conexao_servidor: {e}") # Log detalhado para debugging
    except Exception as e:
        messagebox.showerror("Erro de Conexão", f"❌ Erro inesperado ao testar conexão: {e}") # Mensagem de erro mais clara
        print(f"Erro inesperado em testar_conexao_servidor: {e}") # Log detalhado para debugging

# Classe para Interface Visual
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

# Classe para Gerenciamento de Registro
class RegisterScreen:
    @staticmethod
    def registrar():
        usuario = simpledialog.askstring("Registro", "Escolha um nome de usuário:")  # Captura o nome de usuário
        senha = simpledialog.askstring("Registro", "Crie uma senha:", show="*")  # (Pode ou não usar senha - depende da sua lógica)
        key = simpledialog.askstring("Registro", "Digite sua KEY de acesso:")
        hwid = obter_identificadores_hardware()  # Obtém o HWID

        # Validar a chave com o servidor, enviando usuario e hwid
        success, message = ativar_chave_com_servidor(key, hwid, usuario)  # MODIFICADO: Envia usuario agora
        if not success:
            messagebox.showerror("Erro", f"⚠️ {message}")
            return None

        messagebox.showinfo("Sucesso", "✅ Conta criada com sucesso!")
        return usuario

# Classe do Botão de Registrar
class RegisterButton:
    def __init__(self, frame, command):
        self.frame = frame
        self.command = command
        self.criar_botao()

    def criar_botao(self):
        tk.Button(
            self.frame,
            text="📝 Registrar",
            fg="black",
            bg="#55FFD9",
            font=("Arial", 12, "bold"),
            command=self.command,
            width=25,
            height=1,
            relief="ridge",
            bd=3
        ).pack(pady=10)

# Classe do Menu Principal
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
            text="MIL GRAU SHOP - SPOOFER 1 CLICK",
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
            bd=3
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
        tk.Button(  # Botão "Testar Conexão" adicionado aqui
            self.login_frame,
            text="Testar Conexão",
            fg="white",
            bg="#00D4FF",
            font=("Arial", 12, "bold"),
            command=testar_conexao_servidor,
            width=25,
            height=1,
            relief="ridge",
            bd=3
        ).pack(pady=10)

    def fazer_login(self):
        usuario = simpledialog.askstring("Login", "Digite seu nome de usuário:")  # MODIFICADO: Usar nome de usuário como "key"
        senha = simpledialog.askstring("Login", "Digite sua senha:", show="*")  # (Pode ou não usar senha - depende da sua lógica)
        hwid = obter_identificadores_hardware()

        # ADMIN LOGIN - REMOVER ISSO EM PRODUÇÃO POR SEGURANÇA!!!
        if usuario == "socafofoh" and senha == "Chamego321":
            messagebox.showinfo("Sucesso", "✅ Login de ADMIN realizado com sucesso!")
            self.app.usuario_logado = usuario
            self.root.destroy()
            self.app.abrir_tela_spoofing()
            return

        success, message = validar_chave_com_servidor(usuario, hwid)  # MODIFICADO: Envia 'usuario' para validação
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

# Classe do Menu do Spoofer
class SpooferApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MILGRAU SHOP - SPOOFER 1 CLICK")
        self.root.geometry("700x500")
        VisualManager.carregar_fundo(self.root)
        self.main_menu = MainMenu(root, self)
        self.usuario_logado = None  # Inicializa usuario_logado

    def abrir_tela_spoofing(self):
        spoof_window = tk.Tk()
        spoof_window.title("Menu do Spoofer")
        spoof_window.geometry("700x500")
        spoof_frame = tk.Frame(spoof_window, bg="#1E1E1E")
        spoof_frame.pack(fill="both", expand=True)
        VisualManager.carregar_fundo(spoof_frame)
        tk.Label(
            spoof_frame,
            text=f"Tela de Spoofer - Logado como: {self.usuario_logado}",  # Exibe o usuário logado
            fg="#00D4FF",
            bg="#1E1E1E",
            font=("Arial", 14, "bold"),
        ).pack(pady=10)
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
        tk.Button(  # Botão "Gerar Chaves de Acesso" adicionado aqui
            spoof_frame,
            text="Gerar Chaves de Acesso",
            fg="white",
            bg="#55FFD9",
            font=("Arial", 12, "bold"),
            command=self.gerar_chave_acesso,
            width=25,
            height=1,
            relief="ridge",
            bd=3,
        ).pack(pady=10)

        spoof_window.mainloop()

    def gerar_chave_acesso(self):
        quantidade_chaves = simpledialog.askinteger("Gerar Chaves", "Quantas chaves deseja gerar?", minvalue=1, initialvalue=1)
        if quantidade_chaves is None:  # Usuário cancelou
            return

        chaves_geradas = []
        for _ in range(quantidade_chaves):
            # Gerar chave usando secrets.token_urlsafe (mais seguro e URL-safe)
            chave = secrets.token_urlsafe(32)  # 32 bytes = 43 caracteres base64 URL-safe
            chaves_geradas.append(chave)

        texto_chaves = "\n".join(chaves_geradas)  # Juntar as chaves com quebras de linha
        messagebox.showinfo("Chaves Geradas", f"Chaves de Acesso Geradas:\n\n{texto_chaves}")  # Mostrar em messagebox

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

        # Função para mudar o endereço IP (melhorada)
        def mudar_ip():
            try:
                # Tenta obter o IP externo usando várias APIs
                apis = ["https://api64.ipify.org?format=json", "https://ifconfig.me/ip", "https://ipinfo.io/ip"]
                for api in apis:
                    try:
                        response = requests.get(api, timeout=5)  # Timeout para evitar travamentos
                        response.raise_for_status()  # Verifica se a resposta foi bem sucedida
                        if api == "https://api64.ipify.org?format=json":
                            ip_info = response.json()
                            ip_antigo = ip_info["ip"]
                        elif api == "https://ifconfig.me/ip":
                            ip_antigo = response.text.strip()
                        elif api == "https://ipinfo.io/ip":
                            ip_antigo = response.text.strip()
                        break  # Sai do loop se o IP for obtido com sucesso
                    except requests.exceptions.RequestException as e:
                        print(f"Erro ao obter IP de {api}: {e}")
                else:  # Executado se o loop terminar sem obter o IP
                    raise Exception("Não foi possível obter o IP externo usando nenhuma API.")

                # ... (resto da lógica para mudar o IP, como antes - você pode adicionar aqui se necessário)
                messagebox.showinfo("Sucesso", f"✅ Tentativa de mudar o IP realizada! (Verifique seu IP)")  # Mensagem genérica, você pode refinar
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

# Classe para Suporte
class InfoManager:
    @staticmethod
    def abrir_discord():
        webbrowser.open(DISCORD_LINK)

# Iniciar Aplicação
if __name__ == "__main__":
    root = tk.Tk()
    app = SpooferApp(root)
    root.mainloop()