import streamlit as st
import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
from xml.sax.saxutils import escape
from datetime import datetime
import urllib3
import io

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

USERNAME = st.secrets["USERNAME"]
PASSWORD = st.secrets["PASSWORD"]
SOAP_URL = "https://raizeducacao160286.rm.cloudtotvs.com.br:8051/wsDataServer/IwsDataServer"

ATIVIDADES_MAP = {
    "REUNIÕES": {
        "184 - ATIVIDADES PEDAGOGICAS REUNIÃO EF I": 184, "185 - ATIVIDADES PEDAGOGICAS REUNIÃO EF II": 185,
        "186 - ATIVIDADES PEDAGOGICAS REUNIÃO EM": 186, "187 - ATIVIDADES PEDAGOGICAS REUNIÃO EM 3ª": 187,
    },
    "AULAS EXTRAS": {
        "188 - AULA EXTRA CURSO": 188, "189 - AULA EXTRA ED INFANTIL": 189, "190 - AULA EXTRA EFI": 190,
        "191 - AULA EXTRA EFII": 191, "192 - AULA EXTRA EM": 192, "193 - AULA EXTRA PREVEST": 193, "194 - AULA EXTRA VL": 194,
    },
    "ATIVIDADES PEDAGÓGICAS EXTRAS": {
        "179 - ATIVIDADES PEDAGOGICAS EXTRA ED INFANTIL": 179, "180 - ATIVIDADES PEDAGOGICAS EXTRA EFI": 180,
        "181 - ATIVIDADES PEDAGOGICAS EXTRA EFII": 181, "182 - ATIVIDADES PEDAGOGICAS EXTRA EM": 182, "183 - ATIVIDADES PEDAGOGICAS EXTRA EM 3ª": 183,
    },
    "SUBSTITUIÇÃO DE PROFESSOR": {
        "219 - SUBSTITUIÇÃO PROFESSOR EF I": 219, "220 - SUBSTITUIÇÃO PROFESSOR EF II": 220, "221 - SUBSTITUIÇÃO PROFESSOR EM": 221, "222 - SUBSTITUIÇÃO PROFESSOR EM 3ª": 222,
    },
    "FALTAS (Sem atestado)": {
        "204 - FALTA COLEGIO": 204, "205 - FALTA CURSO": 205, "206 - FALTA ED INFANTIL": 206, "207 - FALTA EFI": 207,
        "208 - FALTA EFII": 208, "209 - FALTA ELETIVA": 209, "210 - FALTA EM": 210, "211 - FALTA EM 3ª": 211, "212 - FALTA PRE VEST": 212,
    },
    "OUTROS": {
        "203 - CORREÇÃO DE PROVAS E REDAÇÕES": 203, "202 - COORDENAÇÃO DE MATERIA": 202,
    },
    "CARGAS COMPLEMENTARES": {
        "195 - CARGA HORARIA BILINGUE": 195, "196 - CARGA HORARIA ED INFANTIL COMPLEMENTAR": 196, "197 - CARGA HORARIA EFI COMPLEMENTAR": 197,
        "198 - CARGA HORARIA EFII COMPLEMENTAR": 198, "199 - CARGA HORARIA EM 3ª COMPLEMENTAR": 199, "200 - CARGA HORARIA EM COMPLEMENTAR": 200, "201 - CARGA HORARIA PRE VEST COMPLEMENTAR": 201,
    },
    "JANELAS": {
        "213 - JANELA ED INFANTIL": 213, "214 - JANELA EF I": 214, "215 - JANELA EF II": 215, "216 - JANELA EM": 216,
        "217 - JANELA EM 3ª": 217, "218 - JANELA PRE VEST": 218,
    }
}

def formatar_decimal_totvs(valor):
    try: return "{:.2f}".format(float(valor)).replace('.', ',')
    except: return "0,00"

