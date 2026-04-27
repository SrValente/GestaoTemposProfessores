import streamlit as st
from streamlit_option_menu import option_menu
import views.gestao_enturmacao as enturmacao
import views.grade_horaria as grade
import views.gestao_atividades as atividades
import views.consulta_atividades as consulta_atividades

# Configuração da página inicial (deve ser a primeira chamada)
st.set_page_config(page_title="Portal Mestre Educacional", layout="wide", page_icon="🎓")

# Estilização Global CSS
st.markdown("""
<style>
/* Estilo moderno, limpo, focado com paleta elegante */
[data-testid="stAppViewContainer"] {
    background: linear-gradient(145deg, #0f172a 0%, #1e1b4b 100%);
    color: white;
}
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(12px);
    border-right: 1px solid rgba(255, 255, 255, 0.05);
}
h1, h2, h3, h4, p, span {
    color: #f1f5f9;
}
/* Login component styling */
.login-box {
    background: rgba(30, 41, 59, 0.75);
    padding: 3rem;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    border: 1px solid rgba(255,255,255,0.08);
    max-width: 450px;
    margin: 50px auto;
    text-align: center;
    backdrop-filter: blur(8px);
}
.stButton > button {
    background: linear-gradient(90deg, #4f46e5 0%, #6366f1 100%) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.6rem 2rem !important;
    font-weight: bold !important;
    font-size: 16px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 6px rgba(79, 70, 229, 0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(79, 70, 229, 0.45) !important;
    background: linear-gradient(90deg, #4338ca 0%, #4f46e5 100%) !important;
}
.stTextInput > div > div > input {
    background-color: rgba(15, 23, 42, 0.6) !important;
    color: white !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    padding: 10px 15px !important;
    font-size: 16px;
}
.stTextInput > div > div > input:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 2px rgba(129, 140, 248, 0.2) !important;
}
/* Customize tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    gap: 10px;
}
.stTabs [data-baseweb="tab"] {
    background-color: rgba(30, 41, 59, 0.6);
    border-radius: 8px 8px 0px 0px;
    padding: 10px 20px;
    border: 1px solid rgba(255,255,255,0.05);
    border-bottom: none;
    color: #cbd5e1;
}
.stTabs [aria-selected="true"] {
    background-color: rgba(99, 102, 241, 0.2) !important;
    color: white !important;
    border-top: 2px solid #818cf8 !important;
}
</style>
""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.5, 1])
    with c2:
        st.markdown('''
        <div class="login-box">
            <div style="font-size: 50px; margin-bottom: 15px;">🚀</div>
            <h2 style="color: #818cf8; margin-bottom: 10px; font-weight: 700;">Portal Mestre</h2>
            <p style="color: #94a3b8; margin-bottom: 35px; font-size: 15px;">Acesso restrito ao corpo de Coordenação</p>
        </div>
        ''', unsafe_allow_html=True)
        
        # Form block aligned centrally
        st.markdown('<div style="max-width: 450px; margin: auto; transform: translateY(-70px); padding: 0 40px;">', unsafe_allow_html=True)
        pwd = st.text_input("🔑 Chave de Segurança", type="password", placeholder="Insira a chave de acesso...", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Autenticar Acesso", use_container_width=True):
            if pwd == "I2E32IZE233IE":
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("⚠️ Chave de acesso inválida!")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Área após Autenticação
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #818cf8; margin-top: 20px;'>Menu Principal</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
    
    selecao = option_menu(
        menu_title=None,
        options=["Gestão de Enturmação", "Grade Horária", "Atividades Extras", "Consulta de Atividades"],
        icons=["people-fill", "calendar-week-fill", "journal-plus", "search"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "#818cf8", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "rgba(255,255,255,0.1)", "color": "#e2e8f0"},
            "nav-link-selected": {"background-color": "#4f46e5", "color": "white", "font-weight": "bold"},
        }
    )
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    if st.button("🚪 Encerrar Sessão", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# Roteamento das Páginas
if selecao == "Gestão de Enturmação":
    enturmacao.show()
elif selecao == "Grade Horária":
    grade.show()
elif selecao == "Atividades Extras":
    atividades.show()
elif selecao == "Consulta de Atividades":
    consulta_atividades.show()
