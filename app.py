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
/* Estilo moderno adaptável ao tema light e dark do Streamlit */
.login-box {
    background-color: var(--secondary-background-color);
    padding: 3rem;
    border-radius: 16px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    border: 1px solid rgba(128, 128, 128, 0.2);
    max-width: 450px;
    margin: 50px auto;
    text-align: center;
}
.stButton > button {
    background: var(--primary-color) !important;
    color: white !important;
    border-radius: 8px !important;
    border: none !important;
    padding: 0.6rem 2rem !important;
    font-weight: bold !important;
    font-size: 16px !important;
    transition: all 0.3s ease !important;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2) !important;
    filter: brightness(1.1);
}
.stTextInput > div > div > input {
    background-color: var(--secondary-background-color) !important;
    color: var(--text-color) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(128, 128, 128, 0.3) !important;
    padding: 10px 15px !important;
    font-size: 16px;
}
.stTextInput > div > div > input:focus {
    border-color: var(--primary-color) !important;
    box-shadow: 0 0 0 2px rgba(128, 128, 128, 0.2) !important;
}
/* Customize tabs */
.stTabs [data-baseweb="tab-list"] {
    background-color: transparent;
    gap: 10px;
}
.stTabs [data-baseweb="tab"] {
    background-color: var(--secondary-background-color);
    border-radius: 8px 8px 0px 0px;
    padding: 10px 20px;
    border: 1px solid rgba(128, 128, 128, 0.2);
    border-bottom: none;
    color: var(--text-color);
}
.stTabs [aria-selected="true"] {
    background-color: transparent !important;
    color: var(--text-color) !important;
    border-top: 2px solid var(--primary-color) !important;
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
            <h2 style="color: var(--primary-color); margin-bottom: 10px; font-weight: 700;">Portal Mestre</h2>
            <p style="color: var(--text-color); opacity: 0.8; margin-bottom: 35px; font-size: 15px;">Acesso restrito ao corpo de Coordenação</p>
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
    st.markdown("<h2 style='text-align: center; color: var(--primary-color); margin-top: 20px;'>Menu Principal</h2>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color: rgba(128,128,128,0.2);'>", unsafe_allow_html=True)
    
    selecao = option_menu(
        menu_title=None,
        options=["Gestão de Enturmação", "Grade Horária", "Atividades Extras", "Consulta de Atividades"],
        icons=["people-fill", "calendar-week-fill", "journal-plus", "search"],
        menu_icon="cast",
        default_index=0,
        styles={
            "container": {"padding": "0!important", "background-color": "transparent"},
            "icon": {"color": "var(--primary-color)", "font-size": "18px"}, 
            "nav-link": {"font-size": "15px", "text-align": "left", "margin":"5px", "--hover-color": "rgba(128,128,128,0.1)", "color": "var(--text-color)"},
            "nav-link-selected": {"background-color": "var(--primary-color)", "color": "white", "font-weight": "bold"},
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
