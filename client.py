import tkinter as tk
from tkinter import messagebox
import requests
import json  # Importe a biblioteca json
import subprocess
import platform  # Import para obter informações do sistema
import os # Import para funcionalidades do sistema operacional

class VisualManager: # Classe para gerenciar elementos visuais (cores, logo, fundo)
    @staticmethod
    def carregar_logo(parent, menu=None): # Carrega a logo, adaptado para menus
        caminho_logo = 'logo.png' # Caminho da logo
        try:
            if not os.path.exists(caminho_logo): # Verifica se o arquivo existe
                print(f"Erro: Arquivo de logo não encontrado em: {caminho_logo}") # Mensagem de erro se não encontrado
                return None # Retorna None em caso de falha ao carregar
            logo_img = tk.PhotoImage(file=caminho_logo) # Tenta carregar a imagem
            if menu == 'spoof': # Se for menu spoof, redimensiona para um tamanho maior
                logo_img = logo_img.zoom(2) # Aumenta 2x
                logo_img = logo_img.subsample(3) # Reduz para 2/3 do tamanho ampliado para suavizar
            logo_label = tk.Label(parent, image=logo_img, bg="#1E1E1E") # Label para exibir a logo, fundo igual ao do frame
            logo_label.image = logo_img # Mantém referência à imagem para evitar ser coletada pelo garbage collector
            logo_label.pack(pady=12) # Espaçamento acima e abaixo da logo (aumentei pady para 12)
            return logo_label # Retorna o label da logo
        except Exception as e: # Captura outras exceções
            print(f"Erro ao carregar a logo: {e}") # Imprime erro no console
            return None # Retorna None em caso de falha ao carregar