def obter_filiais():
    return [
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO BANGU", "CODCOLIGADA": 8, "CODFILIAL": 4},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO CAMPO GRANDE", "CODCOLIGADA": 8, "CODFILIAL": 2},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO DUQUE DE CAXIAS", "CODCOLIGADA": 8, "CODFILIAL": 6},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO MADUREIRA", "CODCOLIGADA": 8, "CODFILIAL": 9},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO NOVA IGUACU", "CODCOLIGADA": 8, "CODFILIAL": 5},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO RETIRO DOS ARTISTAS", "CODCOLIGADA": 8, "CODFILIAL": 10},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO ROCHA MIRANDA", "CODCOLIGADA": 8, "CODFILIAL": 1},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO SÃO JOÃO DE MERITI", "CODCOLIGADA": 8, "CODFILIAL": 8},
        {"NOMEFANTASIA": "COLEGIO E CURSO MATRIZ EDUCACAO TAQUARA", "CODCOLIGADA": 8, "CODFILIAL": 3},
        {"NOMEFANTASIA": "COLÉGIO E CURSO MATRIZ EDUCACAO TIJUCA", "CODCOLIGADA": 8, "CODFILIAL": 11},
    ]

def executar_soap(metodo, xml_interno, primary_key=None, cod_coligada=8):
    if metodo == "ReadRecord":
        corpo = f"<tot:ReadRecord><tot:DataServerName>EduAtividadeProfessorData</tot:DataServerName><tot:PrimaryKey>{primary_key}</tot:PrimaryKey>"
    else:
        corpo = f"<tot:SaveRecord><tot:DataServerName>EduAtividadeProfessorData</tot:DataServerName><tot:XML><![CDATA[{xml_interno}]]></tot:XML>"

    envelope = f"""
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:tot="http://www.totvs.com/">
       <soapenv:Header/>
       <soapenv:Body>
          {corpo}
             <tot:Contexto>CODCOLIGADA={cod_coligada};CODSISTEMA=S;CODUSUARIO={USERNAME}</tot:Contexto>
          {"</tot:ReadRecord>" if metodo == "ReadRecord" else "</tot:SaveRecord>"}
       </soapenv:Body>
    </soapenv:Envelope>
    """
    headers = {"Content-Type": "text/xml; charset=utf-8", "SOAPAction": f"http://www.totvs.com/IwsDataServer/{metodo}"}
    try:
        return requests.post(SOAP_URL, data=envelope.encode('utf-8'), headers=headers, auth=HTTPBasicAuth(USERNAME, PASSWORD), verify=False, timeout=30)
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        return None

def gerar_template_excel():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_vazio = pd.DataFrame(columns=[
            'CODPROF', 'NOME_FILIAL', 'ATIVIDADE_EXTRA', 'DESCRICAO', 
            'CARGAHORARIA', 'VALORHORA', 'DTINICIO', 'DTTERMINO', 'COMPOESALARIO'
        ])
        df_vazio.to_excel(writer, sheet_name='Lancamentos', index=False)
        workbook = writer.book
        worksheet = writer.sheets['Lancamentos']
        
        filiais_nomes = [f["NOMEFANTASIA"] for f in obter_filiais()]
        atividades_nomes = []
        for cat in ATIVIDADES_MAP:
            atividades_nomes.extend(list(ATIVIDADES_MAP[cat].keys()))
            
        worksheet.data_validation('B2:B500', {'validate': 'list', 'source': filiais_nomes})
        worksheet.data_validation('C2:C500', {'validate': 'list', 'source': atividades_nomes})
        worksheet.data_validation('I2:I500', {'validate': 'list', 'source': ['S', 'N']})
        
        header_format = workbook.add_format({'bold': True, 'bg_color': '#D7E4BC'})
        for col_num, value in enumerate(df_vazio.columns.values):
            worksheet.write(0, col_num, value, header_format)
        worksheet.set_column('A:I', 25)
    return output.getvalue()

