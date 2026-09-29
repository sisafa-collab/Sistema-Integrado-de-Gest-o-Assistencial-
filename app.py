import streamlit as st
import pandas as pd
import os 
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client
import time    
import datetime
import base64
from fpdf import FPDF

# --- CONEXÃO COM O BANCO DE DADOS SUPABASE ---
@st.cache_resource
def iniciar_conexao():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = iniciar_conexao()

# --- 1. CONFIGURAÇÃO DA PÁGINA E CSS (COR #231f20) ---
st.set_page_config(layout="wide")

st.markdown("""
<style>
    /* 1. Fundo escuro da aplicação */
    [data-testid="stAppViewContainer"] {
        background-color: #231f20;
    }
    [data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stSidebar"], 
    [data-testid="stSidebar"] > div:first-child {
        background-color: #231f20 !important;
    }

    /* 🔎 2. HIERARQUIA DE TEXTO E CORES (A MÁGICA DA LEITURA LIMPA) */
    
    /* Textos comuns em cinza claro sólido (Sem neon para não cansar a vista) */
    p, label, li, span {
        font-size: 1.15rem !important; 
        color: #E0E0E0 !important; /* Cinza claro elegante */
        text-shadow: none !important; 
    }
    
    /* Apenas os títulos acendem em Verde Neon SISAFA */
    h1, h2, h3, h4, h5, h6 {
        color: #00E676 !important;
        text-shadow: 0 0 8px rgba(0, 230, 118, 0.4) !important;
        font-weight: bold;
    }
    
    h1 { font-size: 2.5rem !important; }
    h2 { font-size: 2.2rem !important; }
    h3 { font-size: 1.8rem !important; }
    h4, h5, h6 { font-size: 1.5rem !important; }

    /* 🔎 3. LINHAS DIVISÓRIAS NEON (st.divider) */
    hr {
        border-top: 1px solid rgba(0, 230, 118, 0.4) !important;
        box-shadow: 0 0 8px rgba(0, 230, 118, 0.2) !important;
        margin-top: 25px !important;
        margin-bottom: 25px !important;
    }

    /* 🔎 4. CAIXAS E EXPANDERS (Organiza o visual "embolado") */
    [data-testid="stExpander"] {
        border: 1px solid rgba(0, 230, 118, 0.3) !important;
        border-radius: 8px !important;
        background-color: #2a2526 !important; /* Fundo um tom acima do painel para destacar */
        margin-bottom: 15px;
    }

    /* 🔎 5. AUMENTO DAS ABAS (TABS) E ÍCONES DELAS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 65px; 
        font-size: 1.25rem !important; 
        white-space: pre-wrap;
        background-color: #332d2e;
        border-radius: 6px 6px 0px 0px;
        padding: 12px 16px;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4c4955;
        border-bottom: 3px solid #00E676; 
    }

    /* 🔎 6. BOTÕES E ÁREA DE CLIQUE */
    div.stButton > button {
        background-color: transparent !important;
        color: #00E676 !important;
        font-weight: 900 !important;
        font-size: 1.15rem !important; 
        padding: 14px 24px !important; 
        border: 2px solid #00E676 !important;
        border-radius: 8px !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.3), inset 0 0 10px rgba(0, 230, 118, 0.1) !important;
        transition: all 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #00E676 !important;
        color: #231f20 !important;
        box-shadow: 0 0 20px rgba(0, 230, 118, 0.8), inset 0 0 15px rgba(0, 230, 118, 0.5) !important;
    }
    
    /* 🔎 7. CAMPOS DE DIGITAÇÃO E SELEÇÃO */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #332d2e !important;
        color: #00E676 !important;
        font-size: 1.15rem !important; 
        padding: 10px !important;
        border: 1px solid #4c4955 !important;
        font-weight: bold;
    }
    .stTextInput input:focus {
        border: 1px solid #00E676 !important;
        box-shadow: 0 0 8px rgba(0, 230, 118, 0.5) !important;
    }
</style>
""", unsafe_allow_html=True)


# --- 2. CONTROLE DE SESSÃO E LOGIN ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    # Criação de 3 colunas para centralizar o conteúdo na coluna do meio
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        # Blindagem: verifica se a imagem existe antes de tentar carregar
        try:
            if os.path.exists("SIGA-LOGO.png"):
                # A imagem assume a largura da coluna perfeitamente
                st.image("SIGA-LOGO.png", width="stretch")
            else:
                st.warning("⚠️ Arquivo 'SIGA-LOGO.png' não encontrado no repositório.")
        except Exception:
            st.markdown("<h1 style='text-align: center; color: #ffffff;'>⚓ SIGA</h1>", unsafe_allow_html=True)

        # Campos de entrada atualizados para NIP/CPF
        nip_input = st.text_input("CPF do Operador")
        senha_input = st.text_input("Senha", type="password")
        
        # Espaçamento para o botão respirar no layout
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            if nip_input and senha_input:
                try:
                    # 1. Busca o usuário na tabela 'usuarios' do Supabase
                    resposta = supabase.table("usuarios").select("*").eq("cpf", nip_input).execute()
                    
                    if len(resposta.data) > 0:
                        user_data = resposta.data[0]
                        
                        # 2. Confere se a senha bate com a do banco
                        if user_data['senha'] == senha_input:
                            st.session_state.logged_in = True
                            st.session_state.user_nip = user_data['cpf']
                            st.session_state.user_full_name = user_data['nome_completo']
                            st.session_state.uasg_logada = user_data['uasg']
                            st.session_state.om_nome = user_data['nome_om']
                            st.session_state.perfil = user_data['perfil']
                            st.rerun() 
                        else:
                            st.error("⚠️ Senha incorreta.")
                    else:
                        st.error("⚠️ Operador não encontrado no sistema.")
                        
                except Exception as e:
                    st.error(f"Erro ao conectar com o banco de dados: {e}")
            else:
                st.warning("⚠️ Preencha o seu CPF e a Senha para continuar.")

