import streamlit as st
import pandas as pd
import os 
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client


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
    /* Força o fundo escuro e o texto claro na aplicação inteira */
    [data-testid="stAppViewContainer"] {
        background-color: #231f20;
        color: #f8f9fa;
    }
    [data-testid="stHeader"] {
        background-color: #231f20;
    }
    
    /* Estiliza as abas para combinarem com o fundo escuro */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #332d2e;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4c4955;
        border-bottom: 2px solid #00E676; /* Detalhe neon na aba ativa */
    }

    /* 🎨 Efeito Neon - Verde Tático Chamativo (#00E676) */
    div.stButton > button {
        background-color: transparent !important;
        color: #00E676 !important;
        font-weight: 900 !important;
        border: 2px solid #00E676 !important;
        border-radius: 6px !important;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        /* Cria o brilho (glow) externo e interno */
        box-shadow: 0 0 10px rgba(0, 230, 118, 0.3), inset 0 0 10px rgba(0, 230, 118, 0.1) !important;
        transition: all 0.3s ease-in-out;
    }
    div.stButton > button:hover {
        background-color: #00E676 !important;
        color: #231f20 !important;
        /* Intensifica o brilho ao passar o mouse */
        box-shadow: 0 0 20px rgba(0, 230, 118, 0.8), inset 0 0 15px rgba(0, 230, 118, 0.5) !important;
        border: 2px solid #00E676 !important;
    }
    
    /* Ajuste tático dos campos de digitação (Inputs) */
    .stTextInput input {
        background-color: #332d2e !important;
        color: #00E676 !important;
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
    # --- 3. INTERFACE PRINCIPAL DO SISTEMA ---
    st.markdown(f"### 🏥 {st.session_state.om_nome} | Operador: {st.session_state.user_full_name}")
    st.divider()

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

            # --- PAINEL DE CONSOLIDAÇÃO (Abaixo do formulário) ---
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
            else:
                st.info("Sua OM ainda não disponibilizou vagas no sistema.")
                
        except Exception as e:
            st.error(f"Erro ao sincronizar com o banco de dados: {e}")

    with tab_mapa:
        st.subheader("Mapa Estratégico de Demandas")
        st.write("Selecione um Hospital Militar no mapa para verificar capacidades e agendar demandas.")
        
        # Gerador do Mapa Interativo com Folium
        m = folium.Map(location=[-15.7906, -47.8920], zoom_start=12) # Coordenadas centrais de Brasília
        
        # Marcador de exemplo (HFAB)
        folium.Marker(
            [-15.8658, -47.8860], 
            popup="Hospital de Força Aérea de Brasília (HFAB)", 
            tooltip="Clique para ver capacidades"
        ).add_to(m)
        
        # Marcador de exemplo (HNBra)
        folium.Marker(
            [-15.8080, -47.8800], 
            popup="Hospital Naval de Brasília (HNBra)", 
            tooltip="Clique para ver capacidades"
        ).add_to(m)

        # Renderiza o mapa no Streamlit
        st_data = st_folium(m, width=900, height=500)
        
        if st.button("Simular Solicitação de Demanda"):
            st.success("Demanda registrada e enviada à OM de destino (Status 1).")

    with tab_acompanhamento:
        st.subheader("Painel de Tramitação e PDFs")
        st.write("Acompanhamento das demandas (Status 1 ao 5) e download seguro de guias e prontuários temporários.")

    with tab_indicadores:
        st.subheader("Painel de Indicadores (Tempo de Resposta)")
        st.write("Gráficos baseados na tabela de Logs de movimentação.")

    with tab_contato:
        st.subheader("Suporte e Gestão do Sistema")
        st.write("Chat integrado e contato direto com os desenvolvedores do SIGA.")