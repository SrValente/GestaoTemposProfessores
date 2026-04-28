import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"

def consultar_rm(sentenca, parametros=""):
    url = f"{BASE_URL}/{sentenca}/0/S"
    try:
        params = {"parameters": parametros} if parametros else {}
        resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False, timeout=30)
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
        return pd.DataFrame()
    except:
        return pd.DataFrame()

@st.cache_data(ttl=600)
def carregar_professores():
    df = consultar_rm("SMP.0060")
    if not df.empty:
        df['LABEL_PROF'] = df['NOME'] + " (" + df['CODPROF'].astype(str) + ")"
    return df

def show():
    st.title("📊 Consulta Geral de Atividades")
    st.markdown("<p style='color: var(--text-color); opacity: 0.8;'>Consulte atividades extras lançadas, filtre por mês, visualize relatórios gerais ou refine a busca por professor.</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Carregar professores para o select
    with st.spinner("Carregando lista de professores..."):
        df_professores = carregar_professores()

    # Barra de Filtros
    st.markdown("### 🔎 Filtros de Consulta")
    c1, c2, c3 = st.columns([1, 1, 2])
    
    hoje = datetime.today()
    inicio_mes_atual = hoje.replace(day=1)
    
    dt_inicio = c1.date_input("Data Início", value=inicio_mes_atual)
    dt_fim = c2.date_input("Data Término", value=hoje)
    
    prof_selecionado = None
    if not df_professores.empty:
        opcoes_prof = ["Todos"] + sorted(df_professores['LABEL_PROF'].unique().tolist())
        prof_selecionado = c3.selectbox("Filtrar por Professor", opcoes_prof, index=0)
    else:
        st.warning("Não foi possível carregar a lista de professores.")
        prof_selecionado = "Todos"

    if st.button("🚀 Buscar Lançamentos", use_container_width=True):
        st.divider()
        
        # Formatar as datas para o parâmetro SQL (YYYY-MM-DD)
        dt_ini_str = dt_inicio.strftime('%Y-%m-%d')
        dt_fim_str = dt_fim.strftime('%Y-%m-%d')
        
        parametros = f"DATA_INICIAL={dt_ini_str};DATA_FINAL={dt_fim_str}"

        with st.spinner(f"Buscando atividades entre {dt_ini_str} e {dt_fim_str}..."):
            df_atividades = consultar_rm("SMP.0061", parametros)
            
            if df_atividades.empty:
                st.info("Nenhuma atividade encontrada para este período.")
            else:
                # Merge com dados de professor se disponível para ter o nome
                if not df_professores.empty and 'CODPROF' in df_atividades.columns:
                    # Garantir os tipos de dados para o merge
                    df_atividades['CODPROF'] = df_atividades['CODPROF'].astype(str)
                    df_prof = df_professores[['CODPROF', 'NOME', 'LABEL_PROF']].copy()
                    df_prof['CODPROF'] = df_prof['CODPROF'].astype(str)
                    
                    df_atividades = pd.merge(df_atividades, df_prof, on='CODPROF', how='left')
                else:
                    df_atividades['NOME'] = df_atividades['CODPROF']
                    df_atividades['LABEL_PROF'] = df_atividades['CODPROF']

                # Aplicar filtro de professor no Python caso não seja Todos
                if prof_selecionado != "Todos":
                    df_atividades = df_atividades[df_atividades['LABEL_PROF'] == prof_selecionado]

                if df_atividades.empty:
                    st.warning("Nenhuma atividade encontrada para o professor selecionado neste período.")
                else:
                    # Garantir tipos corretos para cálculos numéricos
                    for col in ['CARGAHORARIA', 'VALORHORA']:
                        if col in df_atividades.columns:
                            df_atividades[col] = pd.to_numeric(df_atividades[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

                    for col in ['DTINICIO', 'DTTERMINO']:
                        if col in df_atividades.columns:
                            df_atividades[col] = pd.to_datetime(df_atividades[col], errors='coerce').dt.strftime('%d/%m/%Y')

                    # Mapear IDATIVIDADEEXTRA para o nome real
                    from views.gestao_atividades import ATIVIDADES_MAP
                    mapa_invertido = {}
                    for cat, itens in ATIVIDADES_MAP.items():
                        for nome, id_val in itens.items():
                            # Limpar a string e pegar a categoria (ou manter completo, fica a seu critério)
                            # O usuário mencionou que as faltas são na verdade "saídas", então manter
                            # a string completa já atende.
                            mapa_invertido[str(id_val)] = f"[{cat}] {nome}"

                    if 'IDATIVIDADEEXTRA' in df_atividades.columns:
                        # Assegurar formato string limpo para não ocorrer ".0"
                        df_atividades['IDATIVIDADEEXTRA_STR'] = pd.to_numeric(df_atividades['IDATIVIDADEEXTRA'], errors='coerce').astype('Int64').astype(str)
                        df_atividades['TIPO_ATIVIDADE'] = df_atividades['IDATIVIDADEEXTRA_STR'].map(mapa_invertido).fillna(df_atividades['IDATIVIDADEEXTRA_STR'])
                    else:
                        df_atividades['TIPO_ATIVIDADE'] = '-'

                    # Colunas para exibir
                    colunas_exibicao = ['IDATIVIDADEPROF', 'NOME', 'CODPROF', 'TIPO_ATIVIDADE', 'DESCRICAO', 'CARGAHORARIA', 'VALORHORA', 'DTINICIO', 'DTTERMINO', 'CODFILIAL', 'STATUS']
                    colunas_disponiveis = [c for c in colunas_exibicao if c in df_atividades.columns]
                    
                    st.success(f"✅ {len(df_atividades)} registros encontrados!")
                    
                    tab1, tab2 = st.tabs(["📋 Gestão Relatório Geral", "👤 Resumo por Professor"])
                    
                    with tab1:
                        st.dataframe(df_atividades[colunas_disponiveis], use_container_width=True, hide_index=True)
                        
                        csv = df_atividades[colunas_disponiveis].to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Baixar Dados (CSV)",
                            data=csv,
                            file_name=f"atividades_{dt_ini_str}_{dt_fim_str}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                    with tab2:
                        if 'CARGAHORARIA' in df_atividades.columns and 'VALORHORA' in df_atividades.columns:
                            df_atividades['VALOR_TOTAL'] = df_atividades['CARGAHORARIA'] * df_atividades['VALORHORA']
                            
                            resumo = df_atividades.groupby(['NOME', 'CODPROF']).agg(
                                TOTAL_REGISTROS=('IDATIVIDADEPROF', 'count'),
                                TOTAL_CARGA_HORARIA=('CARGAHORARIA', 'sum'),
                                VALOR_ESTIMADO=('VALOR_TOTAL', 'sum')
                            ).reset_index()
                            
                            st.write("Resumo consolidado do período selecionado:")
                            st.dataframe(resumo, use_container_width=True, hide_index=True)
                        else:
                            st.info("As colunas 'CARGAHORARIA' e/ou 'VALORHORA' não foram retornadas na consulta para o cálculo de resumo.")