else:
    # --- MENU LATERAL (SIDEBAR) ---
    with st.sidebar:
        # Tenta carregar o logo; se falhar, exibe a âncora em texto
        try:
            if os.path.exists("SIGA-LOGO.png"):
                st.image("SIGA-LOGO.png", use_container_width=True)
            else:
                st.markdown("<h2 style='text-align: center;'>⚓ SIGA</h2>", unsafe_allow_html=True)
        except Exception:
            st.markdown("<h2 style='text-align: center;'>⚓ SIGA</h2>", unsafe_allow_html=True)
        
        st.divider()
        
        # Resumo do Operador na Barra Lateral
        st.markdown(f"<p style='text-align: center; font-size: 1rem; font-weight: 900;'>👤 {st.session_state.user_full_name}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; font-size: 0.8rem; color: #aaaaaa !important;'>{st.session_state.perfil} | {st.session_state.om_nome}</p>", unsafe_allow_html=True)
        
        st.divider()
        
        # Botão de Logout
        if st.button("🚪 SAIR DO SISTEMA", use_container_width=True):
            st.session_state.clear() # Apaga todas as credenciais da memória
            st.rerun() # Reinicia a página (voltando para a tela de login)

    # --- 3. INTERFACE PRINCIPAL DO SISTEMA ---
    st.markdown(f"### 🏥 {st.session_state.om_nome} | Operador: {st.session_state.user_full_name}")
    st.divider()

    # Botão para expandir/ocultar o painel de informações pessoais
    if st.button("⚙️ ALTERAR INFORMAÇÕES PESSOAIS", use_container_width=True):
        st.session_state.editando_perfil = not st.session_state.get('editando_perfil', False)

    # Se o botão foi clicado, abre o formulário
    if st.session_state.get('editando_perfil', False):
        try:
            # Busca os dados atualizados direto do Supabase
            resposta_user = supabase.table("usuarios").select("*").eq("cpf", st.session_state.user_nip).execute()
            dados_user = resposta_user.data[0]

            with st.form("form_atualizacao_perfil"):
                st.markdown("#### 🔒 Atualização de Cadastro")
                
                col_bloqueada, col_editavel = st.columns(2)
                
                with col_bloqueada:
                    st.text_input("CPF", value=dados_user['cpf'], disabled=True)
                    st.text_input("UASG", value=dados_user['uasg'], disabled=True)
                    st.text_input("Organização Militar", value=dados_user['nome_om'], disabled=True)
                    st.text_input("Perfil de Acesso", value=dados_user['perfil'], disabled=True)

                with col_editavel:
                    novo_nome = st.text_input("Nome Completo", value=dados_user['nome_completo'])
                    novo_email = st.text_input("E-mail", value=dados_user.get('email', ''))
                    novo_telefone = st.text_input("Telefone", value=dados_user.get('telefone', ''))
                    nova_senha = st.text_input("Senha", value=dados_user['senha'], type="password")

                if st.form_submit_button("💾 SALVAR NOVOS DADOS", use_container_width=True):
                    # Faz o envio (UPDATE) para o Supabase com os campos permitidos
                    supabase.table("usuarios").update({
                        "nome_completo": novo_nome,
                        "email": novo_email,
                        "telefone": novo_telefone,
                        "senha": nova_senha
                    }).eq("cpf", st.session_state.user_nip).execute()

                    # Atualiza a memória local para mudar o nome no topo da tela instantaneamente
                    st.session_state.user_full_name = novo_nome
                    
                    st.success("✅ Informações atualizadas com sucesso no banco de dados!")
                    time.sleep(1.5)
                    st.session_state.editando_perfil = False # Esconde o formulário
                    st.rerun() # Atualiza a tela

        except Exception as e:
            st.error(f"Erro ao buscar informações no banco: {e}")

    # Criação das 5 abas operacionais
    tab_capacidade, tab_mapa, tab_acompanhamento, tab_indicadores, tab_contato = st.tabs([
        "📊 Minha Capacidade", 
        "🗺️ Cadastrar Demanda", 
        "🔄 Acompanhamento", 
        "📈 Indicadores", 
        "📞 Fale Conosco"
    ])

    with tab_capacidade:
        st.markdown("<h3 style='color: #00E676; text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);'>📝 Gestão Dinâmica de Agenda</h3>", unsafe_allow_html=True)
        st.info("Siga o fluxo para disponibilizar horários. O sistema só habilitará o próximo passo após a seleção anterior.")
        
        try:
            # 1. Puxa o Catálogo Mestre apenas uma vez para não gastar requisições
            cat_res = supabase.table("capacidades_disponiveis").select("*").execute()
            df_cat = pd.DataFrame(cat_res.data)
            
            if not df_cat.empty:
                # --- FLUXO EM CASCATA ---
                col1, col2 = st.columns(2)
                
                with col1:
                    grupos = df_cat['grupo_capacidade'].unique()
                    grupo_sel = st.selectbox("1️⃣ Selecione o Grupo:", [""] + list(grupos))
                    
                with col2:
                    if grupo_sel:
                        especialidades = df_cat[df_cat['grupo_capacidade'] == grupo_sel]['desc_capacidade'].unique()
                        espec_sel = st.selectbox("2️⃣ Selecione a Especialidade:", [""] + list(especialidades))
                    else:
                        st.selectbox("2️⃣ Selecione a Especialidade:", ["Aguardando seleção do grupo..."], disabled=True)
                        espec_sel = ""

                # Só libera o calendário e os horários se a especialidade foi escolhida
                if espec_sel:
                    col3, col4 = st.columns([1, 2])
                    with col3:
                        data_sel = st.date_input("3️⃣ Selecione o Dia:")
                        
                    with col4:
                        # Motor de Intervalos (Gera horários das 08:00 às 18:00 de 20 em 20 minutos)
                        start_time = datetime.datetime.strptime("08:00", "%H:%M")
                        end_time = datetime.datetime.strptime("18:00", "%H:%M")
                        horarios_disponiveis = []
                        
                        while start_time <= end_time:
                            horarios_disponiveis.append(start_time.strftime("%H:%M"))
                            start_time += datetime.timedelta(minutes=20)
                            
                        horarios_sel = st.multiselect("4️⃣ Selecione os Horários Disponíveis:", horarios_disponiveis)
                        
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Botão de Salvamento com estilo Neon (CSS já embutido no projeto)
                    if st.button("💾 ATUALIZAR CAPACIDADES (SALVAR NO BANCO)", use_container_width=True):
                        if horarios_sel:
                            with st.spinner("Sincronizando com a base central do Supabase..."):
                                # Acha o ID exato da especialidade escolhida
                                id_cap = df_cat[(df_cat['grupo_capacidade'] == grupo_sel) & (df_cat['desc_capacidade'] == espec_sel)]['id_capacidade'].values[0]
                                
                                # Prepara os dados para o banco
                                data_formatada = data_sel.strftime("%d/%m/%Y")
                                horarios_texto = ", ".join(horarios_sel)
                                
                                nova_capacidade = {
                                    "uasg_hospital": st.session_state.uasg_logada,
                                    "id_capacidade": int(id_cap),
                                    "dias_disponiveis": data_formatada,
                                    "horarios_disponiveis": horarios_texto
                                }
                                
                                supabase.table("capacidade_hospitalar").insert(nova_capacidade).execute()
                                
                                st.success(f"✅ Agenda de {espec_sel} para o dia {data_formatada} registrada com sucesso!")
                                time.sleep(1.5)
                                st.rerun() 
                        else:
                            st.warning("⚠️ Selecione pelo menos um horário no passo 4 antes de atualizar.")

            # --- PAINEL DE CONSOLIDAÇÃO E EXCLUSÃO ---
            st.divider()
            st.markdown("<h4 style='color: #f8f9fa;'>📋 Minha Grade Cadastrada Atualmente</h4>", unsafe_allow_html=True)
            
            # Puxa o que a OM já tem cadastrado no banco para mostrar ao operador
            hosp_res = supabase.table("capacidade_hospitalar").select("*").eq("uasg_hospital", st.session_state.uasg_logada).execute()
            df_hosp = pd.DataFrame(hosp_res.data)
            
            if not df_hosp.empty:
                # Cruza com o catálogo para pegar os nomes ao invés dos IDs
                df_merged = pd.merge(df_hosp, df_cat, on="id_capacidade", how="inner")
                df_display = df_merged[["grupo_capacidade", "desc_capacidade", "dias_disponiveis", "horarios_disponiveis"]]
                df_display.columns = ["Grupo", "Especialidade", "Data", "Horários Reservados"]
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                
                # --- SISTEMA DE CANCELAMENTO DE VAGAS ---
                st.markdown("<br><h5 style='color: #ff4b4b;'>🗑️ Cancelamento de Agendas</h5>", unsafe_allow_html=True)
                
                # Cria a lista de opções mostrando o ID, nome e data para o operador identificar
                opcoes_exclusao = df_merged.apply(lambda row: f"ID: {row['id_vinculo']} | {row['desc_capacidade']} - {row['dias_disponiveis']}", axis=1).tolist()
                
                col_ex1, col_ex2 = st.columns([3, 1])
                agenda_cancelar = col_ex1.selectbox("Selecione a grade que deseja indisponibilizar:", [""] + opcoes_exclusao)
                
                col_ex2.markdown("<br>", unsafe_allow_html=True) # Alinhamento com a caixa de texto
                if col_ex2.button("🚫 REMOVER GRADE", use_container_width=True):
                    if agenda_cancelar:
                        with st.spinner("Excluindo..."):
                            # Isola apenas o número do ID para mandar pro banco
                            id_alvo = int(agenda_cancelar.split(" | ")[0].replace("ID: ", ""))
                            supabase.table("capacidade_hospitalar").delete().eq("id_vinculo", id_alvo).execute()
                            st.success("✅ Grade de horários indisponibilizada com sucesso!")
                            time.sleep(1.5)
                            st.rerun()
                    else:
                        st.warning("⚠️ Selecione uma grade na lista antes de clicar em remover.")
            else:
                st.info("Sua OM ainda não disponibilizou vagas no sistema.")
                
        except Exception as e:
            st.error(f"Erro ao sincronizar com o banco de dados: {e}")

    with tab_mapa:
        st.markdown("<h3 style='color: #00E676; text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);'>🗺️ Radar de Demandas Assistenciais</h3>", unsafe_allow_html=True)
        st.write("Clique nos escudos das Forças para visualizar o portfólio e abrir o painel de solicitação.")
        
        try:
            # 1. Puxa as tabelas necessárias
            df_hosp = pd.DataFrame(supabase.table("hospitais").select("*").execute().data)
            df_cap_hosp = pd.DataFrame(supabase.table("capacidade_hospitalar").select("uasg_hospital, id_capacidade").execute().data)
            df_cat = pd.DataFrame(supabase.table("capacidades_disponiveis").select("*").execute().data)
            
            # 2. Gera o Mapa com servidor tático da ESRI
            m = folium.Map(
                location=[-15.7906, -47.8920], 
                zoom_start=11, 
                tiles="https://services.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
                attr="Esri, HERE, Garmin, FAO, NOAA, USGS"
            )    

            if not df_hosp.empty:
                if not df_cap_hosp.empty and not df_cat.empty:
                    df_cruzamento = pd.merge(df_cap_hosp, df_cat, on="id_capacidade")
                else:
                    df_cruzamento = pd.DataFrame(columns=["uasg_hospital", "desc_capacidade"])

                # 3. Laço para criar um marcador para cada Hospital do Banco
                for _, row in df_hosp.iterrows():
                    forca = str(row['forca']).strip().upper()
                    
                    if forca == "MARINHA": logo_file = "MARINHA-LOGO.png"
                    elif forca == "EXERCITO": logo_file = "EXERCITO-LOGO.png"
                    elif forca == "AERONAUTICA": logo_file = "AERONAUTICA-LOGO.png"
                    else: logo_file = "SIGA-LOGO.png"
                    
                    especialidades = df_cruzamento[df_cruzamento['uasg_hospital'] == row['uasg']]['desc_capacidade'].unique()
                    if len(especialidades) > 0:
                        lista_html = "".join([f"<li style='margin-bottom:4px;'>🔹 {esp}</li>" for esp in especialidades])
                    else:
                        lista_html = "<li style='color: #ff4b4b;'>Nenhuma capacidade cadastrada no momento.</li>"

                    b64_img = ""
                    if os.path.exists(logo_file):
                        with open(logo_file, "rb") as f:
                            b64_img = base64.b64encode(f.read()).decode()
                            
                    img_tag = f"<img src='data:image/png;base64,{b64_img}' style='max-height: 55px; display: block; margin: 0 auto;'>" if b64_img else f"<h3 style='text-align:center;'>{forca}</h3>"

                    html_popup = f"""
                    <div style="font-family: Arial, sans-serif; min-width: 240px; background-color: #1a1a1a; padding: 15px; border-radius: 8px; border: 1px solid #00E676; box-shadow: 0 0 15px rgba(0, 230, 118, 0.4);">
                        {img_tag}
                        <h4 style="text-align: center; color: #ffffff; margin: 12px 0 5px 0; font-weight: 900; letter-spacing: 1px;">{row['nome']}</h4>
                        <p style="font-size: 11px; color: #aaaaaa; margin: 0 0 15px 0; text-align: center; font-style: italic;">📍 {row['endereco']}</p>
                        <div style="background-color: #231f20; padding: 10px; border-radius: 5px; border-left: 3px solid #00E676;">
                            <h5 style="margin: 0 0 10px 0; color: #00E676; font-size: 11px; letter-spacing: 1px;">ESPECIALIDADES DISPONÍVEIS:</h5>
                            <ul style="font-size: 11px; color: #e0e0e0; padding-left: 15px; margin: 0; list-style-type: none;">
                                {lista_html}
                            </ul>
                        </div>
                    </div>
                    """
                    
                    if os.path.exists(logo_file):
                        icone_mapa = folium.CustomIcon(logo_file, icon_size=(65, 65))
                    else:
                        icone_mapa = folium.Icon(color="green", icon="info-sign")

                    # O SEGREDO TÁTICO: Colocamos a UASG no tooltip (oculto visualmente no clique, mas o Python lê)
                    folium.Marker(
                        [float(row['latitude']), float(row['longitude'])],
                        popup=folium.Popup(html_popup, max_width=320),
                        icon=icone_mapa,
                        tooltip=f"{row['uasg']} | {row['nome']}" 
                    ).add_to(m)

            # 4. Renderiza o mapa e CAPTURA O CLIQUE DO USUÁRIO
            dados_mapa = st_folium(m, height=500, use_container_width=True)

            # =================================================================
            # 5. PAINEL INFERIOR: GATILHO DE SOLICITAÇÃO DE CONSULTA
            # =================================================================
            if dados_mapa and dados_mapa.get("last_object_clicked_tooltip"):
                info_clique = dados_mapa["last_object_clicked_tooltip"]
                
                if "|" in info_clique:
                    uasg_alvo = info_clique.split("|")[0].strip()
                    nome_alvo = info_clique.split("|")[1].strip()

                    st.divider()
                    
                    # Bloqueia a OM de pedir consulta para si mesma
                    if uasg_alvo == st.session_state.uasg_logada:
                        st.info(f"⚓ Você clicou em sua própria Organização Militar ({nome_alvo}).")
                    else:
                        st.markdown(f"<h3 style='color: #00E676;'>🎯 Solicitar Atendimento: {nome_alvo}</h3>", unsafe_allow_html=True)
                        
                        # Descobre as especialidades do hospital clicado
                        especialidades_alvo = df_cruzamento[df_cruzamento['uasg_hospital'] == uasg_alvo]['desc_capacidade'].unique()
                        
                        if len(especialidades_alvo) > 0:
                            # Formulário de Cadastro da Demanda
                            with st.form(key="form_solicitacao"):
                                esp_selecionada = st.selectbox("1️⃣ Especialidade Necessária:", especialidades_alvo)
                                
                                # O chat inicial
                                texto_chat = st.text_area("2️⃣ Mensagem Inicial (Chat):", placeholder="Ex: Paciente 3ºSG MB com indicação cirúrgica. Necessita de consulta com brevidade. Seguem documentos...")
                                
                                # Botão Verde Neon (Puxa o CSS global automaticamente)
                                submit = st.form_submit_button("🟢 SOLICITAR CONSULTA (CADASTRAR DEMANDA)", use_container_width=True)
                                
                                if submit:
                                    if texto_chat.strip() == "":
                                        st.warning("⚠️ Escreva uma mensagem inicial no chat para que a OM de destino possa analisar seu pedido.")
                                    else:
                                        with st.spinner("Registrando demanda no SIGA..."):
                                            # PASSO A: Cadastra na Tabela "demandas"
                                            nova_demanda = {
                                                "uasg_origem": st.session_state.uasg_logada,
                                                "uasg_destino": uasg_alvo,
                                                "especialidade": esp_selecionada,
                                                "status": 1
                                            }
                                            resposta_demanda = supabase.table("demandas").insert(nova_demanda).execute()
                                            
                                            # Pega o ID gerado pelo banco para a nova demanda
                                            id_gerado = resposta_demanda.data[0]['id_demanda']
                                            
                                            # PASSO B: Cadastra na Tabela "mensagens_chat"
                                            nova_mensagem = {
                                                "id_demanda": id_gerado,
                                                "uasg_remetente": st.session_state.uasg_logada,
                                                "texto": texto_chat
                                            }
                                            supabase.table("mensagens_chat").insert(nova_mensagem).execute()
                                            
                                            # PASSO C: Cadastra na Tabela "logs_demandas"
                                            novo_log = {
                                                "id_demanda": id_gerado,
                                                "status_anterior": 0, # Zero significa "Criação"
                                                "status_novo": 1,
                                                "cpf_operador": st.session_state.user_nip
                                            }
                                            supabase.table("logs_demandas").insert(novo_log).execute()
                                            
                                            st.success(f"✅ Demanda #{id_gerado} protocolada com sucesso! Acompanhe o andamento na aba (iii) Acompanhamento.")
                                            time.sleep(2)
                                            st.rerun()
                        else:
                            st.warning(f"⚠️ {nome_alvo} ainda não cadastrou vagas para as coirmãs.")

        except Exception as e:
            st.error(f"Erro na matriz do mapa ou comunicação com banco: {e}")


    with tab_acompanhamento:
        st.markdown("<h3 style='color: #00E676; text-shadow: 0 0 10px rgba(0, 230, 118, 0.3);'>🔄 Painel de Tramitação</h3>", unsafe_allow_html=True)
        st.write("Acompanhe o status das demandas, troque mensagens em tempo real e anexe a documentação necessária.")
        
        try:
            # --- 1. BUSCA GLOBAL DE AGENDAS (Economia de API) ---
            df_todas_cap = pd.DataFrame(supabase.table("capacidade_hospitalar").select("*").execute().data)
            df_cat_global = pd.DataFrame(supabase.table("capacidades_disponiveis").select("*").execute().data)
            
            if not df_todas_cap.empty and not df_cat_global.empty:
                df_agendas_sistema = pd.merge(df_todas_cap, df_cat_global, on="id_capacidade")
            else:
                df_agendas_sistema = pd.DataFrame()

            # 2. Busca todas as demandas onde a OM logada é ORIGEM (Solicitante) ou DESTINO (Avaliadora)
            res_demandas = supabase.table("demandas").select("*").or_(f"uasg_origem.eq.{st.session_state.uasg_logada},uasg_destino.eq.{st.session_state.uasg_logada}").order("data_criacao", desc=True).execute()
            df_demandas = pd.DataFrame(res_demandas.data)
            
            if df_demandas.empty:
                st.info("Nenhuma demanda registrada para a sua Organização Militar no momento.")
            else:
                # Dicionário visual de Status
                mapa_status = {
                    1: ("1 - APRESENTADA", "#FF9800"), # Laranja
                    2: ("2 - APROVADA", "#00E676"),    # Verde Neon
                    3: ("3 - PROTOCOLADA", "#03A9F4"), # Azul
                    4: ("4 - AGENDADA", "#9C27B0"),   # Roxo
                    5: ("5 - FATURADA", "#4CAF50"),    # Verde Escuro
                    8: ("8 - CANCELADA", "#F44336")    # Vermelho
                }

                # 2. Laço para criar um "Card/Expander" para cada demanda
                for _, row in df_demandas.iterrows():
                    id_dem = row['id_demanda']
                    status_atual = row['status']
                    texto_status, cor_status = mapa_status.get(status_atual, ("DESCONHECIDO", "#FFFFFF"))
                    
                    # Identifica se a minha OM está pedindo ou recebendo o pedido
                    papel = "SOLICITANTE" if row['uasg_origem'] == st.session_state.uasg_logada else "OFERTANTE (AVALIADOR)"
                    outra_om = row['uasg_destino'] if papel == "SOLICITANTE" else row['uasg_origem']
                    
                    # Cabeçalho do Card
                    titulo_card = f"Demanda #{id_dem} | {row['especialidade']} | Status: {texto_status}"
                    
                    with st.expander(titulo_card, expanded=(status_atual in [1, 2])):
                        # Divide a tela: Esquerda (Ações), Direita (Chat)
                        col_acao, col_chat = st.columns([1.2, 1])
                        
                        # ==========================================
                        # LADO ESQUERDO: INFORMAÇÕES E AÇÕES DE FLUXO
                        # ==========================================
                        with col_acao:
                            st.markdown(f"**Meu Papel:** {papel} | **OM Parceira:** {outra_om}")
                            st.markdown(f"<span style='color: {cor_status}; font-weight: bold; font-size: 14px;'>STATUS ATUAL: {texto_status}</span>", unsafe_allow_html=True)
                            st.divider()
                            
                            # --- REGRA DE NEGÓCIO: STATUS 1 -> 2 (Aprovação) ---
                            if status_atual == 1 and papel == "OFERTANTE (AVALIADOR)":
                                st.info("⚠️ Esta demanda aguarda a sua aprovação para seguir o trâmite.")
                                c_btn1, c_btn2 = st.columns(2)
                                if c_btn1.button("✅ APROVAR DEMANDA", key=f"apr_{id_dem}", use_container_width=True):
                                    with st.spinner("Registrando aprovação..."):
                                        # Atualiza Status
                                        supabase.table("demandas").update({"status": 2}).eq("id_demanda", id_dem).execute()
                                        # Salva Log
                                        supabase.table("logs_demandas").insert({"id_demanda": id_dem, "status_anterior": 1, "status_novo": 2, "cpf_operador": st.session_state.user_nip}).execute()
                                        st.rerun()
                                        
                                if c_btn2.button("❌ RECUSAR", key=f"rec_{id_dem}", use_container_width=True):
                                    supabase.table("demandas").update({"status": 8}).eq("id_demanda", id_dem).execute()
                                    supabase.table("logs_demandas").insert({"id_demanda": id_dem, "status_anterior": 1, "status_novo": 8, "cpf_operador": st.session_state.user_nip}).execute()
                                    st.rerun()

                            # --- REGRA DE NEGÓCIO: STATUS 2 -> 3 (Envio de Documentos pelo Solicitante) ---
                            elif status_atual == 2 and papel == "SOLICITANTE":
                                st.success("Demanda aprovada! 1º) Preencha os dados e baixe o Prontuário. 2º) Anexe-o escaneado com a guia médica.")
                                
                                # --- MAPEAMENTO DE HORÁRIOS DA OM DESTINO ---
                                uasg_atendimento = row['uasg_destino']
                                
                                # Faz a consulta na tabela relacional que o SAME alimenta
                                res_agenda = supabase.table("capacidade_hospitalar").select("dias_disponiveis, horarios_disponiveis").eq("uasg_hospital", uasg_atendimento).execute()
                                
                                # 1. Agrupa os horários por data em um Dicionário: {'26/10': ['13:00', '13:20'], '27/10': ['08:00']}
                                dict_agendas = {}
                                if res_agenda.data:
                                    for agenda in res_agenda.data:
                                        dias_raw = str(agenda.get("dias_disponiveis", "")).strip()
                                        horas_raw = str(agenda.get("horarios_disponiveis", "")).strip()
                                        
                                        if dias_raw and horas_raw:
                                            lista_dias = [d.strip() for d in dias_raw.split(",")]
                                            lista_horas = [h.strip() for h in horas_raw.split(",")]
                                            
                                            for d in lista_dias:
                                                if d not in dict_agendas:
                                                    dict_agendas[d] = []
                                                dict_agendas[d].extend(lista_horas)

                                # 1º PASSO: ÁREA DE PREENCHIMENTO
                                with st.expander("📝 Dados de agendamento", expanded=True):
                                    
                                    # =================================================================
                                    # SELEÇÃO DINÂMICA (Fica FORA do st.form para atualizar em tempo real)
                                    # =================================================================
                                    st.markdown("<h5 style='color: #00E676;'>📅 ESCOLHA DA DATA E HORÁRIO</h5>", unsafe_allow_html=True)
                                    
                                    if dict_agendas:
                                        datas_disponiveis = list(dict_agendas.keys())
                                        
                                        # Mostra visualmente as datas liberadas em destaque
                                        st.markdown(f"🗓️ *Datas liberadas pelo SAME:* **<span style='color: #00E676;'>{', '.join(datas_disponiveis)}</span>**", unsafe_allow_html=True)
                                        
                                        col_data, col_hora = st.columns(2)
                                        # Passo A: Escolhe a data
                                        data_escolhida = col_data.selectbox("Selecione o Dia:", datas_disponiveis, key=f"sel_data_{id_dem}")
                                        
                                        # Passo B: Puxa apenas os horários da data escolhida acima
                                        horarios_da_data = dict_agendas.get(data_escolhida, [])
                                        hora_escolhida = col_hora.selectbox("Selecione o Horário:", [""] + horarios_da_data, key=f"sel_hora_{id_dem}")
                                        
                                        # Salva a escolha final para imprimir no PDF
                                        horario_pref = f"{data_escolhida} - {hora_escolhida}" if hora_escolhida else ""
                                    else:
                                        st.warning("Nenhuma agenda cadastrada pelo SAME.")
                                        horario_pref = ""
                                    
                                    st.divider()

                                # 1º PASSO: FORMULÁRIO PARA GERAR O PDF (Não salva no banco)
                                with st.expander("📝 Preenchimento cadastral", expanded=True):
                                    with st.form(key=f"form_docs_{id_dem}"):
                                        
                                        st.markdown("<h5 style='color: #00E676;'>1. IDENTIFICAÇÃO DO PACIENTE</h5>", unsafe_allow_html=True)
                                        
                                        c1, c2, c3 = st.columns([2, 1, 1.2])
                                        nome_pac = c1.text_input("Nome Completo", key=f"nome_pac_{id_dem}")
                                        dt_nasc = c2.date_input("Data de Nascimento", key=f"dtnasc_{id_dem}")
                                        cpf_pac = c3.text_input("CPF", key=f"cpfpac_{id_dem}")

                                        c4, c5 = st.columns(2)
                                        nome_pai = c4.text_input("Nome do pai", key=f"pai_{id_dem}")
                                        nome_mae = c5.text_input("Nome da mãe", key=f"mae_{id_dem}")

                                        c6, c7, c8, c9 = st.columns([1.5, 1, 1.5, 1])
                                        rg = c6.text_input("Identidade", key=f"rg_{id_dem}")
                                        emissor = c7.text_input("Emissor", key=f"emis_{id_dem}")
                                        nat = c8.text_input("Naturalidade", key=f"nat_{id_dem}")
                                        sexo = c9.selectbox("Sexo", ["", "Masculino", "Feminino"], key=f"sex_{id_dem}")

                                        c10, c11, c12 = st.columns(3)
                                        nac = c10.text_input("Nacionalidade", key=f"nac_{id_dem}")
                                        cor = c11.text_input("Cor", key=f"cor_{id_dem}")
                                        est_civil = c12.text_input("Estado Civil", key=f"estciv_{id_dem}")

                                        st.markdown("<h5 style='color: #00E676; margin-top: 15px;'>2. CONTATO E ENDEREÇO</h5>", unsafe_allow_html=True)
                                        c13, c14 = st.columns([3, 1])
                                        end = c13.text_input("Endereço", key=f"end_{id_dem}")
                                        bairro = c14.text_input("Bairro", key=f"bai_{id_dem}")

                                        c15, c16, c17 = st.columns([2, 1, 1])
                                        cidade = c15.text_input("Cidade", key=f"cid_{id_dem}")
                                        uf = c16.text_input("UF", key=f"uf_{id_dem}")
                                        cep = c17.text_input("CEP", key=f"cep_{id_dem}")

                                        c18, c19, c20 = st.columns([1, 1.5, 1])
                                        celular = c18.text_input("Celular", key=f"cel_{id_dem}")
                                        email = c19.text_input("E-mail", key=f"email_{id_dem}")
                                        nip_pac = c20.text_input("SARAM / FUSEX / NIP", key=f"nip_pac_{id_dem}")

                                        st.markdown("<h5 style='color: #00E676; margin-top: 15px;'>3. IDENTIFICAÇÃO DO RESPONSÁVEL</h5>", unsafe_allow_html=True)
                                        c21, c22, c23 = st.columns([2, 1, 1])
                                        resp_nome = c21.text_input("Nome do Responsável", key=f"resp_{id_dem}")
                                        resp_posto = c22.text_input("Posto/Graduação", key=f"posto_{id_dem}", placeholder="Ex: Terceiro-Sargento")
                                        resp_om = c23.text_input("OM", key=f"om_{id_dem}")

                                        c24, c25, c26 = st.columns([2, 1, 1])
                                        resp_end = c24.text_input("Endereço do Responsável", key=f"rend_{id_dem}")
                                        resp_cel = c25.text_input("Tel. Celular", key=f"rcel_{id_dem}")
                                        resp_trab = c26.text_input("Tel. Trabalho", key=f"rtrab_{id_dem}")


                                        enviou = st.form_submit_button("🖨️ GERAR PRONTUÁRIO EM PDF", use_container_width=True)
                                        
                                        if enviou:
                                            if nome_pac and hora_escolhida:
                                                with st.spinner("Compilando prontuário tecnológico..."):
                                                    
                                                    # Função auxiliar para limpar acentos para o FPDF (Latin-1)
                                                    def limpa(texto):
                                                        return str(texto).encode('latin-1', 'ignore').decode('latin-1')

                                                    pdf = FPDF()
                                                    pdf.add_page()
                                                    
                                                    # --- PALETA DE CORES SIGA ---
                                                    COR_PRIMARIA = (46, 107, 84)    # Verde Institucional do SIGA
                                                    COR_FUNDO = (240, 245, 242)     # Verde super claro para fundos
                                                    COR_TEXTO = (60, 60, 60)        # Cinza escuro elegante
                                                    
                                                    # --- CABEÇALHO DE ALTO IMPACTO ---
                                                    pdf.set_fill_color(*COR_PRIMARIA)
                                                    pdf.set_text_color(255, 255, 255)
                                                    pdf.set_font("Arial", 'B', 15)
                                                    pdf.cell(0, 14, "  INFORMAÇÕES CADASTRAIS", border=0, ln=True, align='L', fill=True)
                                                    
                                                    # Subtítulo alinhado à direita
                                                    pdf.set_text_color(120, 120, 120)
                                                    pdf.set_font("Arial", 'I', 9)
                                                    pdf.cell(0, 6, f"Horário de Agendamento: {limpa(horario_pref)}", border=0, ln=True, align='R')
                                                    pdf.ln(4)
                                                    
                                                    # --- FUNÇÃO TÁTICA PARA ALINHAMENTO EM GRADE ---
                                                    def add_linha(label1, val1, label2="", val2="", label3="", val3=""):
                                                        pdf.set_font("Arial", 'B', 9)
                                                        pdf.set_text_color(*COR_PRIMARIA)
                                                        pdf.cell(24, 6, limpa(label1), border=0)
                                                        pdf.set_font("Arial", '', 9)
                                                        pdf.set_text_color(*COR_TEXTO)
                                                        pdf.cell(66, 6, limpa(val1), border=0)
                                                        
                                                        if label2:
                                                            pdf.set_font("Arial", 'B', 9)
                                                            pdf.set_text_color(*COR_PRIMARIA)
                                                            pdf.cell(22, 6, limpa(label2), border=0)
                                                            pdf.set_font("Arial", '', 9)
                                                            pdf.set_text_color(*COR_TEXTO)
                                                            pdf.cell(38, 6, limpa(val2), border=0)
                                                            
                                                        if label3:
                                                            pdf.set_font("Arial", 'B', 9)
                                                            pdf.set_text_color(*COR_PRIMARIA)
                                                            pdf.cell(15, 6, limpa(label3), border=0)
                                                            pdf.set_font("Arial", '', 9)
                                                            pdf.set_text_color(*COR_TEXTO)
                                                            pdf.cell(25, 6, limpa(val3), border=0)
                                                        pdf.ln(6)

                                                    # --- SEÇÃO 1: PACIENTE ---
                                                    pdf.set_fill_color(*COR_FUNDO)
                                                    pdf.set_text_color(*COR_PRIMARIA)
                                                    pdf.set_font("Arial", 'B', 10)
                                                    pdf.cell(0, 8, "  1. IDENTIFICAÇÃO DO PACIENTE", border=0, ln=True, align='L', fill=True)
                                                    pdf.ln(2)
                                                    
                                                    add_linha("NOME:", nome_pac, "CPF:", cpf_pac, "NASC:", dt_nasc.strftime('%d/%m/%Y'))
                                                    add_linha("NIP/SARAM/FUSEX:", nip_pac, "RG:", f"{rg} {emissor}", "SEXO:", sexo)
                                                    add_linha("MÃE:", nome_mae, "PAI:", nome_pai)
                                                    add_linha("EST. CIVIL:", est_civil, "NACIONAL.:", nac, "COR:", cor)
                                                    pdf.ln(4)

                                                    # --- SEÇÃO 2: CONTATO E ENDEREÇO ---
                                                    pdf.set_fill_color(*COR_FUNDO)
                                                    pdf.set_text_color(*COR_PRIMARIA)
                                                    pdf.set_font("Arial", 'B', 10)
                                                    pdf.cell(0, 8, "  2. CONTATO E ENDEREÇO", border=0, ln=True, align='L', fill=True)
                                                    pdf.ln(2)

                                                    add_linha("ENDEREÇO:", f"{end}, {bairro}", "CIDADE:", f"{cidade}/{uf}", "CEP:", cep)
                                                    add_linha("CELULAR:", celular, "E-MAIL:", email)
                                                    pdf.ln(4)

                                                    # --- SEÇÃO 3: RESPONSÁVEL ---
                                                    pdf.set_fill_color(*COR_FUNDO)
                                                    pdf.set_text_color(*COR_PRIMARIA)
                                                    pdf.set_font("Arial", 'B', 10)
                                                    pdf.cell(0, 8, "  3. IDENTIFICAÇÃO DO RESPONSÁVEL", border=0, ln=True, align='L', fill=True)
                                                    pdf.ln(2)

                                                    add_linha("NOME:", resp_nome, "POSTO/GRAD:", resp_posto, "OM:", resp_om)
                                                    add_linha("CELULAR:", resp_cel, "TRABALHO:", resp_trab)
                                                    pdf.ln(12)

                                                    # --- RODAPÉ DE AUTENTICIDADE ---
                                                    pdf.set_draw_color(*COR_PRIMARIA)
                                                    pdf.set_line_width(0.5)
                                                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                                                    pdf.ln(4)
                                                    pdf.set_text_color(150, 150, 150)
                                                    pdf.set_font("Arial", 'I', 8)
                                                    pdf.multi_cell(0, 4, "Documento gerado eletronicamente pelo Sistema Integrado de Gestão Assistencial (SIGA).\nEste impresso é de uso interno e serve como documento auxiliar de identificação e tramitação.", align='C')

                                                    # ==========================================
                                                    # GERAÇÃO E DOWNLOAD SEGURO
                                                    # ==========================================
                                                    pdf_bytes = pdf.output(dest='S').encode('latin-1', 'ignore')
                                                    b64 = base64.b64encode(pdf_bytes).decode()
                                                    nome_arquivo = f"Prontuario_{nip_pac if nip_pac else 'Usuario'}.pdf"
                                        
                                                    btn_html = f'''
                                                    <a href="data:application/pdf;base64,{b64}" download="{nome_arquivo}"
                                                        style="display: block; text-align: center; background-color: #00E676;
                                                                color: #1e1e1e; padding: 12px; border-radius: 8px; font-weight: bold;
                                                                text-decoration: none; margin-top: 15px; font-family: sans-serif;
                                                                box-shadow: 0 4px 6px rgba(0, 230, 118, 0.2);">
                                                        📥 PRONTUÁRIO GERADO! CLIQUE AQUI PARA BAIXAR
                                                    </a>
                                                    '''
                                                    st.markdown(btn_html, unsafe_allow_html=True)
                                            else:
                                                st.warning("Preencha ao menos o Nome do Paciente e escolha o Horário para gerar o documento.")


                                        st.markdown("<h5 style='color: #00E676; margin-top: 15px;'> DOCUMENTAÇÃO OBRIGATÓRIA</h5>", unsafe_allow_html=True)
                                        pdf_file = st.file_uploader("Anexar Pedido Médico / Guia (PDF)", type=["pdf"], key=f"pdf_{id_dem}")
                                        
                                        st.markdown("<br>", unsafe_allow_html=True)
                                        

                            # --- REGRA DE NEGÓCIO: STATUS 3 EM DIANTE (Análise do SAME) ---
                            elif status_atual >= 3:
                                if status_atual == 3:
                                    st.info("📄 Documentação protocolada. Aguardando análise do SAME.")
                                
                                # Botão visual para baixar o PDF anexado
                                url_pdf = row.get('url_pdf_temporario')
                                if url_pdf:
                                    st.markdown(f'''
                                    <a href="{url_pdf}" target="_blank"
                                       style="display: block; text-align: center; border: 2px solid #00E676;
                                              color: #00E676; padding: 10px; border-radius: 5px; font-weight: bold;
                                              text-decoration: none; margin-bottom: 15px; background-color: #1a1a1a;">
                                        📥 VISUALIZAR DOCUMENTAÇÃO ANEXADA (PDF)
                                    </a>
                                    ''', unsafe_allow_html=True)
                                
                                # Ações exclusivas para a OM Ofertante (SAME) durante o Status 3
                                if status_atual == 3 and papel == "OFERTANTE (AVALIADOR)":
                                    st.divider()
                                    st.markdown("#### ⚙️ Decisão do SAME")
                                    c_btn1, c_btn2 = st.columns(2)
                                    
                                    if c_btn1.button("✅ CONFIRMAR AGENDAMENTO", key=f"agendar_{id_dem}", use_container_width=True):
                                        with st.spinner("Confirmando agendamento..."):
                                            supabase.table("demandas").update({"status": 4}).eq("id_demanda", id_dem).execute()
                                            supabase.table("logs_demandas").insert({"id_demanda": id_dem, "status_anterior": 3, "status_novo": 4, "cpf_operador": st.session_state.user_nip}).execute()
                                            st.rerun()
                                            
                                    if c_btn2.button("❌ CANCELAR / DEVOLVER", key=f"canc_same_{id_dem}", use_container_width=True):
                                        with st.spinner("Cancelando demanda..."):
                                            supabase.table("demandas").update({"status": 8}).eq("id_demanda", id_dem).execute()
                                            supabase.table("logs_demandas").insert({"id_demanda": id_dem, "status_anterior": 3, "status_novo": 8, "cpf_operador": st.session_state.user_nip}).execute()
                                            st.rerun()

                        # ==========================================
                        # LADO DIREITO: CHAT TÁTICO INTEGRADO
                        # ==========================================
                        with col_chat:
                            st.markdown("#### 💬 Chat da Demanda")
                            
                            # Puxa as mensagens desta demanda específica
                            res_msg = supabase.table("mensagens_chat").select("*").eq("id_demanda", id_dem).order("timestamp_msg", desc=False).execute()
                            
                            # 🎨 CONSTRUÇÃO DO CHAT EM HTML (Sem espaços no início para o Streamlit não bugar)
                            html_chat = "<div style='height: 300px; overflow-y: auto; border: 2px solid #00E676; box-shadow: 0 0 15px rgba(0, 230, 118, 0.3); border-radius: 8px; padding: 15px; background-color: #1a1a1a; margin-bottom: 15px;'>"
                            
                            if not res_msg.data:
                                html_chat += "<p style='text-align: center; color: #555555; font-style: italic; margin-top: 100px;'>Nenhuma mensagem enviada ainda...</p>"
                            else:
                                for msg in res_msg.data:
                                    eh_minha = msg['uasg_remetente'] == st.session_state.uasg_logada
                                    alinhamento = "right" if eh_minha else "left"
                                    cor_fundo = "#00E676" if eh_minha else "#4c4955"
                                    cor_texto = "#231f20" if eh_minha else "#ffffff"
                                    
                                    # Puxa o nome do banco
                                    nome_exibicao = msg.get('nome_operador') if msg.get('nome_operador') else 'Operador SIGA'
                                    
                                    # Monta os balões em blocos únicos (impede a quebra do Markdown)
                                    html_chat += f"<div style='text-align: {alinhamento}; margin-bottom: 12px;'>"
                                    html_chat += f"<div style='font-size: 10px; color: #aaaaaa; margin-bottom: 3px; font-weight: bold;'>{nome_exibicao}</div>"
                                    html_chat += f"<div style='display: inline-block; background-color: {cor_fundo}; color: {cor_texto}; padding: 8px 12px; border-radius: 8px; max-width: 85%; font-size: 13px; text-align: left;'>{msg['texto']}</div>"
                                    html_chat += "</div>"
                            
                            html_chat += "</div>" # Fecha a caixa com borda neon
                            
                            # Renderiza a caixa inteira na tela
                            st.markdown(html_chat, unsafe_allow_html=True)
                            
                            # Campo de envio de nova mensagem
                            nova_msg = st.text_input("Escreva uma mensagem...", key=f"txt_msg_{id_dem}")
                            
                            # Botão em maiúsculo para combinar com o layout
                            if st.button("ENVIAR MENSAGEM", key=f"btn_msg_{id_dem}", use_container_width=True):
                                if nova_msg.strip():
                                    supabase.table("mensagens_chat").insert({
                                        "id_demanda": id_dem,
                                        "uasg_remetente": st.session_state.uasg_logada,
                                        "texto": nova_msg,
                                        "nome_operador": st.session_state.user_full_name
                                    }).execute()
                                    st.rerun()

        except Exception as e:
            st.error(f"Erro ao carregar o painel de tramitação: {e}")

    with tab_indicadores:
        st.subheader("Painel de Indicadores (Tempo de Resposta)")
        st.write("Gráficos baseados na tabela de Logs de movimentação.")

    with tab_contato:
        st.subheader("Suporte e Gestão do Sistema")
        st.write("Chat integrado e contato direto com os desenvolvedores do SIGA.")