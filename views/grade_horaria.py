import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib3
from typing import List

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"
SQL_ID_HORARIOS = "SMP.0023"
SQL_ID_LISTA_PROFESSORES = "SMP.0024"
CODCOLIGADA_FIXO = 8

FILIAIS = [
    {"NOME": "BANGU", "CODFILIAL": 4},
    {"NOME": "CAMPO GRANDE", "CODFILIAL": 2},
    {"NOME": "DUQUE DE CAXIAS", "CODFILIAL": 6},
    {"NOME": "MADUREIRA", "CODFILIAL": 9},
    {"NOME": "NOVA IGUAÇU", "CODFILIAL": 5},
    {"NOME": "RETIRO DOS ARTISTAS", "CODFILIAL": 10},
    {"NOME": "ROCHA MIRANDA", "CODFILIAL": 1},
    {"NOME": "SÃO JOÃO DE MERITI", "CODFILIAL": 8},
    {"NOME": "TAQUARA", "CODFILIAL": 3},
    {"NOME": "TIJUCA", "CODFILIAL": 11},
]

def _fazer_requisicao(sql_id: str, parametros: str) -> list:
    url = f"{BASE_URL}/{sql_id}/0/S"
    params = {"parameters": parametros}
    try:
        resp = requests.get(
            url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False, timeout=30
        )
        resp.raise_for_status()
        dados = resp.json()
        return dados if isinstance(dados, list) else []
    except Exception as exc:
        st.error(f"Erro na requisição TOTVS ({sql_id}): {exc}")
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def listar_professores() -> List[str]:
    nomes = set()
    for f in FILIAIS:
        parametros = f"CODCOLIGADA={CODCOLIGADA_FIXO};CODFILIAL={f['CODFILIAL']}"
        dados = _fazer_requisicao(SQL_ID_LISTA_PROFESSORES, parametros)
        if not dados:
            continue
        
        chaves_nome = [k for k in dados[0].keys() if "prof" in k.lower() or "nome" in k.lower()]
        if not chaves_nome:
            continue
            
        chave_nome = chaves_nome[0]
        for item in dados:
            nome_val = item.get(chave_nome)
            if nome_val:
                nomes.add(nome_val.strip())
    return sorted(list(nomes))

def consultar_horarios(nome: str) -> pd.DataFrame:
    parametros = f"NOME_PROFESSOR={nome}"
    dados = _fazer_requisicao(SQL_ID_HORARIOS, parametros)
    
    if not dados:
        return pd.DataFrame()
    
    df = pd.DataFrame(dados)
    df.columns = [str(c).strip().capitalize() for c in df.columns]
    
    mapeamento = {
        "Horario": "Horário", "Segunda": "Segunda-feira", "Terca": "Terça-feira",
        "Terca-feira": "Terça-feira", "Terça": "Terça-feira", "Quarta": "Quarta-feira",
        "Quinta": "Quinta-feira", "Sexta": "Sexta-feira",
    }
    df = df.rename(columns=mapeamento)
    
    ordem_desejada = ["Horário", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira"]
    colunas_finais = [c for c in ordem_desejada if c in df.columns]
    
    if not colunas_finais:
        return df 
    return df[colunas_finais]

def show():
    st.title("📅 Quadro de Horários do Professor")
    st.markdown("<p style='color: #94a3b8;'>Visualize e exporte a grade horária de qualquer professor da rede.</p>", unsafe_allow_html=True)
    st.markdown("---")

    with st.spinner("Carregando lista de professores..."):
        nomes_professores = listar_professores()

    if nomes_professores:
        escolha = st.selectbox(
            "Selecione o Professor:",
            options=["(escolha um professor)"] + nomes_professores,
            index=0
        )
        nome_professor = "" if escolha == "(escolha um professor)" else escolha.strip()
    else:
        nome_professor = st.text_input("Nome do Professor (digite o nome completo):").strip()

    if st.button("🔍 Buscar Horários", use_container_width=True):
        if not nome_professor:
            st.warning("⚠️ Por favor, selecione ou digite o nome de um professor.")
        else:
            with st.spinner(f"Consultando horários para {nome_professor}..."):
                df_horarios = consultar_horarios(nome_professor)
            
            if df_horarios.empty:
                st.warning(f"🚫 Nenhum horário encontrado para o professor '{nome_professor}'.")
            else:
                st.success(f"Quadro de Horários: {nome_professor}")
                
                # Exibição da Tabela Organizada
                st.dataframe(df_horarios, use_container_width=True, hide_index=True)
                
                # Botão de Download
                csv = df_horarios.to_csv(index=False, sep=";").encode("utf-8")
                st.download_button(
                    label="📥 Baixar Horário em CSV",
                    data=csv,
                    file_name=f"horario_{nome_professor.replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