def show():
    st.title("👨‍🏫 Gestão de Atividades do Professor")
    st.markdown("<p style='color: #94a3b8;'>Gerencie o lançamento de atividades extras, faltas, reuniões e substituições para o corpo docente.</p>", unsafe_allow_html=True)
    st.markdown("---")

    tab_cadastro, tab_lote, tab_consulta = st.tabs(["➕ Novo Lançamento", "🚀 Lote via Planilha", "🔍 Consultar"])

    with tab_cadastro:
        filiais = obter_filiais()
        nome_filial_sel = st.selectbox("🏫 Unidade/Filial:", [f["NOMEFANTASIA"] for f in filiais], key="filial_u")
        
        col_c1, col_c2 = st.columns(2)
        cat_sel = col_c1.selectbox("📁 Categoria:", list(ATIVIDADES_MAP.keys()), key="cat_u")
        ativ_sel = col_c2.selectbox("📝 Atividade:", list(ATIVIDADES_MAP[cat_sel].keys()), key="ativ_u")
        
        with st.form("form_unico"):
            chapa = st.text_input("Chapa do Professor (CODPROF)", placeholder="Ex: 1355")
            
            f1, f2, f3, f4 = st.columns(4)
            c_horaria = f1.number_input("Carga Horária", value=1.0, step=0.5, format="%.2f")
            v_hora = f2.number_input("Valor Hora", value=0.0, step=1.0, format="%.2f")
            remunera = f3.selectbox("Remunerada?", ["Sim", "Não"])
            compoe = f4.selectbox("Compõe Salário?", ["Não", "Sim"])
            
            d1, d2 = st.columns(2)
            dt_ini = d1.date_input("Data Início", datetime.today().replace(day=1))
            dt_fim = d2.date_input("Data Término", datetime.today())
            
            obs = st.text_area("Descrição/Observações")
            
            if st.form_submit_button("🚀 Enviar para o RM", use_container_width=True):
                if not chapa:
                    st.warning("⚠️ Informe a chapa do professor.")
                else:
                    f_info = next(f for f in filiais if f["NOMEFANTASIA"] == nome_filial_sel)
                    id_ext = ATIVIDADES_MAP[cat_sel][ativ_sel]
                    
                    xml_save = f"""
                    <EduAtividadeProfessor>
                        <SAtividadeProfessor>
                            <CODCOLIGADA>{f_info['CODCOLIGADA']}</CODCOLIGADA>
                            <IDATIVIDADEPROF>-1</IDATIVIDADEPROF>
                            <CODPROF>{chapa}</CODPROF>
                            <IDATIVIDADEEXTRA>{id_ext}</IDATIVIDADEEXTRA>
                            <DESCRICAO>{escape(obs)}</DESCRICAO>
                            <CARGAHORARIA>{formatar_decimal_totvs(c_horaria)}</CARGAHORARIA>
                            <VALORHORA>{formatar_decimal_totvs(v_hora)}</VALORHORA>
                            <REMUNERADA>{"1" if remunera == "Sim" else "0"}</REMUNERADA>
                            <COMPOESALARIO>{"S" if compoe == "Sim" else "N"}</COMPOESALARIO>
                            <DTINICIO>{datetime.today().replace(day=1).strftime("%Y-%m-%dT00:00:00")}</DTINICIO>
                            <DTTERMINO>{dt_fim.strftime("%Y-%m-%dT00:00:00")}</DTTERMINO>
                            <CODFILIAL>{f_info['CODFILIAL']}</CODFILIAL>
                            <STATUS>1</STATUS>
                        </SAtividadeProfessor>
                    </EduAtividadeProfessor>
                    """
                    with st.spinner("Processando..."):
                        res = executar_soap("SaveRecord", xml_save, cod_coligada=f_info['CODCOLIGADA'])
                        if res and "<SaveRecordResult>" in res.text and ";" in res.text:
                            novo_id = res.text.split("<SaveRecordResult>")[1].split("</SaveRecordResult>")[0].split(";")[1]
                            st.success(f"✅ Registrado com sucesso! ID no RM: {novo_id}")
                        else:
                            st.error("❌ Erro ao salvar.")
                            st.code(res.text if res else "Sem resposta")

    with tab_lote:
        st.subheader("🚀 Processamento por Planilha")
        
        tmp_excel = gerar_template_excel()
        st.download_button(
            label="📥 Baixar Template com Validações",
            data=tmp_excel,
            file_name="Template_Atividades_RM.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.divider()
        upload = st.file_uploader("Carregue a planilha preenchida", type=['xlsx'])
        if upload:
            df_lote = pd.read_excel(upload)
            st.dataframe(df_lote.head())
            
            if st.button("🔥 Iniciar Processamento em Massa", use_container_width=True):
                prog = st.progress(0)
                logs = []
                lista_f = obter_filiais()
                
                mapa_ativ = {}
                for cat in ATIVIDADES_MAP:
                    for n, i in ATIVIDADES_MAP[cat].items():
                        mapa_ativ[n] = i

                for idx, row in df_lote.iterrows():
                    try:
                        f_match = next(f for f in lista_f if f["NOMEFANTASIA"] == row['NOME_FILIAL'])
                        id_ativ_lote = mapa_ativ[row['ATIVIDADE_EXTRA']]
                        
                        xml_l = f"""
                        <EduAtividadeProfessor>
                            <SAtividadeProfessor>
                                <CODCOLIGADA>{f_match['CODCOLIGADA']}</CODCOLIGADA>
                                <IDATIVIDADEPROF>-1</IDATIVIDADEPROF>
                                <CODPROF>{row['CODPROF']}</CODPROF>
                                <IDATIVIDADEEXTRA>{id_ativ_lote}</IDATIVIDADEEXTRA>
                                <DESCRICAO>{escape(str(row['DESCRICAO']))}</DESCRICAO>
                                <CARGAHORARIA>{formatar_decimal_totvs(row['CARGAHORARIA'])}</CARGAHORARIA>
                                <VALORHORA>{formatar_decimal_totvs(row['VALORHORA'])}</VALORHORA>
                                <REMUNERADA>1</REMUNERADA>
                                <COMPOESALARIO>{row['COMPOESALARIO']}</COMPOESALARIO>
                                <DTINICIO>{datetime.today().replace(day=1).strftime("%Y-%m-%dT00:00:00")}</DTINICIO>
                                <DTTERMINO>{pd.to_datetime(row['DTTERMINO']).strftime("%Y-%m-%dT00:00:00")}</DTTERMINO>
                                <CODFILIAL>{f_match['CODFILIAL']}</CODFILIAL>
                                <STATUS>1</STATUS>
                            </SAtividadeProfessor>
                        </EduAtividadeProfessor>
                        """
                        r = executar_soap("SaveRecord", xml_l, cod_coligada=f_match['CODCOLIGADA'])
                        if r and ";" in r.text:
                            n_id = r.text.split("<SaveRecordResult>")[1].split("</SaveRecordResult>")[0].split(";")[1]
                            logs.append({"Linha": idx+2, "Prof": row['CODPROF'], "Status": "✅ Sucesso", "ID": n_id})
                        else:
                            logs.append({"Linha": idx+2, "Prof": row['CODPROF'], "Status": "❌ Erro RM", "ID": "-"})
                    except Exception as e:
                        logs.append({"Linha": idx+2, "Prof": "Erro", "Status": f"❌ Falha: {str(e)}", "ID": "-"})
                    prog.progress((idx + 1) / len(df_lote))
                
                st.table(pd.DataFrame(logs))

    with tab_consulta:
        st.subheader("🔍 Consultar Registro")
        id_q = st.text_input("ID do Registro", value="444")
        if st.button("Procurar", use_container_width=True):
            res_q = executar_soap("ReadRecord", None, primary_key=f"8;{id_q}")
            if res_q: st.code(res_q.text, language='xml')