class SpooferClient:
    def __init__(self, root):
        self.root = root
        root.title("Spoofer Client")
        root.configure(bg="#1E1E1E") # Define a cor de fundo da janela principal como #1E1E1E

        # Centralizar janela
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        width = 400 # Largura padrão da janela (pode ser ajustada)
        height = 300 # Altura padrão da janela (pode ser ajustada)
        x = (screen_width/2) - (width/2)
        y = (screen_height/2) - (height/2)
        root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')
        root.resizable(False, False) # Impede redimensionar a janela

        self.usuario_logado = None # Inicializa como None, será atualizado no login
        self.feedback_text = None # Inicializa como None, será criado depois

        # Frame principal para login
        self.login_frame = tk.Frame(root, bg="#1E1E1E") # Frame com fundo #1E1E1E
        self.login_frame.pack(pady=20, padx=20, fill="both", expand=True) # Pack do frame de login

        VisualManager.carregar_logo(self.login_frame) # Carrega a logo no frame de login

        # Label e Entry para Key
        key_label = tk.Label(self.login_frame, text="Chave de Acesso:", fg="#00D4FF", bg="#1E1E1E", font=("Arial", 10, "bold")) # Label "Chave de Acesso"
        key_label.pack(pady=(0, 5), anchor=tk.W) # Posição e espaçamento do label
        self.key_entry = tk.Entry(self.login_frame, bg="#2E2E2E", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Arial", 9)) # Entry para a chave
        self.key_entry.pack(pady=(0, 15), fill=tk.X) # Posição e preenchimento horizontal da Entry

        # Botão de Login
        login_button_bg_frame = tk.Frame(self.login_frame, bg="#1E1E1E") # Frame para background do botão login
        login_button_bg_frame.pack(pady=(0, 15), anchor=tk.CENTER) # Posição do frame do botão login
        login_button = tk.Button(
            login_button_bg_frame,
            text="Login",
            command=self.requisitar_login,
            fg="black",
            bg="#00D4FF",
            font=("Arial", 9, "bold"),
            width=15,
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
        )
        login_button.pack(pady=0) # Pack do botão login

        # Botão "Gerar Chaves de Acesso" (ADMIN, inicialmente oculto)
        self.gerar_chaves_button_bg_frame = tk.Frame(self.login_frame, bg="#1E1E1E") # Frame para bg botão gerar chaves
        self.gerar_chaves_button_bg_frame.pack(pady=0, anchor=tk.CENTER) # Pack frame bg gerar chaves
        self.gerar_chaves_button = tk.Button(
            self.gerar_chaves_button_bg_frame,
            text="Gerar Chaves de Acesso (ADMIN)",
            command=self.abrir_janela_gerar_chaves, # Função para abrir janela de gerar chaves
            fg="black",
            bg="#55FFD9",
            font=("Arial", 9, "bold"),
            width=25,
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
        )
        self.gerar_chaves_button.pack(pady=0) # Pack do botão gerar chaves
        self.gerar_chaves_button.pack_forget() # Inicialmente oculto

        # Bind Enter key para login
        root.bind('<Return>', lambda event=None: login_button.invoke()) # Bind Enter para o botão de login

    def mostrar_feedback(self, mensagem, limpar_antes=False): # Função para mostrar feedback na interface
        if self.feedback_text is None: # Se feedback_text ainda não foi criado, cria agora
            self.feedback_text = tk.Text(
                self.login_frame,
                height=3, # Altura reduzida para 3 linhas
                width=35, # Largura ajustada para 35 caracteres
                bg="#2E2E2E",
                fg="#00D4FF",
                font=("Arial", 9),
                wrap=tk.WORD,
                state=tk.DISABLED
            )
            self.feedback_text.pack(pady=5, padx=10, fill=tk.X) # Posição e preenchimento do feedback_text

        self.feedback_text.config(state=tk.NORMAL) # Habilita edição para modificar o texto
        if limpar_antes: # Se limpar_antes for True, limpa o texto antes de inserir
            self.feedback_text.delete(1.0, tk.END) # Limpa o texto
        self.feedback_text.insert(tk.END, mensagem + "\n") # Insere a nova mensagem com nova linha
        self.feedback_text.config(state=tk.DISABLED) # Desabilita edição novamente
        self.feedback_text.see(tk.END) # Auto-scroll para o fim do texto

    def requisitar_login(self): # Função para requisitar o login ao servidor
        chave_acesso = self.key_entry.get() # Obtém a chave de acesso digitada
        hwid = self.obter_hwid() # Obtém o HWID do computador

        if not chave_acesso: # Validação da chave de acesso
            self.mostrar_feedback("Por favor, insira a chave de acesso.", limpar_antes=True) # Feedback se a chave estiver vazia
            return

        self.mostrar_feedback("Validando chave de acesso...", limpar_antes=True) # Feedback enquanto valida

        try:
            response = requests.post(
                "http://127.0.0.1:5000/login", # Endpoint de login no servidor
                json={"key": chave_acesso, "hwid": hwid}, # Envia chave e HWID no formato JSON
                timeout=10 # Timeout de 10 segundos para a requisição
            )
            response.raise_for_status() # Erro para HTTP status codes de erro (4xx ou 5xx)
            data = response.json() # Decodifica a resposta JSON

            if data.get("success"): # Verifica se o login foi bem-sucedido
                self.usuario_logado = data.get("usuario") # Obtém o nome de usuário do JSON
                self.mostrar_feedback(f"Login bem-sucedido! Bem-vindo, {self.usuario_logado}.", limpar_antes=True) # Feedback de sucesso
                if self.usuario_logado == "socafofoh": # Se o usuário for o admin ("socafofoh")
                    self.gerar_chaves_button.pack(pady=0, anchor=tk.CENTER) # Exibe o botão de gerar chaves para admin
                self.root.after(1500, self.abrir_tela_spoofing) # Espera 1.5 segundos e abre a tela de spoofing
            else: # Se login falhou
                erro_msg = data.get("message", "Falha ao validar a chave de acesso.") # Obtém mensagem de erro ou usa padrão
                self.mostrar_feedback(erro_msg, limpar_antes=True) # Feedback de falha
        except requests.exceptions.RequestException as e: # Captura erros de requisição (ex: timeout, conexão recusada)
            self.mostrar_feedback(f"Erro de conexão: {e}", limpar_antes=True) # Feedback de erro de conexão
        except json.JSONDecodeError: # Captura erros de decodificação JSON
            self.mostrar_feedback("Erro ao processar resposta do servidor.", limpar_antes=True) # Feedback de erro JSON

    def obter_hwid(self): # Função para obter o HWID do computador
        try:
            sys_platform = platform.system() # Obtém o sistema operacional
            if sys_platform == "Windows": # Para Windows
                return subprocess.check_output('wmic csproduct get uuid', shell=True, text=True).split('\n')[1].strip() # HWID Windows
            elif sys_platform == "Linux": # Para Linux
                return subprocess.check_output('sudo dmidecode -s system-uuid', shell=True, text=True).strip() # HWID Linux (requer sudo)
            elif sys_platform == "Darwin": # Para macOS
                return subprocess.check_output('ioreg -rd1 -c IOPlatformExpertDevice | grep -E \'"UUID"\'', shell=True, text=True).split('=')[1].strip().strip('"') # HWID macOS
            else: # Se não for Windows, Linux ou macOS
                return "Sistema operacional não suportado para HWID" # Retorna msg de sistema não suportado
        except Exception as e: # Captura exceções ao obter HWID
            return f"Erro ao obter HWID: {e}" # Retorna msg de erro ao obter HWID

    def abrir_tela_spoofing(self): # Função para abrir a tela de spoofing (menu spoofer)
        spoof_window = tk.Tk() # Cria nova janela tkinter
        spoof_window.title("Menu do Spoofer") # Título da janela
        # VisualManager.carregar_fundo(spoof_window, apply_background=True) # Carrega o fundo no menu spoofer!  <--- BACKGROUND AINDA REMOVIDO!
        default_width = 500 # <--- DIMENSÕES PADRÃO
        default_height = 380 # <--- DIMENSÕES PADRÃO
        bg_width = default_width  # <--- USANDO PADRÃO SE NÃO TIVER BACKGROUND
        bg_height = default_height # <--- USANDO PADRÃO SE NÃO TIVER BACKGROUND
        if hasattr(spoof_window, 'background_size'): # <--- VERIFICA SE background_size EXISTE
            bg_width, bg_height = spoof_window.background_size # <--- USA AS DIMENSÕES DO BACKGROUND SE DISPONÍVEIS
        spoof_window.geometry(f"{bg_width}x{bg_height + 150}") # Janela do spoofer AINDA MENOR verticalmente (reduzi de 160 para 150)
        spoof_frame = tk.Frame(spoof_window, bg="#1E1E1E") # Frame principal do menu spoofer com bg #1E1E1E
        spoof_frame.pack(fill="both", expand=True) # Pack do frame para preencher a janela
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
            text="✅ Li o Guia",
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
                command=self.abrir_janela_gerar_chaves, # Manter para admin gerar chaves
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

    def mostrar_guia(self): # Função para mostrar o guia (simulada por enquanto)
        messagebox.showinfo("Guia de Desvinculação", "Aqui estará o guia de desvinculação...")

    def atualizar_estado_botao_spoofar(self): # Função para atualizar o estado do botão Spoofar
        if self.guia_lido.get(): # Se o guia foi lido (checklist marcado)
            self.spoof_button.config(state=tk.NORMAL) # Habilita o botão Spoofar
        else: # Se o guia não foi lido
            self.spoof_button.config(state=tk.DISABLED) # Desabilita o botão Spoofar

    def spoofar_completo(self): # Função para executar o spoofing completo (simulada por enquanto)
        messagebox.showinfo("Spoofing!", "Spoofing completo em 1 clique... (funcionalidade simulada)")

    def abrir_janela_gerar_chaves(self): # Função para abrir a janela de gerar chaves
        janela_gerar_chaves = tk.Toplevel(self.root) # Cria uma nova janela toplevel
        janela_gerar_chaves.title("Gerar Chaves de Acesso") # Título da janela
        janela_gerar_chaves.configure(bg="#1E1E1E", padx=20, pady=15) # Cor de fundo e padding da janela
        janela_gerar_chaves.resizable(False, False) # Impede redimensionar

        # Centralizar janela de gerar chaves (relativo à janela principal)
        window_width = 300 # Largura da janela de gerar chaves
        window_height = 200 # Altura da janela de gerar chaves
        screen_width = janela_gerar_chaves.winfo_screenwidth()
        screen_height = janela_gerar_chaves.winfo_screenheight()
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))
        janela_gerar_chaves.geometry(f"{window_width}x{window_height}+{x}+{y}")

        # Label "Gerar Chaves de Acesso Admin" no topo
        tk.Label(janela_gerar_chaves, text="Gerar Chaves de Acesso Admin", fg="#55FFD9", bg="#1E1E1E", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        # Frame para campos de quantidade e tempo
        frame_campos = tk.Frame(janela_gerar_chaves, bg="#1E1E1E") # Frame para alinhar campos
        frame_campos.pack(pady=5, fill=tk.X) # Pack do frame de campos

        # Label e Entry para Quantidade de Chaves
        tk.Label(frame_campos, text="Quantidade:", fg="#00D4FF", bg="#1E1E1E", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5), anchor=tk.W) # Label Quantidade
        self.quantidade_chaves_entry = tk.Entry(frame_campos, width=5, bg="#2E2E2E", fg="#FFFFFF", insertbackground="#FFFFFF", font=("Arial", 9)) # Entry Quantidade
        self.quantidade_chaves_entry.pack(side=tk.LEFT, fill=tk.X, expand=True) # Pack Entry Quantidade

        # Label e Combobox para Tempo de Expiração
        tk.Label(frame_campos, text="Tempo (dias):", fg="#00D4FF", bg="#1E1E1E", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=(10, 5), anchor=tk.W) # Label Tempo
        tempos = [1, 7, 30, 90, 180, 365] # Tempos de expiração predefinidos
        self.tempo_expiracao_combobox = tk.ttk.Combobox(frame_campos, values=tempos, width=4) # Combobox Tempo
        self.tempo_expiracao_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True) # Pack Combobox Tempo
        self.tempo_expiracao_combobox.set(30) # Define 30 dias como padrão

        # Botão Gerar Chaves dentro da janela
        button_gerar_bg_frame = tk.Frame(janela_gerar_chaves, bg="#1E1E1E") # Frame bg botão Gerar
        button_gerar_bg_frame.pack(pady=15, anchor=tk.CENTER) # Pack Frame bg botão Gerar
        gerar_button = tk.Button(
            button_gerar_bg_frame,
            text="Gerar Chaves",
            command=self.requisitar_chaves_servidor, # Função para requisitar as chaves do servidor
            fg="black",
            bg="#55FFD9",
            font=("Arial", 9, "bold"),
            width=15,
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
        )
        gerar_button.pack(pady=0) # Pack botão Gerar

        # Textbox de Feedback para janela de gerar chaves
        self.feedback_gerar_chaves_text = tk.Text(
            janela_gerar_chaves,
            height=4, # Altura para feedback de gerar chaves
            width=30, # Largura para feedback de gerar chaves
            bg="#2E2E2E",
            fg="#00D4FF",
            font=("Arial", 9),
            wrap=tk.WORD,
            state=tk.DISABLED
        )
        self.feedback_gerar_chaves_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True) # Pack feedback gerar chaves

    def requisitar_chaves_servidor(self): # Função para requisitar chaves ao servidor
        quantidade_chaves = self.quantidade_chaves_entry.get() # Obtém quantidade de chaves desejada
        tempo_expiracao_dias = self.tempo_expiracao_combobox.get() # Obtém o tempo de expiração em dias

        # Validações dos inputs (quantidade e tempo)
        if not quantidade_chaves.isdigit() or int(quantidade_chaves) <= 0: # Valida quantidade
            self.mostrar_feedback_gerar_chaves("Quantidade inválida. Insira um número positivo.", limpar_antes=True) # Feedback quantidade inválida
            return
        if not tempo_expiracao_dias.isdigit() or int(tempo_expiracao_dias) <= 0: # Valida tempo
            self.mostrar_feedback_gerar_chaves("Tempo de expiração inválido.", limpar_antes=True) # Feedback tempo inválido
            return

        try:
            quantidade = int(quantidade_chaves) # Converte quantidade para inteiro
            tempo_exp = int(tempo_expiracao_dias) # Converte tempo para inteiro
            self.mostrar_feedback_gerar_chaves(f"Gerando {quantidade} chaves...", limpar_antes=True) # Feedback gerando chaves

            response = requests.post(
                "http://127.0.0.1:5000/generate_keys", # Endpoint para gerar chaves no servidor
                json={"quantidade": quantidade, "tempo_expiracao": tempo_exp}, # Envia quantidade e tempo no JSON
                timeout=15 # Timeout para a requisição de gerar chaves
            )
            response.raise_for_status() # Erro para HTTP status codes de erro
            data = response.json() # Decodifica resposta JSON

            if data.get("success"): # Se a geração de chaves foi bem-sucedida
                chaves_geradas = data.get("chaves", []) # Obtém a lista de chaves geradas
                if chaves_geradas: # Se chaves foram geradas
                    mensagem_chaves = "\n".join(chaves_geradas) # Formata chaves para exibição
                    feedback_msg = f"Chaves geradas com sucesso:\n\n{mensagem_chaves}" # Mensagem de feedback sucesso
                    self.mostrar_feedback_gerar_chaves(feedback_msg, limpar_antes=True) # Exibe feedback de sucesso
                else: # Se nenhuma chave foi gerada (improvável, mas trata o caso)
                    self.mostrar_feedback_gerar_chaves("Chaves geradas com sucesso, mas lista está vazia.", limpar_antes=True) # Feedback lista vazia
            else: # Se a geração de chaves falhou
                erro_msg = data.get("message", "Falha ao gerar chaves.") # Obtém mensagem de erro ou usa padrão
                self.mostrar_feedback_gerar_chaves(erro_msg, limpar_antes=True) # Feedback de falha
        except requests.exceptions.RequestException as e: # Captura erros de requisição
            self.mostrar_feedback_gerar_chaves(f"Erro de conexão ao gerar chaves: {e}", limpar_antes=True) # Feedback de erro de conexão
        except json.JSONDecodeError: # Captura erros de decodificação JSON
            self.mostrar_feedback_gerar_chaves("Erro ao processar resposta do servidor de geração de chaves.", limpar_antes=True) # Feedback erro JSON

    def mostrar_feedback_gerar_chaves(self, mensagem, limpar_antes=False): # Feedback na janela de gerar chaves
        self.feedback_gerar_chaves_text.config(state=tk.NORMAL) # Habilita edição
        if limpar_antes: # Limpa texto se solicitado
            self.feedback_gerar_chaves_text.delete(1.0, tk.END) # Limpa
        self.feedback_gerar_chaves_text.insert(tk.END, mensagem + "\n") # Insere msg
        self.feedback_gerar_chaves_text.config(state=tk.DISABLED) # Desabilita edição
        self.feedback_gerar_chaves_text.see(tk.END) # Auto-scroll

if __name__ == "__main__":
    root = tk.Tk()
    app = SpooferClient(root)
    root.mainloop()