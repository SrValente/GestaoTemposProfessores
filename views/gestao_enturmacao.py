import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import urllib3
import time
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
BASE_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/api/framework/v1/consultaSQLServer/RealizaConsulta"
SOAP_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer"
MAPA_DIAS = {1: "Dom", 2: "Seg", 3: "Ter", 4: "Qua", 5: "Qui", 6: "Sex", 7: "Sab"}

def consultar_rm(sentenca, parametros=""):
    url = f"{BASE_URL}/{sentenca}/0/S"
    try:
        params = {"parameters": parametros} if parametros else {}
        resp = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD), params=params, verify=False, timeout=20)
        return pd.DataFrame(resp.json()) if resp.status_code == 200 else pd.DataFrame()
    except: return pd.DataFrame()

def soap_request(dataserver, xml_content, acao="SaveRecord"):
    xml = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
       <soapenv:Body>
          <tot:{acao}>
             <tot:DataServerName>{dataserver}</tot:DataServerName>
             <tot:XML><![CDATA[{xml_content}]]></tot:XML>
             <tot:Contexto>CODCOLIGADA=8;CODSISTEMA=S;CODUSUARIO={USERNAME}</tot:Contexto>
          </tot:{acao}>
       </soapenv:Body>
    </soapenv:Envelope>"""
    headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f"http://www.totvs.com/IwsDataServer/{acao}"}
    return requests.post(SOAP_URL, data=xml.encode('utf-8'), headers=headers, auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False, timeout=30)

@st.cache_data(ttl=600)
def carregar_listas():
    turmas = consultar_rm("SMP.0042", "CODCOLIGADA=8;CODPERLET=2026")
    professores = consultar_rm("SMP.0060")
    return turmas, professores

def show():
    st.title("🎓 Gestão de Enturmação Express")
    st.markdown("<p style='color: var(--text-color); opacity: 0.8;'>Preencha as informações para a substituição ou enturmação de professores nas disciplinas.</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    with st.spinner("Carregando Dados..."):
        df_turmas, df_lista_prof = carregar_listas()
    
    if not df_turmas.empty:
        c1, c2 = st.columns(2)
        with c1:
            unidade = st.selectbox("📍 Unidade", sorted(df_turmas['UNIDADE'].unique()))
            df_unidade = df_turmas[df_turmas['UNIDADE'] == unidade].copy()
        with c2:
            df_unidade['LABEL'] = df_unidade['CODTURMA'] + " - " + df_unidade['DISCIPLINA']
            turma_sel = st.selectbox("📚 Turma / Disciplina", df_unidade['LABEL'].unique())
            id_turma_disc = str(df_unidade[df_unidade['LABEL'] == turma_sel].iloc[0]['IDTURMADISC'])

        st.divider()
        
        # Busca Horários
        df_grade = consultar_rm("SMP.0050", f"CODCOLIGADA=8;IDTURMADISC={id_turma_disc}")
        
        if not df_grade.empty:
            df_grade['DIA_NOME'] = df_grade['DIASEMANA'].map(MAPA_DIAS)
            df_grade['SELECIONAR'] = False
            grade_editada = st.data_editor(
                df_grade[['SELECIONAR', 'DIA_NOME', 'HORAINICIAL', 'HORAFINAL', 'PROFESSOR_ATUAL']], 
                hide_index=True, use_container_width=True
            )

            st.subheader("👤 Substituição")
            
            # Selectbox com busca de professores
            cod_prof_novo = None
            if not df_lista_prof.empty:
                df_lista_prof['LABEL_PROF'] = df_lista_prof['NOME'] + " (" + df_lista_prof['CODPROF'].astype(str) + ")"
                prof_selecionado = st.selectbox("Selecione o Novo Professor", sorted(df_lista_prof['LABEL_PROF'].unique()), index=None)
                if prof_selecionado:
                    cod_prof_novo = prof_selecionado.split("(")[-1].replace(")", "").strip()
            else:
                cod_prof_novo = st.text_input("Código do Professor (Manual)").strip()

            if st.button("🚀 EXECUTAR SUBSTITUIÇÃO", use_container_width=True):
                selecionados = grade_editada[grade_editada['SELECIONAR'] == True]
                
                if selecionados.empty or not cod_prof_novo:
                    st.warning("⚠️ Selecione os horários e o professor.")
                else:
                    status = st.empty()
                    hoje = datetime.now()
                    dt_inicio = hoje.replace(day=1).strftime('%Y-%m-%dT00:00:00')
                    dt_fim = "2027-01-31T00:00:00"

                    status.info("Passo 1/3: Verificando se o professor já está na turma...")
                    df_vinculo = consultar_rm("SMP.0051", f"CODCOLIGADA=8;IDTURMADISC={id_turma_disc}")
                    id_pt_novo = None
                    if not df_vinculo.empty:
                        match = df_vinculo[df_vinculo['CODPROF'].astype(str) == str(cod_prof_novo)]
                        if not match.empty:
                            id_pt_novo = match.iloc[0]['IDPROFESSORTURMA']

                    if not id_pt_novo:
                        status.info("Criando novo vínculo do professor na turma...")
                        xml_pt = f"""
                        <EduProfessorTurmaData>
                          <SPROFESSORTURMA>
                            <CODCOLIGADA>8</CODCOLIGADA>
                            <IDPROFESSORTURMA>0</IDPROFESSORTURMA>
                            <IDTURMADISC>{id_turma_disc}</IDTURMADISC>
                            <CODPROF>{cod_prof_novo}</CODPROF>
                            <DTINICIO>{dt_inicio}</DTINICIO>
                            <DTFIM>{dt_fim}</DTFIM>
                            <TIPOPROF>T</TIPOPROF>
                            <STATUS>1</STATUS>
                            <COMPOESALARIO>S</COMPOESALARIO>
                          </SPROFESSORTURMA>
                          <SPROFESSORTURMACOMPL>
                            <CODCOLIGADA>8</CODCOLIGADA>
                            <IDPROFESSORTURMA>0</IDPROFESSORTURMA>
                          </SPROFESSORTURMACOMPL>
                        </EduProfessorTurmaData>"""
                        
                        resp = soap_request("EduProfessorTurmaData", xml_pt)
                        time.sleep(4) 
    
                        df_vinculo = consultar_rm("SMP.0051", f"CODCOLIGADA=8;IDTURMADISC={id_turma_disc}")
                        if not df_vinculo.empty:
                            match = df_vinculo[df_vinculo['CODPROF'].astype(str) == str(cod_prof_novo)]
                            if not match.empty:
                                id_pt_novo = match.iloc[0]['IDPROFESSORTURMA']
                    else:
                        status.info("Professor já vinculado. Prosseguindo...")

                    if id_pt_novo:
                        status.success("Vínculo OK! Atualizando horários...")
                        p_bar = st.progress(0)
                        for i, (idx, row) in enumerate(selecionados.iterrows()):
                            id_h = df_grade.loc[idx, 'IDHORARIOTURMA']
                            id_pt_velho = df_grade.loc[idx, 'IDPROFESSORTURMA']
                            
                            if pd.notnull(id_pt_velho) and str(id_pt_velho) == str(id_pt_novo):
                                pass # O professor já está vinculado a este horário
                            else:
                                soap_request("EduHorarioProfessorData", f"<EduHorarioProfessor><SHorarioProfessor><CODCOLIGADA>8</CODCOLIGADA><IDPROFESSORTURMA>{id_pt_novo}</IDPROFESSORTURMA><IDHORARIOTURMA>{id_h}</IDHORARIOTURMA></SHorarioProfessor></EduHorarioProfessor>")
                                if pd.notnull(id_pt_velho):
                                    soap_request("EduHorarioProfessorData", f"<EduHorarioProfessor><SHorarioProfessor><CODCOLIGADA>8</CODCOLIGADA><IDPROFESSORTURMA>{id_pt_velho}</IDPROFESSORTURMA><IDHORARIOTURMA>{id_h}</IDHORARIOTURMA></SHorarioProfessor></EduHorarioProfessor>", "DeleteRecord")
                                    
                            p_bar.progress((i + 1) / len(selecionados))
                        
                        st.success(f"✅ Professor {cod_prof_novo} enturmado com sucesso!")
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Erro crítico: O vínculo não foi encontrado no banco após a criação.")
                        with st.expander("Ver Resposta do WebService"):
                            st.text(resp.text)
    else:
        st.error("Não foi possível carregar as turmas. Verifique a conexão com a API.")
