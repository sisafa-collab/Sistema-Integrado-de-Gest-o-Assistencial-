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
        border-bottom: 2px solid #bc3c31;
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Estiliza o botão de acesso */
    div.stButton > button {
        background-color: #6c7d6c !important;
        color: #231f20 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 4px !important;
    }
    div.stButton > button:hover {
        background-color: #6ec24c !important;
        color: #ffffff !important;
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

        # Campos de entrada atualizados para NIP
        nip_input = st.text_input("NIP do Operador")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("ACESSAR SISTEMA", use_container_width=True):
            # Simulando validação inicial
            if nip_input == "123" and senha_input == "siga":
                st.session_state.logged_in = True
                st.session_state.user_nip = nip_input
                st.session_state.user_full_name = "Bruno Matheus França Figueiredo"
                st.session_state.uasg_logada = "120000"
                st.session_state.om_nome = "HOSPITAL NAVAL DE BRASÍLIA"
                st.rerun() 
            else:
                st.error("Credenciais inválidas. (Para teste use NIP: 123 | Senha: siga)")

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
        st.subheader("Disponibilização de Vagas e Serviços")
        st.info("Aqui sua OM irá cadastrar quantas consultas, exames e cirurgias pode oferecer às Forças coirmãs.")
        # Espaço para o st.data_editor futuramente

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