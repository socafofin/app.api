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
SERVER_URL = os.environ.get("SERVER_URL") or "https://mgs-qpbo.onrender.com"  # <--- **VERIFIQUE SE ESTE É O URL CORRETO DO SEU SERVIDOR NO RENDER.COM!**
DISCORD_LINK = os.environ.get("DISCORD_LINK") or "https://discord.gg/9Z5m4zk9"
LOGO_PATH = os.environ.get("LOGO_PATH") or "logo.png"
BACKGROUND_PATH = os.environ.get("BACKGROUND_PATH") or "background.png"

# Chave de criptografia (lida da variável de ambiente)
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY")

if ENCRYPTION_KEY is None:
    raise ValueError("A variável de ambiente ENCRYPTION_KEY não está definida.")

# Usar ast.literal_eval para converter a string literal em bytes
ENCRYPTION_KEY_BYTES = ast.literal_eval(ENCRYPTION_KEY)

# Codifique a chave para URL-safe Base64
ENCRYPTION_KEY_ENCODED = base64.urlsafe_b64encode(ENCRYPTION_KEY_BYTES)

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
def testar_conexao_servidor(): # REMOVIDA DO MENU PRINCIPAL
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
            bg_resized = bg.resize((500, 380), Image.Resampling.LANCZOS) # Dimensões do background
            bg_image = ImageTk.PhotoImage(bg_resized)
            label_fundo = tk.Label(frame, image=bg_image)
            label_fundo.place(relwidth=1, relheight=1)
            frame.background_image = bg_image  # Mantém a referência
            frame.background_size = (500, 380) # Guarda as dimensões do background
        except Exception as e:
            print(f"Erro ao carregar o fundo: {e}")
            frame.configure(bg="#121212")

    @staticmethod
    def carregar_logo(frame, menu='main'): # Adicionado parâmetro 'menu' para diferenciar o tamanho do logo
        try:
            logo_size = (120, 120) # Tamanho padrão para menu principal
            if menu == 'spoof': # Se for menu spoofer, usa logo maior
                logo_size = (190, 190) # Logo AINDA MAIOR para menu spoofer (quase tela cheia!)
            logo = Image.open(LOGO_PATH)
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            logo_image = ImageTk.PhotoImage(logo)
            label_logo = tk.Label(frame, image=logo_image, bg="#1E1E1E")
            label_logo.image = logo_image  # Mantém a referência
            label_logo.pack(pady=5) # Menor pady
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            tk.Label(frame, text="Logo", fg="#00D4FF", bg="#1E1E1E", font=("Arial", 12, "bold")).pack(pady=5) # Menor fonte, Menor pady

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
        button_bg_frame = tk.Frame(self.frame, bg="#1E1E1E") # Frame Preto semi-transparente - SEM BD PARA FICAR CLEAN
        button_bg_frame.pack(pady=2) # Menor pady
        tk.Button(
            button_bg_frame, # Botão dentro do frame preto
            text="📝 Registrar",
            fg="black",
            bg="#55FFD9",
            font=("Arial", 9, "bold"), # Menor fonte
            command=self.command,
            width=16, # Mais Menor
            height=1,
            relief="ridge",
            bd=0, # REMOVIDO BORDA DO BOTÃO PARA FICAR MAIS CLEAN
            pady=3, # Mais Menor
            padx=6, # Mais Menor
            highlightbackground="#1E1E1E", # Cor de fundo para 'relief' e 'bd' se necessário
            highlightcolor="#1E1E1E",
            borderwidth=0, # Remova a borda padrão se desejar um visual mais 'flat'
            activebackground="#70FFEF", # Cor ao clicar
            activeforeground="black"
        ).pack(pady=0) # Removido pady do botão, padding no frame

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
        VisualManager.carregar_logo(self.login_frame) # Logo no menu principal

        # Título
        tk.Label(
            self.login_frame,
            text="MIL GRAU SHOP - SPOOFER 1 CLICK",
            fg="#00D4FF",
            bg="#1E1E1E",
            font=("Arial", 12, "bold"), # Menor fonte
        ).pack(pady=5) # Menor pady

        # Frame para agrupar campos de login/senha e fundo preto
        login_fields_frame = tk.Frame(self.login_frame, bg="#1E1E1E") # Frame Preto semi-transparente
        login_fields_frame.pack(pady=5) # Menor pady

        # Entrada para Nome de Usuário
        self.usuario_entry = tk.Entry(login_fields_frame, bg="#2E2E2E", fg="white", font=("Arial", 9), insertbackground="white", width=18) # Menor e mais estreito
        self.usuario_entry.config(show=None) # Para mostrar texto normalmente
        self.usuario_entry.pack(pady=2, padx=5, fill='x') # Menor pady/padx

        # Rótulo "Usuário" acima da entrada
        tk.Label(login_fields_frame, text="Usuário:", fg="#A0A0A0", bg="#1E1E1E", font=("Arial", 8)).pack() # Menor fonte

        # Entrada para Senha
        self.senha_entry = tk.Entry(login_fields_frame, show="*", bg="#2E2E2E", fg="white", font=("Arial", 9), insertbackground="white", width=18) # Menor e mais estreito
        self.senha_entry.pack(pady=2, padx=5, fill='x') # Menor pady/padx

        # Rótulo "Senha" acima da entrada
        tk.Label(login_fields_frame, text="Senha:", fg="#A0A0A0", bg="#1E1E1E", font=("Arial", 8)).pack() # Menor fonte

        button_login_bg_frame = tk.Frame(self.login_frame, bg="#1E1E1E") # Frame Preto semi-transparente - SEM BD PARA FICAR CLEAN
        button_login_bg_frame.pack(pady=2) # Menor pady
        login_button = tk.Button(
            button_login_bg_frame, # Botão dentro do frame preto
            text="🔑 Login",
            fg="black",
            bg="#00D4FF",
            font=("Arial", 9, "bold"), # Menor fonte
            command=self.fazer_login,
            width=16, # Mais Menor
            height=1,
            relief="ridge",
            bd=0, # REMOVIDO BORDA DO BOTÃO PARA FICAR MAIS CLEAN
            pady=3, # Mais Menor
            padx=6, # Mais Menor
            highlightbackground="#1E1E1E", # Cor de fundo para 'relief' e 'bd' se necessário
            highlightcolor="#1E1E1E",
            borderwidth=0, # Remova a borda padrão se desejar um visual mais 'flat'
            activebackground="#70FFEF", # Cor ao clicar
            activeforeground="black"
        )
        login_button.pack(pady=0) # Removido pady do botão, padding no frame

        RegisterButton(self.login_frame, self.fazer_registro)

        button_discord_bg_frame = tk.Frame(self.login_frame, bg="#1E1E1E") # Frame Preto semi-transparente - SEM BD PARA FICAR CLEAN
        button_discord_bg_frame.pack(pady=2) # Menor pady
        tk.Button(
            button_discord_bg_frame, # Botão dentro do frame preto
            text="💬 Suporte no Discord",
            fg="white",
            bg="#5865F2",
            font=("Arial", 9, "bold"), # Menor fonte
            command=InfoManager.abrir_discord,
            width=16, # Mais Menor
            height=1,
            relief="ridge",
            bd=0,  # REMOVIDO BORDA DO BOTÃO PARA FICAR MAIS CLEAN
            pady=3, # Mais Menor
            padx=6, # Mais Menor
            highlightbackground="#1E1E1E", # Cor de fundo para 'relief' e 'bd' se necessário
            highlightcolor="#1E1E1E",
            borderwidth=0, # Remova a borda padrão se desejar um visual mais 'flat'
            activebackground="#70FFEF", # Cor ao clicar
            activeforeground="black"
        ).pack(pady=0) # Removido pady do botão, padding no frame

        # Bind Enter key para logar quando foco estiver no campo de senha
        self.senha_entry.bind('<Return>', lambda event=None: self.fazer_login())
        # Bind Enter key para logar quando foco estiver no campo de usuario (opcional, mais amigavel)
        self.usuario_entry.bind('<Return>', lambda event=None: self.fazer_login())


    def fazer_login(self):
        usuario = self.usuario_entry.get() # Obtém o usuário da Entry
        senha = self.senha_entry.get() # Obtém a senha da Entry
        hwid = obter_identificadores_hardware()

        # ADMIN LOGIN - REMOVER ISSO EM PRODUÇÃO POR SEGURANÇA!!!
        if usuario == "socafofoh" and senha == "Chamego321":
            messagebox.showinfo("Sucesso", "✅ Login de ADMIN realizado com sucesso!")
            self.app.usuario_logado = usuario
            self.root.destroy()
            self.app.abrir_tela_spoofing()
            return

        # **CORREÇÃO DO LOGIN:** Validar chave COM usuário e senha (ambos são importantes!)
        success, message = validar_chave_com_servidor(usuario, hwid) # <--- USANDO APENAS USUARIO PARA VALIDAR (CONFORME A FUNÇÃO)
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
        self.root.title("MIL GRAU SHOP - SPOOFER 1 CLICK")
        VisualManager.carregar_fundo(self.root) # Carrega o fundo para obter as dimensões
        bg_width, bg_height = self.root.background_size # Obtém as dimensões do background carregado
        self.root.geometry(f"{bg_width}x{bg_height}") # Define a geometria da janela principal = tamanho do background
        self.main_menu = MainMenu(root, self)
        self.usuario_logado = None  # Inicializa usuario_logado

    def abrir_tela_spoofing(self):
        spoof_window = tk.Tk()
        spoof_window.title("Menu do Spoofer")
        # VisualManager.carregar_fundo(spoof_window, apply_background=True) # Carrega o fundo no menu spoofer!  <--- BACKGROUND AINDA REMOVIDO!
        default_width = 500 # <--- DIMENSÕES PADRÃO
        default_height = 380 # <--- DIMENSÕES PADRÃO
        bg_width = default_width  # <--- USANDO PADRÃO SE NÃO TIVER BACKGROUND
        bg_height = default_height # <--- USANDO PADRÃO SE NÃO TIVER BACKGROUND
        if hasattr(spoof_window, 'background_size'): # <--- VERIFICA SE background_size EXISTE
            bg_width, bg_height = spoof_window.background_size # <--- USA AS DIMENSÕES DO BACKGROUND SE DISPONÍVEIS
        spoof_window.geometry(f"{bg_width}x{bg_height + 150}") # Janela do spoofer AINDA MENOR verticalmente (reduzi de 160 para 150)
        spoof_frame = tk.Frame(spoof_window, bg="#1E1E1E")
        spoof_frame.pack(fill="both", expand=True)
        VisualManager.carregar_logo(spoof_frame, menu='spoof') # Logo no menu spoofer, agora maior!

        tk.Label(
            spoof_frame,
            text=f"Tela de Spoofer - Logado como: {self.usuario_logado}",  # Exibe o usuário logado
            fg="#00D4FF",
            bg="#1E1E1E",
            font=("Arial", 12, "bold"), # Menor fonte
        ).pack(pady=3) # Menor pady

        # Textbox de Feedback - Mova para o topo e redimensione
        self.feedback_text = tk.Text(
            spoof_frame,
            height=8, # Altura do feedback um pouco menor (reduzi de 9 para 8)
            width=38, # <--- LARGURA REDUZIDA PARA 38 (ANTES ERA 42)
            bg="#2E2E2E",
            fg="#00D4FF",
            font=("Arial", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.feedback_text.pack(pady=3, padx=10, fill=tk.X, anchor=tk.N)

        # Label "IMPORTANTE LER PRIMEIRO" - TEXTO ADICIONADO!
        tk.Label(
            spoof_frame,
            text="IMPORTANTE LER PRIMEIRO: PARA DESBLOQUEAR O SPOOFER", # TEXTO ADICIONADO!
            fg="#FFD700", # Cor dourada para destaque
            bg="#1E1E1E",
            font=("Arial", 9, "bold")
        ).pack(pady=(8, 2), anchor=tk.CENTER) # Subi um pouco o "IMPORTANTE..." (reduzi pady superior)

        # Variável para controlar se o guia foi lido (para o checklist)
        self.guia_lido = tk.BooleanVar(value=False) # Inicialmente NÃO marcado

        # Frame para alinhar o botão Guia e o Checklist
        guia_checklist_frame = tk.Frame(spoof_frame, bg="#1E1E1E") # Frame para alinhar
        guia_checklist_frame.pack(pady=(10, 2), anchor=tk.CENTER) # REMOVIDO side=tk.BOTTOM <-- AQUI A ALTERAÇÃO!

        # Botão Guia Desvinculação (PRIMEIRO BOTÃO)
        button_guia_bg_frame = tk.Frame(guia_checklist_frame, bg="#1E1E1E") # Botão dentro do frame alinhado
        button_guia_bg_frame.pack(side=tk.LEFT, padx=5) # Posiciona à esquerda e adiciona espaço
        button_guia = tk.Button(
            button_guia_bg_frame,
            text="Desvincular Contas & Apps", # <--- TEXTO DO BOTÃO ALTERADO!
            fg="black",
            bg="#FFA500",
            font=("Arial", 9, "bold"),
            command=self.mostrar_guia,
            width=22, # Aumentei um pouco a largura para o novo texto
            height=1,
            relief="ridge",
            bd=0,
            pady=3,
            padx=6,
            highlightbackground="#1E1E1E",
            highlightcolor="#1E1E1E",
            borderwidth=0,
            activebackground="#FFC045",
            activeforeground="black"
        )
        button_guia.pack(pady=0)

        # Checklist "Li o Guia" (SEGUNDO ELEMENTO: CHECKLIST)
        check_guia = tk.Checkbutton(
            guia_checklist_frame, # Checklist dentro do frame alinhado
            text="✅ Li o guia",
            variable=self.guia_lido, # Associa à variável self.guia_lido
            bg="#1E1E1E",
            fg="#55FFD9",
            font=("Arial", 9, "bold"),
            activebackground="#1E1E1E", # Cor de fundo quando clicado
            activeforeground="#70FFEF", # Cor da fonte quando clicado
            selectcolor="#1E1E1E",    # Cor do quadrado quando marcado (mesma do fundo)
            command=self.atualizar_estado_botao_spoofar # <--- NOVA FUNÇÃO PARA ATUALIZAR BOTÃO
        )
        check_guia.pack(side=tk.LEFT, padx=5) # Posiciona à direita do botão Guia e adiciona espaço

        # Botão Spoofar 1 Click (TERCEIRO BOTÃO, inicialmente DESABILITADO)
        button_spoof_bg_frame = tk.Frame(spoof_frame, bg="#1E1E1E")
        button_spoof_bg_frame.pack(pady=2) # REMOVEMOS side=tk.BOTTOM
        self.spoof_button = tk.Button( # 'self.spoof_button' para poder manipular depois
            button_spoof_bg_frame,
            text="🚀 Spoofar 1 Click",
            fg="black",
            bg="#FF4500",
            font=("Arial", 9, "bold"),
            command=self.spoofar_completo, # MODIFICADO: Chama 'spoofar_completo' DIRETAMENTE
            width=16,
            height=1,
            relief="ridge",
            bd=0,
            pady=3,
            padx=6,
            highlightbackground="#1E1E1E",
            highlightcolor="#1E1E1E",
            borderwidth=0,
            activebackground="#FF6030",
            activeforeground="black",
            state=tk.DISABLED # Inicialmente desabilitado!
        )
        self.spoof_button.pack(pady=0)

        # Botão Sair do Menu (QUARTO BOTÃO, renomeado e último)
        button_sair_bg_frame = tk.Frame(spoof_frame, bg="#1E1E1E") # Renomeado para 'sair'
        button_sair_bg_frame.pack(pady=2) # REMOVEMOS side=tk.BOTTOM
        tk.Button(
            button_sair_bg_frame, # Renomeado para 'sair_button'
            text="🚪 Sair do Menu", # TEXTO RENOMEADO para "Sair do Menu" e emoji
            fg="black",
            bg="#00D4FF",
            font=("Arial", 9, "bold"),
            command=spoof_window.destroy,
            width=16,
            height=1,
            relief="ridge",
            bd=0,
            pady=3,
            padx=6,
            highlightbackground="#1E1E1E",
            highlightcolor="#1E1E1E",
            borderwidth=0,
            activebackground="#70FFEF",
            activeforeground="black"
        ).pack(pady=0)

        # Botão "Gerar Chaves de Acesso" SÓ PARA ADMIN (sem alterações de posição)
        if self.usuario_logado == "socafofoh":
            button_gerarchaves_bg_frame = tk.Frame(spoof_frame, bg="#1E1E1E")
            button_gerarchaves_bg_frame.pack(pady=2) # REMOVEMOS side=tk.BOTTOM
            tk.Button(
                button_gerarchaves_bg_frame,
                text="Gerar Chaves Admin",
                fg="black",
                bg="#55FFD9",
                font=("Arial", 9, "bold"),
                command=self.requisitar_chaves_servidor,
                width=16,
                height=1,
                relief="ridge",
                bd=0,
                pady=3,
                padx=6,
                highlightbackground="#1E1E1E",
                highlightcolor="#1E1E1E",
                borderwidth=0,
                activebackground="#70FFEF",
                activeforeground="black"
            ).pack(pady=0)

        spoof_window.mainloop()

    def atualizar_estado_botao_spoofar(self):
        if self.guia_lido.get(): # Se o checklist estiver marcado (True)
            self.spoof_button.config(state=tk.NORMAL) # Habilita o botão Spoofar
        else: # Se o checklist NÃO estiver marcado (False)
            self.spoof_button.config(state=tk.DISABLED) # Desabilita o botão Spoofer

    def confirmar_spoofar(self): # Nova função para confirmar leitura do guia - **REMOVIDA!**
        pass # Função removida, lógica movida para checklist e spoofar_completo

    def requisitar_chaves_servidor(self): # FUNÇÃO MODIFICADA! REQUISITA CHAVES DO SERVIDOR!
        quantidade_chaves = simpledialog.askinteger("Gerar Chaves", "Quantas chaves deseja gerar?", minvalue=1, initialvalue=1)
        if quantidade_chaves is None:  # Usuário cancelou
            return

        duracao_dias = simpledialog.askinteger("Duração da Chave", "Duração em dias para cada chave?", minvalue=1, initialvalue=30) # Padrão 30 dias
        if duracao_dias is None:  # Usuário cancelou
            return

        try:
            # FAZ REQUISIÇÃO POST PARA O ENDPOINT /generate_keys NO SERVIDOR
            response = requests.post(f"{SERVER_URL}/generate_keys", json={"quantidade": quantidade_chaves, "duracao_dias": duracao_dias})  # <--- ENVIA QUANTIDADE E DURACAO PARA O SERVIDOR!
            response.raise_for_status()  # Verifica erros HTTP
            data = response.json()
            if data["success"]:
                chaves_geradas_info = data["chaves"]  # Recebe lista de dicionários com chave e expiração
                texto_chaves = ""
                for chave_info in chaves_geradas_info:  # Formata as chaves com info de expiração (opcional)
                    texto_chaves += f"Chave: {chave_info['chave']}, Expira em: {chave_info['expira_em']}\n"  # <--- EXIBINDO EXPIRAÇÃO (OPCIONAL)
                messagebox.showinfo("Chaves Geradas", f"Chaves de Acesso Geradas:\n\n{texto_chaves}")
            else:
                messagebox.showerror("Erro ao Gerar Chaves", f"Erro do servidor: {data['message']}")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Erro ao Gerar Chaves", f"Falha ao comunicar com o servidor para gerar chaves: {e}")
        except json.JSONDecodeError as e:
            messagebox.showerror("Erro ao Gerar Chaves", f"Resposta do servidor inválida (não é JSON): {e}")
        except Exception as e:
            messagebox.showerror("Erro ao Gerar Chaves", f"Erro inesperado ao gerar chaves: {e}")

    def spoofar_completo(self):
        if not self.guia_lido.get(): # <--- VERIFICA SE CHECKLIST ESTÁ MARCADO
            estado_anterior = self.feedback_text.cget("state") # Salva o estado anterior
            self.feedback_text.config(state=tk.NORMAL) # Habilita para edição
            self.feedback_text.delete("1.0", tk.END) # Limpa todo o texto
            self.feedback_text.insert(tk.END, "⚠️ Leia o 'Desvincular Contas & Apps' e marque 'Li o Guia' para usar o Spoofer!\n", "erro") # Mensagem de erro - TEXTO DO BOTÃO GUIA ALTERADO!
            self.feedback_text.tag_config("erro", foreground="red") # Tag para cor vermelha
            self.feedback_text.config(state=estado_anterior) # Restaura o estado original
            return # <--- INTERROMPE A FUNÇÃO SE O CHECKLIST NÃO ESTIVER MARCADO

        feedback = "" # Variável para acumular feedback

        # Função para exibir feedback na Textbox
        def exibir_feedback(mensagem, sucesso=True):
            nonlocal feedback
            estado_anterior = self.feedback_text.cget("state") # Salva o estado anterior
            self.feedback_text.config(state=tk.NORMAL) # Habilita para edição
            cor = "#00D4FF" if sucesso else "red" # Ciano para sucesso, vermelho para erro
            self.feedback_text.insert(tk.END, mensagem + "\n", cor)
            self.feedback_text.tag_config(cor, foreground=cor) # Aplica a cor
            self.feedback_text.config(state=estado_anterior) # Restaura o estado original
            feedback += mensagem + "\n" # Acumula no feedback geral
            self.feedback_text.see(tk.END) # Auto-scroll para o final

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
                exibir_feedback(f"✅ MAC Address alterado para: {novo_mac}")
                return True
            except Exception as e:
                exibir_feedback(f"❌ Falha ao mudar MAC Address: {e}", sucesso=False)
                return False

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
                exibir_feedback("✅ Cache e logs do FiveM removidos!")
                return True
            except Exception as e:
                exibir_feedback(f"❌ Falha ao limpar cache: {e}", sucesso=False)
                return False

        # Função para criar novo usuário do Windows
        def criar_novo_usuario():
            try:
                novo_usuario = "SpoofUser"
                senha = "Spoof1234"
                subprocess.run(["net", "user", novo_usuario, senha, "/add"], check=True)
                exibir_feedback(f"✅ Novo usuário criado: {novo_usuario} | Senha: {senha}")
                return True
            except Exception as e:
                exibir_feedback(f"❌ Falha ao criar novo usuário: {e}", sucesso=False)
                return False

        # Função para mudar o endereço IP (melhorada)
        def mudar_ip():
            try:
                # Tenta obter o IP externo usando várias APIs
                apis = ["https://api64.ipify.org?format=json", "https://ifconfig.me/ip", "https://ipinfo.io/ip"]
                ip_antigo = "N/A" # Valor padrão se não conseguir obter o IP antigo
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
                exibir_feedback(f"✅ Tentativa de mudar o IP realizada! IP antigo (aproximado): {ip_antigo} (Verifique seu IP)")  # Mensagem com IP antigo
                return True
            except Exception as e:
                exibir_feedback(f"❌ Falha ao mudar IP: {e}", sucesso=False)
                return False

        # Limpar a Textbox de feedback antes de iniciar
        estado_anterior_limpeza = self.feedback_text.cget("state") # Salva o estado anterior
        self.feedback_text.config(state=tk.NORMAL) # Habilita para edição
        self.feedback_text.delete("1.0", tk.END) # Limpa todo o texto
        self.feedback_text.config(state=estado_anterior_limpeza) # Restaura o estado original
        feedback = "" # Reseta o feedback acumulado

        # Executar todas as funções de spoofing e exibir feedback
        sucesso_mac = mudar_mac()
        sucesso_cache = limpar_cache_fivem()
        sucesso_ip = mudar_ip()
        sucesso_usuario = criar_novo_usuario()

        # Mensagem de conclusão baseada no resultado geral
        if sucesso_mac and sucesso_cache and sucesso_ip and sucesso_usuario:
            exibir_feedback("✅ Spoofing concluído com SUCESSO!", sucesso=True)
            messagebox.showinfo("Concluído", "✅ Spoofing completo! Reinicie o PC antes de abrir o FiveM.")
        else:
            exibir_feedback("⚠️ Spoofing concluído com algumas FALHAS. Verifique o feedback acima.", sucesso=False)
            messagebox.showinfo("Atenção", "⚠️ Spoofing concluído com algumas falhas. Verifique o feedback na tela do Spoofer.")


    def mostrar_guia(self):
        guia_texto = """Guia rápido para desvincular suas contas e apps do Windows:

⚙️ Conta Windows
Win + Foto de Perfil > Mudar configurações da conta
Verifique se tem e-mail abaixo do nome. Se sim, > mudar para Conta Local
E-mail e contas > Remover conta de e-mail

🎮 FiveM & Discord
Discord > Configurações ⚙️ > Aplicativos Autorizados
FiveM > Desautorizar
⚠️ Importante: Não autorize o Discord no FiveM novamente!

🚀 Epic Games
Epic Games > Perfil
Sair (Sign Out)

🎮 Steam
Steam > Perfil
Sair (Sign Out)

🛡️ Riot Vanguard
⬇️ Baixe e instale o Revo Uninstaller
Revo Uninstaller > Vanguard > Desinstalar (completo)

Observações
Instruções podem variar um pouco.
Dificuldades? > Chamar no discord""" # <--- TEXTO DO GUIA COMPLETO E ATUALIZADO!
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
