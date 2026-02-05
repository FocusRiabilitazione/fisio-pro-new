import streamlit as st
import streamlit.components.v1 as components
from pyairtable import Api
import pandas as pd
import altair as alt
from datetime import date, datetime, timedelta
import io
import os
import base64
import time 

# =========================================================
# 0. CONFIGURAZIONE & STILE
# =========================================================
st.set_page_config(page_title="Gestionale Fisio Pro", page_icon="🏥", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top left, #1a202c, #0d1117);
        color: #e2e8f0;
    }

    section[data-testid="stSidebar"] {
        background-color: rgba(13, 17, 23, 0.95);
        border-right: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(20px);
    }

    h1 {
        font-family: 'Outfit', sans-serif;
        font-weight: 800 !important;
        background: linear-gradient(120deg, #ffffff, #a0aec0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -1px;
        margin-bottom: 10px;
    }
    h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        font-weight: 600 !important;
        color: #f7fafc !important;
        letter-spacing: 0.5px;
    }

    /* KPI CARDS */
    .glass-kpi {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        height: 140px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        margin-bottom: 10px;
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    .glass-kpi:hover {
        transform: translateY(-5px);
        background: rgba(255, 255, 255, 0.06);
    }
    
    .kpi-icon { 
        font-size: 32px;
        margin-bottom: 8px; 
        transition: transform 0.3s ease;
        filter: drop-shadow(0 0 5px rgba(255,255,255,0.3));
    }
    .glass-kpi:hover .kpi-icon { transform: scale(1.1); }

    .kpi-value { font-size: 36px; font-weight: 800; color: white; line-height: 1; letter-spacing: -1px; }
    .kpi-label { font-size: 11px; text-transform: uppercase; color: #a0aec0; margin-top: 8px; letter-spacing: 1.5px; font-weight: 600; }

    /* PULSANTI */
    div[data-testid="column"] .stButton > button {
        background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
        border: none !important;
        color: white !important;
        border-radius: 12px !important;
        font-size: 12px !important;
        font-weight: 600 !important;
        padding: 6px 0 !important;
        box-shadow: 0 4px 10px rgba(66, 153, 225, 0.3) !important;
        transition: all 0.3s ease;
        margin-top: 0px !important;
    }
    div[data-testid="column"] .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(66, 153, 225, 0.5) !important;
    }
    
    /* MODIFICA: Colore Verde per il bottone di aumento */
    button:has(div p:contains("🔺")) {
        border-color: #2ecc71 !important;
        color: #2ecc71 !important;
        background: rgba(46, 204, 113, 0.1) !important;
    }
    button:has(div p:contains("🔺")):hover {
        background: rgba(46, 204, 113, 0.2) !important;
        border-color: #27ae60 !important;
    }

    /* RIGHE AVVISI */
    .alert-row-name {
        background-color: rgba(255, 255, 255, 0.03);
        border-radius: 10px;
        padding: 0 15px;
        height: 42px;    
        display: flex; align-items: center;
        border: 1px solid rgba(255, 255, 255, 0.05);
        font-weight: 600;
        color: #fff; font-size: 14px;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }

    .border-orange { border-left: 4px solid #ed8936 !important; }
    .border-red { border-left: 4px solid #e53e3e !important; }
    .border-blue { border-left: 4px solid #0bc5ea !important; }
    .border-purple { border-left: 4px solid #9f7aea !important; }
    .border-yellow { border-left: 4px solid #ecc94b !important; }
    .border-green { border-left: 4px solid #2ecc71 !important; }
    .border-gray { border-left: 4px solid #a0aec0 !important; }

    /* PULSANTI AZIONE */
    div[data-testid="stHorizontalBlock"] button {
        padding: 2px 12px !important;
        font-size: 11px !important; min-height: 0px !important;
        height: 32px !important; line-height: 1 !important; border-radius: 8px !important;
        margin-top: 6px !important;
        font-weight: 500 !important;
    }
    button[kind="primary"] { background: linear-gradient(135deg, #3182ce, #2b6cb0) !important; border: none !important; color: white !important; }
    button[kind="secondary"] { background: rgba(255, 255, 255, 0.08) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; color: #cbd5e0 !important; }
    button[kind="secondary"]:hover { border-color: #a0aec0 !important; color: white !important; }

    div[data-testid="stDataFrame"] { background: transparent; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; }
    input, select, textarea { background-color: rgba(13, 17, 23, 0.8) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important; color: white !important; border-radius: 8px; }

    div[data-testid="stVerticalBlockBorderWrapper"] { padding: 10px !important; margin-bottom: 5px !important; background-color: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); }
    div[data-testid="stProgress"] > div > div { height: 6px !important; }
    .compact-text { font-size: 13px; color: #cbd5e0; margin: 0; }
</style>
""", unsafe_allow_html=True)

# --- 1. CONNESSIONE ---
API_KEY = None
BASE_ID = None

if "AIRTABLE_TOKEN" in st.secrets:
    API_KEY = st.secrets["AIRTABLE_TOKEN"]
    BASE_ID = st.secrets["AIRTABLE_BASE_ID"]

# Fallback: Se non trova i secrets, chiede input manuale
if not API_KEY or not BASE_ID:
    with st.sidebar:
        with st.expander("⚙️ Configurazione API", expanded=True):
            st.warning("⚠️ Chiavi non trovate nei Secrets.")
            API_KEY = st.text_input("Airtable API Key (pat...)", type="password", key="user_api_key")
            BASE_ID = st.text_input("Base ID (app...)", key="user_base_id")
            
            if not API_KEY or not BASE_ID:
                st.info("Inserisci le chiavi per continuare.")
                st.stop()

api = Api(API_KEY)

# --- 2. FUNZIONI ---
def safe_str(val):
    if val is None: return ""
    if pd.isna(val): return ""
    return str(val).strip()

@st.cache_data(ttl=60)
def get_data(table_name):
    try:
        # --- FIX IMPORTANTE: Rallentamento per evitare errore 429 ---
        time.sleep(0.35) 
        # ------------------------------------------------------------
        table = api.table(BASE_ID, table_name)
        records = table.all()
        if not records: return pd.DataFrame()
        data = [{'id': r['id'], **r['fields']} for r in records]
        return pd.DataFrame(data)
    except Exception as e:
        # Mostra l'errore se serve debug, altrimenti torna vuoto
        st.error(f"Errore caricamento {table_name}: {e}")
        return pd.DataFrame()

def save_paziente(n, c, a, d):
    try: api.table(BASE_ID, "Pazienti").create({"Nome": n, "Cognome": c, "Area": a, "Disdetto": d}, typecast=True); get_data.clear(); return True
    except: return False

def update_generic(tbl, rid, data):
    try:
        clean_data = {}
        for k, v in data.items():
            if v is None: clean_data[k] = None
            elif hasattr(v, 'strftime'): clean_data[k] = v.strftime('%Y-%m-%d')
            else: clean_data[k] = v
        api.table(BASE_ID, tbl).update(rid, clean_data, typecast=True)
        time.sleep(1.0)
        get_data.clear()
        return True
    except: return False

def delete_generic(tbl, rid):
    try: api.table(BASE_ID, tbl).delete(rid); get_data.clear(); return True
    except: return False

def save_preventivo_temp(paziente, dettagli_str, totale, note):
    try: api.table(BASE_ID, "Preventivi_Salvati").create({"Paziente": paziente, "Dettagli": dettagli_str, "Totale": totale, "Note": note, "Data_Creazione": str(date.today())}, typecast=True); get_data.clear(); return True
    except: return False

def save_materiale_avanzato(materiale, area, quantita, obiettivo, soglia):
    try: 
        api.table(BASE_ID, "Inventario").create({
            "Materiali": materiale, 
            "Area": area,
            "Quantità": int(quantita),
            "Obiettivo": int(obiettivo),
            "Soglia_Minima": int(soglia)
        }, typecast=True)
        get_data.clear()
        return True
    except Exception as e: st.error(f"Errore Salvataggio: {e}"); return False

def save_consegna(paziente, area, indicazione, scadenza):
    try:
        api.table(BASE_ID, "Consegne").create({
            "Paziente": paziente, "Area": area, "Indicazione": indicazione, 
            "Data_Scadenza": str(scadenza), "Completato": False
        }, typecast=True)
        get_data.clear(); return True
    except: return False

def save_prestito_new(paziente, oggetto, categoria, data_prestito, data_scadenza):
    try: 
        api.table(BASE_ID, "Prestiti").create({
            "Paziente": paziente, 
            "Oggetto": oggetto,
            "Categoria": categoria, 
            "Data_Prestito": str(data_prestito), 
            "Data_Scadenza": str(data_scadenza),
            "Restituito": False
        }, typecast=True)
        time.sleep(1.0)
        get_data.clear()
        return True
    except Exception as e:
        st.error(f"Errore: {e}")
        return False

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file: return base64.b64encode(img_file.read()).decode()
    except: return ""

# --- PDF GENERATOR ---
def generate_html_preventivo(paziente, data_oggi, note, righe_preventivo, totale_complessivo, logo_b64=None, auto_print=False):
    rows_html = ""
    for r in righe_preventivo:
        rows_html += f"<tr><td>{r['nome']}</td><td class='col-qty'>{r['qty']}</td><td class='col-price'>{r['tot']} €</td></tr>"
    
    header_content = f"<div style='text-align:center;'><img src='data:image/png;base64,{logo_b64}' class='logo-img'></div>" if logo_b64 else "<div class='brand-text-container'><div class='doc-brand-main'>FOCUS</div></div>"
    print_script = "<script>window.print();</script>" if auto_print else ""
    action_bar_style = "display:none;" if auto_print else "display:flex;"
    return f"""
    <!DOCTYPE html> <html lang="it"> <head> <meta charset="UTF-8"> <style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600;700&display=swap');
    body {{ font-family: 'Segoe UI', sans-serif; background: #fff; margin: 0; padding: 20px; color: #000; }}
    .action-bar {{ margin-bottom: 20px; justify-content: flex-end; {action_bar_style} }}
    .btn-download {{ background-color: #333; color: white; border: none; padding: 10px 20px; font-weight: bold; border-radius: 4px; cursor: pointer; }}
    .sheet-a4 {{ width: 210mm; min-height: 296mm; padding: 10mm 15mm; margin: 0 auto; background: white; box-sizing: border-box; position: relative; box-shadow: 0 0 10px rgba(0,0,0,0.1); overflow: hidden; }}
    .logo-img {{ max-width: 150px; height: auto; display: block; margin: 0 auto 5px auto; }}
    .doc-brand-main {{ font-size: 26px; font-weight: 800; text-transform: uppercase; letter-spacing: 2px; color: #000; text-align: center; }}
    .doc-title {{ font-size: 18px; font-weight: 700; text-transform: uppercase; color: #000; border-bottom: 2px solid #000; padding-bottom: 5px; margin-bottom: 15px; margin-top: 10px; }}
    .info-box {{ margin-bottom: 15px; font-size: 13px; display: flex; justify-content: space-between; }}
    .info-label {{ font-weight: bold; color: #000; margin-right: 5px; }}
    .obj-box {{ background-color: #f2f2f2; border-left: 4px solid #333; padding: 10px; margin-bottom: 20px; font-size: 12px; line-height: 1.5; white-space: pre-wrap; }}
    .obj-title {{ font-weight: bold; text-transform: uppercase; display: block; margin-bottom: 3px; font-size: 11px; }}
    table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
    th {{ background-color: #e0e0e0; text-align: left; padding: 6px 8px; text-transform: uppercase; font-size: 10px; font-weight: bold; border-bottom: 1px solid #000; color: #000; }}
    td {{ padding: 6px 8px; border-bottom: 1px solid #ccc; font-size: 12px; vertical-align: middle; }}
    .col-qty {{ text-align: center; width: 10%; }} .col-price {{ text-align: right; width: 20%; }}
    .total-row td {{ font-weight: bold; font-size: 14px; border-top: 2px solid #000; padding-top: 8px; color: #000; }}
    .payment-section {{ border: 1px solid #999; padding: 10px; border-radius: 0; margin-bottom: 20px; }}
    .pay-title {{ font-weight: bold; text-transform: uppercase; font-size: 11px; margin-bottom: 8px; color: #000; }}
    .pay-line {{ display: flex; justify-content: space-between; margin-bottom: 6px; font-size: 12px; }}
    .dotted {{ border-bottom: 1px dotted #000; width: 80px; display: inline-block; }} .dotted-date {{ border-bottom: 1px dotted #000; width: 120px; display: inline-block; }}
    .footer {{ margin-top: 40px; display: flex; justify-content: flex-end; }}
    .sign-box {{ text-align: center; width: 200px; }} .sign-line {{ border-bottom: 1px solid #000; margin-top: 30px; }}
    .page-num {{ position: absolute; bottom: 10mm; left: 15mm; font-size: 9px; color: #666; }}
    @media print {{ @page {{ size: A4; margin: 0; }} body {{ margin: 0; padding: 0; background: none; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }} .action-bar {{ display: none !important; }} .sheet-a4 {{ margin: 0; box-shadow: none; border: none; width: 100%; height: 100%; page-break-after: avoid; page-break-inside: avoid; }} }}
    </style> </head> <body>
    <div class="action-bar"><button class="btn-download" onclick="window.print()">📥 SALVA PDF</button></div>
    <div class="sheet-a4"> {header_content}
    <div class="doc-title">PREVENTIVO PERCORSO RIABILITATIVO</div>
    <div class="info-box"><div><span class="info-label">Paziente:</span> {paziente}</div><div><span class="info-label">Data:</span> {data_oggi}</div></div>
    <div class="obj-box"><span class="obj-title">Obiettivi e Descrizione del Percorso:</span>{note}</div>
    <table><thead><tr><th>Trattamento</th><th class="col-qty">Q.ta</th><th class="col-price">Importo</th></tr></thead><tbody>{rows_html}<tr class="total-row"><td colspan="2" style="text-align:right">TOTALE COMPLESSIVO:</td><td class="col-price">{totale_complessivo} €</td></tr></tbody></table>
    <div class="payment-section"><div class="pay-title">Piano di Pagamento Concordato:</div><div class="pay-line"><span>1) € <span class="dotted"></span></span> <span>entro il <span class="dotted-date"></span></span></div><div class="pay-line"><span>2) € <span class="dotted"></span></span> <span>entro il <span class="dotted-date"></span></span></div><div class="pay-line"><span>3) € <span class="dotted"></span></span> <span>entro il <span class="dotted-date"></span></span></div></div>
    <div class="footer"><div class="sign-box"><div>Firma per accettazione:</div><div class="sign-line"></div></div></div>
    <div class="page-num">Pagina 1</div> </div> {print_script} </body> </html>
    """

# --- 3. INTERFACCIA ---
with st.sidebar:
    LOGO_B64 = ""
    try: 
        st.image("logo.png", use_container_width=True)
        LOGO_B64 = get_base64_image("logo.png")
    except: 
        st.title("Focus Rehab")
        
    menu = st.radio("Menu", ["⚡ Dashboard", "👥 Pazienti", "💳 Preventivi", "📨 Consegne", "📦 Magazzino", "🔄 Prestiti", "📅 Scadenze"], label_visibility="collapsed")
    st.divider(); st.caption("App v102 - Noleggi Smart")

# =========================================================
# DASHBOARD
# =========================================================
if menu == "⚡ Dashboard":
    st.title("⚡ Dashboard")
    st.write("")
    
    # --- PREPARAZIONE DATI ---
    df_pres_alert = get_data("Prestiti")
    # Calcolo Prestiti Scaduti (Solo logica, visualizzazione spostata)
    scaduti = pd.DataFrame()
    if not df_pres_alert.empty:
        if 'Restituito' not in df_pres_alert.columns: df_pres_alert['Restituito'] = False
        if 'Data_Scadenza' not in df_pres_alert.columns: df_pres_alert['Data_Scadenza'] = None
        if 'Oggetto' not in df_pres_alert.columns: df_pres_alert['Oggetto'] = "Strumento"
        if 'Paziente' not in df_pres_alert.columns: df_pres_alert['Paziente'] = "Sconosciuto"
        
        df_pres_alert['Data_Scadenza'] = pd.to_datetime(df_pres_alert['Data_Scadenza'], errors='coerce')
        oggi_ts = pd.Timestamp.now().normalize()
        
        scaduti = df_pres_alert[
            (df_pres_alert['Restituito'] != True) & 
            (df_pres_alert['Data_Scadenza'] < oggi_ts) &
            (df_pres_alert['Data_Scadenza'].notna())
        ]

    if 'kpi_filter' not in st.session_state: st.session_state.kpi_filter = "None"

    df = get_data("Pazienti")
    df_prev = get_data("Preventivi_Salvati")
    df_inv = get_data("Inventario")
    df_cons = get_data("Consegne")
    
    if not df.empty:
        for col in ['Disdetto', 'Visita_Esterna']:
            if col not in df.columns: df[col] = False
            df[col] = df[col].fillna(False)
        for col in ['Data_Disdetta', 'Data_Visita']:
            if col not in df.columns: df[col] = None
            df[col] = pd.to_datetime(df[col], errors='coerce')
        if 'Area' not in df.columns: df['Area'] = None

        totali = len(df)
        df_disdetti = df[ (df['Disdetto'] == True) | (df['Disdetto'] == 1) ]
        cnt_attivi = totali - len(df_disdetti)
        oggi = pd.Timestamp.now().normalize()
        
        limite_recall = oggi - pd.Timedelta(days=7)
        da_richiamare = df_disdetti[ (df_disdetti['Data_Disdetta'].notna()) & (df_disdetti['Data_Disdetta'] <= limite_recall) ]
        df_visite = df[ (df['Visita_Esterna'] == True) | (df['Visita_Esterna'] == 1) ]
        
        curr_week = oggi.isocalendar()[1]
        visite_settimana = df_visite[ df_visite['Data_Visita'].apply(lambda x: x.isocalendar()[1] if pd.notnull(x) else -1) == curr_week ]
        visite_da_reinserire = df_visite[ (df_visite['Data_Visita'].notna()) & (oggi >= (df_visite['Data_Visita'] + pd.Timedelta(days=2))) ]

        cnt_prev = len(df_prev)
        prev_scaduti = pd.DataFrame()
        if not df_prev.empty:
            df_prev['Data_Creazione'] = pd.to_datetime(df_prev['Data_Creazione'], errors='coerce')
            limite_prev = oggi - timedelta(days=7)
            prev_scaduti = df_prev[df_prev['Data_Creazione'] <= limite_prev]

        low_stock = pd.DataFrame()
        if not df_inv.empty:
            if 'Quantità' in df_inv.columns: df_inv = df_inv.rename(columns={'Quantità': 'Quantita'})
            for c in ['Quantita', 'Soglia_Minima', 'Materiali']:
                if c not in df_inv.columns: df_inv[c] = 0
            low_stock = df_inv[df_inv['Quantita'] <= df_inv['Soglia_Minima']]

        consegne_pendenti = pd.DataFrame()
        if not df_cons.empty:
            if 'Completato' not in df_cons.columns: df_cons['Completato'] = False
            if 'Data_Scadenza' not in df_cons.columns: df_cons['Data_Scadenza'] = None
            if 'Paziente' not in df_cons.columns: df_cons['Paziente'] = None
            
            # Fix sicurezza
            if 'Area' not in df_cons.columns: df_cons['Area'] = "Altro"
            
            df_cons = df_cons.dropna(subset=['Paziente'])
            df_cons['Data_Scadenza'] = pd.to_datetime(df_cons['Data_Scadenza'], errors='coerce')
            consegne_pendenti = df_cons[df_cons['Completato'] != True]

        col1, col2, col3, col4, col5 = st.columns(5)
        def draw_kpi(col, icon, num, label, color, filter_key):
            with col:
                st.markdown(f"""<div class="glass-kpi" style="border-bottom: 4px solid {color};"><div class="kpi-icon" style="color:{color};">{icon}</div><div class="kpi-value">{num}</div><div class="kpi-label">{label}</div></div>""", unsafe_allow_html=True)
                if st.button("Vedi Lista", key=f"btn_{filter_key}"): st.session_state.kpi_filter = filter_key

        draw_kpi(col1, "👥", cnt_attivi, "Attivi", "#2ecc71", "Attivi")
        draw_kpi(col2, "📉", len(df_disdetti), "Disdetti", "#e53e3e", "Disdetti")
        draw_kpi(col3, "💡", len(da_richiamare), "Recall", "#ed8936", "Recall")
        draw_kpi(col4, "🩺", len(df_visite), "Visite", "#0bc5ea", "Visite")
        draw_kpi(col5, "💳", cnt_prev, "Preventivi", "#9f7aea", "Preventivi")

        st.write("")
        if st.session_state.kpi_filter != "None":
            st.divider(); c_head, c_close = st.columns([9, 1])
            c_head.subheader(f"📋 Lista: {st.session_state.kpi_filter}")
            if c_close.button("❌"): st.session_state.kpi_filter = "None"; st.rerun()
            df_show = pd.DataFrame()
            if st.session_state.kpi_filter == "Attivi": df_show = df[ (df['Disdetto'] == False) | (df['Disdetto'] == 0) ]
            elif st.session_state.kpi_filter == "Disdetti": df_show = df_disdetti
            elif st.session_state.kpi_filter == "Recall": df_show = da_richiamare
            elif st.session_state.kpi_filter == "Visite": df_show = df_visite
            elif st.session_state.kpi_filter == "Preventivi": df_show = df_prev
            if not df_show.empty: 
                cols_to_show = ['Nome', 'Cognome', 'Area', 'Data_Disdetta', 'Data_Visita']
                if st.session_state.kpi_filter == "Preventivi": cols_to_show = ['Paziente', 'Data_Creazione', 'Totale']
                valid_show = [c for c in cols_to_show if c in df_show.columns]
                st.dataframe(df_show[valid_show], use_container_width=True, height=250)
            else: st.info("Nessun dato.")
            st.divider()

        st.write("")
        st.subheader("🔔 Avvisi e Scadenze")
        
        # 1. DISDETTE / RECALL (Ordine Richiesto: 1)
        if not da_richiamare.empty:
            st.caption(f"📞 Recall Necessari: {len(da_richiamare)}")
            for i, row in da_richiamare.iterrows():
                c_info, c_btn1, c_btn2 = st.columns([3, 1, 1], gap="small")
                with c_info: st.markdown(f"""<div class="alert-row-name border-orange">{row['Nome']} {row['Cognome']}</div>""", unsafe_allow_html=True)
                with c_btn1:
                    if st.button("✅ Rientrato", key=f"rk_{row['id']}", type="primary", use_container_width=True): update_generic("Pazienti", row['id'], {"Disdetto": False, "Data_Disdetta": None}); st.rerun()
                with c_btn2: 
                    if st.button("📅 Rimandare", key=f"pk_{row['id']}", type="secondary", use_container_width=True): update_generic("Pazienti", row['id'], {"Data_Disdetta": str(date.today())}); st.rerun()
        
        if not visite_da_reinserire.empty:
            st.caption(f"🛑 Reinserimento Post-Visita: {len(visite_da_reinserire)}")
            for i, row in visite_da_reinserire.iterrows():
                c_info, c_btn1, c_void = st.columns([3, 1, 1], gap="small")
                with c_info: st.markdown(f"""<div class="alert-row-name border-blue">{row['Nome']} {row['Cognome']} (Visitato il {row['Data_Visita'].strftime('%d/%m')})</div>""", unsafe_allow_html=True)
                with c_btn1:
                    if st.button("✅ Rientrato", key=f"vk_{row['id']}", type="primary", use_container_width=True): update_generic("Pazienti", row['id'], {"Visita_Esterna": False, "Data_Visita": None}); st.rerun()

        # 2. CONSEGNE (Ordine Richiesto: 2)
        if not consegne_pendenti.empty:
            st.caption(f"📨 Consegne in sospeso: {len(consegne_pendenti)}")
            for i, row in consegne_pendenti.iterrows():
                c_info, c_btn1, c_void = st.columns([3, 1, 1], gap="small")
                scad_str = row['Data_Scadenza'].strftime('%d/%m') if pd.notnull(row['Data_Scadenza']) else "N.D."
                with c_info: 
                    st.markdown(f"""<div class="alert-row-name border-gray">{row['Paziente']}: {row['Indicazione']} (Entro: {scad_str})</div>""", unsafe_allow_html=True)
                with c_btn1:
                    if st.button("✅ Fatto", key=f"ok_dash_{row['id']}", type="secondary", use_container_width=True):
                        update_generic("Consegne", row['id'], {"Completato": True})
                        st.rerun()

        # 3. PRESTITI (Ordine Richiesto: 3)
        if not scaduti.empty:
             st.caption(f"⚠️ Prestiti Scaduti: {len(scaduti)}")
             for i, row in scaduti.iterrows():
                data_str = row['Data_Scadenza'].strftime('%d/%m') if pd.notnull(row['Data_Scadenza']) else "N.D."
                st.markdown(f"""<div class="alert-row-name border-red">🔴 {row['Oggetto']} - {row['Paziente']} (Scaduto il {data_str})</div>""", unsafe_allow_html=True)

        # 4. PAGAMENTI / PREVENTIVI SCADUTI (Ordine Richiesto: 4)
        if not prev_scaduti.empty:
            st.caption(f"⏳ Preventivi > 7gg: {len(prev_scaduti)}")
            for i, row in prev_scaduti.iterrows():
                c_info, c_btn1, c_btn2 = st.columns([3, 1, 1], gap="small")
                with c_info: st.markdown(f"""<div class="alert-row-name border-purple">{row['Paziente']} ({row['Data_Creazione'].strftime('%d/%m')})</div>""", unsafe_allow_html=True)
                with c_btn1:
                    if st.button("📞 Rinnova", key=f"ren_{row['id']}", type="primary", use_container_width=True): update_generic("Preventivi_Salvati", row['id'], {"Data_Creazione": str(date.today())}); st.rerun()
                with c_btn2:
                    if st.button("🗑️ Elimina", key=f"del_prev_{row['id']}", type="secondary", use_container_width=True): delete_generic("Preventivi_Salvati", row['id']); st.rerun()

        # 5. INVENTARIO (Ordine Richiesto: 5)
        if not low_stock.empty:
            st.caption(f"⚠️ Prodotti in esaurimento: {len(low_stock)}")
            for i, row in low_stock.iterrows():
                c_info, c_btn, c_void = st.columns([3, 1, 1], gap="small")
                with c_info:
                    mat_name = row.get('Materiali', 'Sconosciuto')
                    st.markdown(f"""<div class="alert-row-name border-yellow">{mat_name} (Qta: {row.get('Quantita',0)})</div>""", unsafe_allow_html=True)
                with c_btn:
                    if st.button("🔄 Riordinato", key=f"restock_{row['id']}", type="primary", use_container_width=True):
                        target = int(row.get('Obiettivo', 5))
                        update_generic("Inventario", row['id'], {"Quantità": target})
                        st.rerun()

        # (Extra) Visite Settimana - in fondo
        if not visite_settimana.empty:
            st.caption(f"📅 Visite questa settimana: {len(visite_settimana)}")
            for i, row in visite_settimana.iterrows():
                st.markdown(f"""<div class="alert-row-name border-blue" style="justify-content: space-between;"><span>{row['Nome']} {row['Cognome']}</span><span style="color:#0bc5ea; font-size:13px;">{row['Data_Visita'].strftime('%A %d/%m')}</span></div>""", unsafe_allow_html=True)
        
        if da_richiamare.empty and visite_da_reinserire.empty and visite_settimana.empty and prev_scaduti.empty and low_stock.empty and consegne_pendenti.empty and scaduti.empty: st.success("Tutto tranquillo! Nessun avviso.")
        
        st.divider()

        # GRAFICO
        st.subheader("📈 Performance Aree")
        df_attivi = df[ (df['Disdetto'] == False) | (df['Disdetto'] == 0) ]
        all_areas = []
        if 'Area' in df_attivi.columns:
            for item in df_attivi['Area'].dropna():
                if isinstance(item, list): all_areas.extend(item)
                elif isinstance(item, str): all_areas.extend([p.strip() for p in item.split(',')])
                else: all_areas.append(str(item))
        
        if all_areas:
            counts = pd.Series(all_areas).value_counts().reset_index()
            counts.columns = ['Area', 'Pazienti']
            domain = ["Mano-Polso", "Muscolo-Scheletrico", "Colonna", "ATM", "Gruppi", "Ortopedico"]
            range_ = ["#0bc5ea", "#9f7aea", "#ecc94b", "#2ecc71", "#e53e3e", "#4a5568"]
            chart = alt.Chart(counts).mark_bar(cornerRadius=6, height=35).encode(
                x=alt.X('Pazienti', axis=None),
                y=alt.Y('Area', sort='-x', title=None, axis=alt.Axis(domain=False, ticks=False, labelColor="#cbd5e0", labelFontSize=14)),
                color=alt.Color('Area', scale=alt.Scale(domain=domain, range=range_), legend=None),
                tooltip=['Area', 'Pazienti']
            ).properties(height=400).configure(background='transparent').configure_view(strokeWidth=0).configure_axis(grid=False)
            st.altair_chart(chart, use_container_width=True, theme=None)
        else: st.info("Dati insufficienti.")

# =========================================================
# SEZIONE 2: PAZIENTI
# =========================================================
elif menu == "👥 Pazienti":
    st.title("Anagrafica Pazienti")
    lista_aree = ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Gruppi", "Ortopedico"]
    
    with st.container(border=True):
        st.subheader("➕ Aggiungi Paziente")
        with st.form("form_paziente", clear_on_submit=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.text_input("Nome", key="new_name", placeholder="Es. Mario")
            c2.text_input("Cognome", key="new_surname", placeholder="Es. Rossi")
            c3.multiselect("Area", lista_aree, key="new_area")
            if st.form_submit_button("Salva Paziente", use_container_width=True, type="primary"):
                if st.session_state.new_name and st.session_state.new_surname:
                    save_paziente(st.session_state.new_name, st.session_state.new_surname, ", ".join(st.session_state.new_area), False)
                    st.success("Paziente salvato!"); st.rerun()
    
    st.write(""); df_original = get_data("Pazienti")
    
    if not df_original.empty:
        for c in ['Disdetto', 'Visita_Esterna', 'Dimissione']:
            if c not in df_original.columns: df_original[c] = False
            df_original[c] = df_original[c].fillna(False).infer_objects(copy=False)
        for c in ['Data_Disdetta', 'Data_Visita']:
            if c not in df_original.columns: df_original[c] = None
            df_original[c] = pd.to_datetime(df_original[c], errors='coerce')
        if 'Area' in df_original.columns: df_original['Area'] = df_original['Area'].apply(lambda x: x[0] if isinstance(x, list) and len(x)>0 else (str(x) if x else "")).str.strip() 
        df_original['Area'] = df_original['Area'].astype("category")
        
        col_search, _ = st.columns([1, 2])
        with col_search: search = st.text_input("🔍 Cerca Paziente", placeholder="Digita il cognome...")
        df_filt = df_original[df_original['Cognome'].astype(str).str.contains(search, case=False, na=False)] if search else df_original
        cols_show = ['Nome', 'Cognome', 'Area', 'Disdetto', 'Data_Disdetta', 'Visita_Esterna', 'Data_Visita', 'Dimissione', 'id']
        valid_cols = [c for c in cols_show if c in df_filt.columns]
        
        edited = st.data_editor(df_filt[valid_cols], column_config={"Disdetto": st.column_config.CheckboxColumn("Disd.", width="small"), "Data_Disdetta": st.column_config.DateColumn("Data Disd.", format="DD/MM/YYYY"), "Visita_Esterna": st.column_config.CheckboxColumn("Visita Ext.", width="small"), "Data_Visita": st.column_config.DateColumn("Data Visita", format="DD/MM/YYYY"), "Dimissione": st.column_config.CheckboxColumn("🗑️", width="small"), "Area": st.column_config.SelectboxColumn("Area Principale", options=lista_aree), "id": None}, disabled=["Nome", "Cognome"], hide_index=True, use_container_width=True, key="editor_main", num_rows="fixed", height=500)
        
        if st.button("💾 Salva Modifiche Tabella", type="primary", use_container_width=True):
            count_upd = 0; count_del = 0
            for i, row in edited.iterrows():
                rec_id = row['id']
                if row.get('Dimissione') == True: delete_generic("Pazienti", rec_id); count_del += 1; continue
                orig = df_original[df_original['id'] == rec_id].iloc[0]; changes = {}
                if row['Disdetto'] != (orig['Disdetto'] in [True, 1]): changes['Disdetto'] = row['Disdetto']
                if str(row['Data_Disdetta']) != str(orig['Data_Disdetta']): changes['Data_Disdetta'] = row['Data_Disdetta']
                if row['Disdetto'] and (pd.isna(row['Data_Disdetta']) or str(row['Data_Disdetta']) == "NaT"): changes['Data_Disdetta'] = pd.Timestamp.now().normalize()
                if row['Visita_Esterna'] != (orig['Visita_Esterna'] in [True, 1]): changes['Visita_Esterna'] = row['Visita_Esterna']
                if str(row['Data_Visita']) != str(orig['Data_Visita']): changes['Data_Visita'] = row['Data_Visita']
                if row['Area'] != orig['Area']: changes['Area'] = row['Area']
                if changes: update_generic("Pazienti", rec_id, changes); count_upd += 1
            if count_upd > 0 or count_del > 0: get_data.clear(); st.toast("Database aggiornato!", icon="✅"); st.rerun()

# =========================================================
# SEZIONE 3: PREVENTIVI
# =========================================================
elif menu == "💳 Preventivi":
    st.title("Preventivi & Proposte")
    tab1, tab2 = st.tabs(["📝 Generatore", "📂 Archivio Salvati"])
    df_srv = get_data("Servizi"); df_paz = get_data("Pazienti"); df_std = get_data("Preventivi_Standard")
    
    if 'prev_note' not in st.session_state: st.session_state.prev_note = ""
    if 'prev_selected_services' not in st.session_state: st.session_state.prev_selected_services = []
    
    listino_dict = {str(r['Servizio']): float(r.get('Prezzo', 0) or 0) for i, r in df_srv.iterrows() if r.get('Servizio')}
    all_services_list = sorted(list(listino_dict.keys()))

    with tab1:
        with st.container(border=True):
            st.subheader("Creazione Nuovo Preventivo")
            
            if not df_std.empty and 'Area' in df_std.columns and 'Nome' in df_std.columns:
                c_filter, c_pack = st.columns(2)
                with c_filter:
                    # FIX TYPE ERROR: ensure all values are strings, filter None, and strip whitespace
                    raw_areas = df_std['Area'].unique()
                    clean_areas = [str(a) for a in raw_areas if pd.notnull(a) and str(a).strip() != ""]
                    aree_std = sorted(list(set(clean_areas))) # set removes duplicates
                    
                    area_sel = st.selectbox("Filtra per Area:", ["-- Tutte --"] + aree_std)
                
                with c_pack:
                    if area_sel != "-- Tutte --": df_std_filtered = df_std[df_std['Area'].astype(str) == area_sel]
                    else: df_std_filtered = df_std
                    
                    # Ensure Names are clean too
                    raw_names = df_std_filtered['Nome'].unique()
                    clean_names = [str(n) for n in raw_names if pd.notnull(n)]
                    nomi_pacchetti = sorted(clean_names)
                    
                    scelta_std = st.selectbox("Carica Pacchetto:", ["-- Seleziona --"] + nomi_pacchetti)

                if scelta_std != "-- Seleziona --":
                    if 'last_std_pkg' not in st.session_state or st.session_state.last_std_pkg != scelta_std:
                        row_std = df_std[df_std['Nome'] == scelta_std].iloc[0]
                        
                        # FIX TEXT_AREA TYPE ERROR: Ensure string, handle None
                        desc_val = row_std.get('Descrizione')
                        st.session_state.prev_note = str(desc_val) if pd.notnull(desc_val) else ""
                        
                        new_services = []
                        content = safe_str(row_std.get('Contenuto'))
                        if content:
                            for p in content.split(','):
                                # Robust split logic (Turn 6 Logic)
                                if ' x' in p:
                                    # Split from right to handle names with "x"
                                    parts = p.rsplit(' x', 1)
                                    if len(parts) == 2:
                                        srv_raw, qty_raw = parts[0].strip(), parts[1].strip()
                                        if srv_raw in all_services_list:
                                            new_services.append(srv_raw)
                                            try:
                                                st.session_state[f"qty_{srv_raw}"] = int(qty_raw)
                                            except:
                                                st.session_state[f"qty_{srv_raw}"] = 1
                        
                        st.session_state.prev_selected_services = new_services
                        st.session_state.last_std_pkg = scelta_std
                        st.rerun()

            nomi_pazienti = ["Seleziona..."] + sorted([f"{r['Cognome']} {r['Nome']}" for i, r in df_paz.iterrows()]) if not df_paz.empty else []
            c_paz, c_serv = st.columns([1, 2])
            
            with c_paz:
                paziente_scelto = st.selectbox("Intestato a:", nomi_pazienti)
            
            with c_serv:
                servizi_scelti = st.multiselect("Trattamenti:", all_services_list, key="prev_selected_services")

            st.write("---")
            st.caption("Strumenti Rapidi Note:")
            
            c_btn1, c_btn2, c_btn3, c_btn4 = st.columns(4)
            
            def append_note(text):
                st.session_state.prev_note += text
            
            if c_btn1.button("🔥 Fase Infiammatoria"): 
                append_note("\n\nFase Infiammatoria: Il primo obiettivo è ridurre l'infiammazione e controllare il dolore, associando la prima fase di riabilitazione alla gestione del movimento e del carico.")
            if c_btn2.button("🤸 Fase Sub-Acuta"): 
                append_note("\n\nFase Sub-Acuta: L'obiettivo è recuperare la completa mobilità e la qualità del movimento, reintroducendo gradualmente i carichi per riabituare i tessuti allo sforzo.")
            if c_btn3.button("💪 Fase Rinforzo"): 
                append_note("\n\nFase Rinforzo: L'obiettivo è recuperare e incrementare la forza e la resistenza dei tessuti interessati, per una ripresa completa delle attività quotidiane e sportive, prevenendo future recidive.")
            if c_btn4.button("🏃 Fase Riatletizzazione"): 
                append_note("\n\nFase Riatletizzazione: L'obiettivo è recuperare il gesto specifico e la performance, lavorando su forza, resistenza ed esplosività per un ritorno allo sport in sicurezza.")
            
            c_prog1, c_prog2 = st.columns([1, 3])
            settimane = c_prog1.number_input("Settimane", 1, 52, 4)
            if c_prog2.button("Genera Prognosi"): 
                append_note(f"\n\nPrognosi Funzionale: In base alla valutazione clinica, stimiamo un percorso di circa {settimane} settimane per il raggiungimento degli obiettivi.")

            note_preventivo = st.text_area("Dettagli del Percorso:", key="prev_note", height=150)
            
            righe = []; tot = 0
            if servizi_scelti:
                st.divider()
                
                # Header colonne (MODIFICATO PER PREZZO)
                h1, h2, h3, h4, h5 = st.columns([2.5, 0.7, 0.7, 1.1, 1])
                h1.caption("Trattamento")
                h2.caption("Prezzo")
                h3.caption("Qta")
                h4.caption("Sconto")
                h5.caption("Totale")

                for s in servizi_scelti:
                    c1, c2, c3, c4, c5 = st.columns([2.5, 0.7, 0.7, 1.1, 1])
                    
                    # Nome Trattamento
                    with c1: st.write(f"**{s}**")
                    
                    # Prezzo Unitario (NUOVO)
                    unit_price = listino_dict[s]
                    with c2: st.write(f"{unit_price:.2f} €")
                    
                    # Quantità
                    if f"qty_{s}" not in st.session_state: st.session_state[f"qty_{s}"] = 1
                    qty = c3.number_input(f"Qta {s}", 1, 50, key=f"qty_{s}", label_visibility="collapsed")
                    
                    # Sconto (Nuova funzionalità €/%)
                    with c4:
                        cd_val, cd_type = st.columns([2, 1])
                        if f"d_val_{s}" not in st.session_state: st.session_state[f"d_val_{s}"] = 0.0
                        if f"d_type_{s}" not in st.session_state: st.session_state[f"d_type_{s}"] = "%"
                        
                        d_val = cd_val.number_input(f"V_{s}", 0.0, 1000.0, step=5.0, key=f"d_val_{s}", label_visibility="collapsed")
                        d_type = cd_type.selectbox(f"T_{s}", ["%", "€"], key=f"d_type_{s}", label_visibility="collapsed")
                    
                    # Calcolo Prezzo
                    base_price = unit_price * qty
                    
                    if d_type == "%":
                        discount_amount = base_price * (d_val / 100)
                        desc_sconto = f"{int(d_val)}%"
                    else: # Euro
                        discount_amount = d_val
                        desc_sconto = f"{d_val}€"
                    
                    final_price = max(0.0, base_price - discount_amount)
                    tot += final_price
                    
                    # Display Totale Riga
                    with c5: st.write(f"**{final_price:.2f} €**")
                    
                    # Aggiunta alla lista per salvataggio/PDF
                    nome_display = s
                    if d_val > 0:
                        nome_display = f"{s} (Sc. -{desc_sconto})"
                    
                    righe.append({"nome": nome_display, "qty": qty, "tot": round(final_price, 2)})
                
                st.divider()
                c_tot, c_btn = st.columns([2, 1])
                c_tot.markdown(f"### TOTALE: {tot:.2f} €")
                
                with c_btn:
                    if st.button("💾 Salva Preventivo", type="primary", use_container_width=True):
                        if paziente_scelto != "Seleziona...":
                            dett = " | ".join([f"{r['nome']} x{r['qty']} ({r['tot']}€)" for r in righe])
                            save_preventivo_temp(paziente_scelto, dett, tot, note_preventivo)
                            st.success("Salvato!")
                        else: st.error("Seleziona un paziente.")
                    
                    if st.button("🖨️ Anteprima Stampa", use_container_width=True):
                        st.session_state.show_html = True

            if st.session_state.get('show_html'):
                html = generate_html_preventivo(paziente_scelto, date.today().strftime("%d/%m/%Y"), note_preventivo, righe, tot, LOGO_B64)
                components.html(html, height=800, scrolling=True)
                if st.button("Chiudi Anteprima"):
                    st.session_state.show_html = False
                    st.rerun()

    with tab2:
        st.subheader("Archivio"); df_prev = get_data("Preventivi_Salvati")
        if not df_prev.empty:
            for i, r in df_prev.iterrows():
                try:
                    date_display = pd.to_datetime(r['Data_Creazione']).strftime('%d/%m/%Y')
                except:
                    date_display = str(r['Data_Creazione'])

                with st.expander(f"{r['Paziente']} - {r['Totale']}€ ({date_display})"):
                    st.write(r['Dettagli'])
                    if r.get('Note'):
                        st.caption(f"Note: {r['Note']}")
                    
                    c_print, c_del = st.columns([1, 5])
                    
                    with c_print:
                        if st.button("🖨️ Stampa", key=f"print_{r['id']}"):
                            righe_reconstructed = []
                            dettagli_raw = r.get('Dettagli', '')
                            if dettagli_raw:
                                items = dettagli_raw.split(" | ")
                                for item in items:
                                    try:
                                        temp, price_part = item.rsplit(' (', 1)
                                        price_str = price_part.replace('€)', '')
                                        name_str, qty_str = temp.rsplit(' x', 1)
                                        righe_reconstructed.append({
                                            'nome': name_str,
                                            'qty': qty_str,
                                            'tot': price_str
                                        })
                                    except:
                                        righe_reconstructed.append({'nome': item, 'qty': '-', 'tot': '-'})
                            
                            html_archive = generate_html_preventivo(
                                r['Paziente'],
                                date_display,
                                r.get('Note', ''),
                                righe_reconstructed,
                                r['Totale'],
                                LOGO_B64
                            )
                            components.html(html_archive, height=800, scrolling=True)

                    with c_del:
                        if st.button("🗑️ Elimina", key=f"del_{r['id']}"): 
                            delete_generic("Preventivi_Salvati", r['id'])
                            st.rerun()

# =========================================================
# SEZIONE NUOVA: CONSEGNE (AGGIORNATA CON SEGRETERIA)
# =========================================================
elif menu == "📨 Consegne":
    st.title("📨 Consegne Pazienti")
    df_cons = get_data("Consegne")
    df_paz = get_data("Pazienti")
    nomi_paz = ["-- Seleziona --"] + sorted([f"{r['Cognome']} {r['Nome']}" for i, r in df_paz.iterrows()]) if not df_paz.empty else []
    
    with st.expander("➕ Nuova Consegna", expanded=True):
        with st.form("new_cons"):
            c1, c2 = st.columns(2)
            paz = c1.selectbox("Paziente", nomi_paz)
            # AGGIUNTA "Segreteria" QUI SOTTO
            area = c2.selectbox("Area Competenza", ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"])
            ind = st.text_input("Cosa consegnare? (es. Referto, Scheda Esercizi)")
            scad = st.date_input("Entro quando?", date.today() + timedelta(days=3))
            if st.form_submit_button("Salva Promemoria"):
                if paz != "-- Seleziona --" and ind:
                    save_consegna(paz, area, ind, scad); st.success("Salvato!"); st.rerun()
                else: st.error("Compila i campi.")

    st.write("")
    
    # AGGIUNTA "Segreteria" NELLE TABS E NEL MAPPING
    tabs = st.tabs(["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"])
    mapping = ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"]
    
    if not df_cons.empty:
        # --- FIX PER EVITARE KEYERROR SE MANCANO COLONNE ---
        if 'Area' not in df_cons.columns: df_cons['Area'] = "Altro"
        if 'Data_Scadenza' not in df_cons.columns: df_cons['Data_Scadenza'] = None
        if 'Completato' not in df_cons.columns: df_cons['Completato'] = False
        
        # Conversione sicura della data
        df_cons['Data_Scadenza'] = pd.to_datetime(df_cons['Data_Scadenza'], errors='coerce').dt.date
        
        for i, tab_name in enumerate(mapping):
            with tabs[i]:
                # Filtra per l'area specifica della tab corrente
                items = df_cons[ (df_cons['Area'] == tab_name) & (df_cons['Completato'] != True) ]
                
                if items.empty: 
                    st.info(f"Nessuna consegna in attesa per {tab_name}.")
                else:
                    for _, row in items.iterrows():
                        # Calcolo giorni mancanti o ritardo
                        if row['Data_Scadenza']:
                            delta = (row['Data_Scadenza'] - date.today()).days
                            status_text = f"Scade tra {delta} gg" if delta >= 0 else f"SCADUTO da {abs(delta)} gg"
                            color = "border-green" if delta > 3 else "border-yellow" if delta >= 0 else "border-red"
                            date_display = row['Data_Scadenza'].strftime('%d/%m')
                        else:
                            status_text = "Data non definita"
                            color = "border-gray"
                            date_display = "N.D."
                        
                        # Layout riga
                        c_chk, c_info, c_date = st.columns([1, 6, 2])
                        with c_chk:
                            if st.button("✅", key=f"ok_{row['id']}"):
                                update_generic("Consegne", row['id'], {"Completato": True})
                                st.rerun()
                        with c_info:
                            st.markdown(f"""<div class="alert-row-name {color}"><b>{row.get('Paziente', 'Sconosciuto')}</b>: {row.get('Indicazione', '')}</div>""", unsafe_allow_html=True)
                        with c_date:
                            st.caption(f"{date_display}\n({status_text})")

# =========================================================
# SEZIONE 4: MAGAZZINO (MODIFICATA CON + E -)
# =========================================================
elif menu == "📦 Magazzino":
    st.title("Magazzino & Materiali")
    STANZE = ["Segreteria", "Mano", "Stanze", "Medicinali", "Pulizie"]
    col_add, col_view = st.columns([1, 2])
    
    with col_add:
        with st.container(border=True):
            st.subheader("Nuovo Articolo")
            with st.form("add_inv"):
                new_mat = st.text_input("Nome Materiale")
                new_area = st.selectbox("Area/Stanza", STANZE)
                c_q1, c_q2, c_q3 = st.columns(3)
                qty_now = c_q1.number_input("Q.tà Attuale", 0, 1000, 1)
                qty_target = c_q2.number_input("Obiettivo", 1, 1000, 5)
                qty_min = c_q3.number_input("Soglia Minima", 0, 100, 2)
                if st.form_submit_button("Aggiungi", use_container_width=True, type="primary"):
                    if new_mat:
                        save_materiale_avanzato(new_mat, new_area, qty_now, qty_target, qty_min)
                        st.success("Aggiunto!"); st.rerun()

    with col_view:
        df_inv = get_data("Inventario")
        if not df_inv.empty:
            if 'Quantità' in df_inv.columns: df_inv = df_inv.rename(columns={'Quantità': 'Quantita'})
            for c in ['Quantita', 'Soglia_Minima', 'Materiali', 'Obiettivo']:
                if c not in df_inv.columns: df_inv[c] = 0
            df_inv['Quantita'] = df_inv['Quantita'].fillna(0).astype(int)
            
            tabs = st.tabs(STANZE)
            for i, stanza in enumerate(STANZE):
                with tabs[i]:
                    items = df_inv[df_inv['Area'] == stanza]
                    if items.empty: st.caption("Nessun articolo.")
                    else:
                        for _, row in items.iterrows():
                            is_low = row['Quantita'] <= row['Soglia_Minima']
                            with st.container(border=True):
                                st.markdown('<style>div[data-testid="stVerticalBlockBorderWrapper"] {padding: 8px 15px !important; margin-bottom: 5px !important;}</style>', unsafe_allow_html=True)
                                c_info, c_stat, c_act = st.columns([3, 2, 1], gap="small")
                                with c_info:
                                    mat_name = row.get('Materiali', 'Senza Nome')
                                    st.markdown(f"**{mat_name}**")
                                    if is_low: st.caption(":red[⚠️ BASSO]")
                                    else: st.caption(":green[OK]")
                                with c_stat:
                                    val = min(row['Quantita'] / max(row['Obiettivo'], 1), 1.0)
                                    st.progress(val)
                                    st.caption(f"**{row['Quantita']}** / {row['Obiettivo']}")
                                with c_act:
                                    st.write("") 
                                    # --- MODIFICA: DUE PULSANTI PER AUMENTO E DIMINUZIONE ---
                                    b_minus, b_plus = st.columns(2)
                                    
                                    with b_minus:
                                        if st.button("🔻", key=f"dec_{row['id']}", type="secondary", use_container_width=True):
                                            if row['Quantita'] > 0:
                                                new_qty = int(row['Quantita'] - 1)
                                                update_generic("Inventario", row['id'], {"Quantità": new_qty})
                                                st.rerun()
                                    with b_plus:
                                        # Il tasto ha la freccia verde grazie al CSS aggiunto sopra
                                        if st.button("🔺", key=f"inc_{row['id']}", type="secondary", use_container_width=True):
                                            new_qty = int(row['Quantita'] + 1)
                                            update_generic("Inventario", row['id'], {"Quantità": new_qty})
                                            st.rerun()
        else: st.info("Magazzino vuoto.")

# =========================================================
# SEZIONE 5: PRESTITI (NUOVA LOGICA MODERNA)
# =========================================================
elif menu == "🔄 Prestiti":
    st.title("Gestione Noleggi e Prestiti")
    
    # 1. INVENTARIO (Definizione Strumenti)
    # IMPORTANTE: Nomi univoci per evitare errori
    INVENTARIO = {
        "Strumenti Mano": [
            "Flex-Bar Gialla1 5L", "Flex-Bar Gialla2 5L", "Flex-Bar Verde1 10L", "Flex-Bar Verde2 10L",
            "Flex-Bar Rossa 10L", "Flex-Bar Blu 25L", "Molla Esercizi (A)", "Molla Esercizi (B)", 
            "Dinamometro", "Kit Riabilitazione Mano", "Tutore Polso A", "Tutore Polso B"
        ],
        "Elettrostimolatore": ["Compex Pro 1", "Compex Pro 2", "Compex Wireless", "Neurostimolatore TENS"],
        "Magnetoterapia": ["Mag 2000 (A)", "Mag 2000 (B)", "I-Tech Magneto", "Solenoidi Fascia"]
    }
    
    df_pres = get_data("Prestiti")
    df_paz = get_data("Pazienti")
    nomi_paz = ["-- Seleziona --"] + sorted([f"{r['Cognome']} {r['Nome']}" for i, r in df_paz.iterrows()]) if not df_paz.empty else []

    # --- FIX ANTI-CRASH: Assicuriamo che le colonne esistano ---
    if not df_pres.empty:
        if 'Restituito' not in df_pres.columns: df_pres['Restituito'] = False
        if 'Data_Scadenza' not in df_pres.columns: df_pres['Data_Scadenza'] = None
        if 'Oggetto' not in df_pres.columns: df_pres['Oggetto'] = "Strumento"
        if 'Paziente' not in df_pres.columns: df_pres['Paziente'] = "Sconosciuto"

    # KPI TOP
    tot_strumenti = sum(len(v) for v in INVENTARIO.values())
    in_prestito = 0
    in_ritardo = 0
    if not df_pres.empty:
        # Conta solo non restituiti
        in_prestito = len(df_pres[df_pres['Restituito'] != True])
        # Conta scaduti
        df_pres['Data_Scadenza'] = pd.to_datetime(df_pres['Data_Scadenza'], errors='coerce')
        in_ritardo = len(df_pres[(df_pres['Restituito'] != True) & (df_pres['Data_Scadenza'] < pd.Timestamp.now().normalize())])

    kp1, kp2, kp3 = st.columns(3)
    kp1.metric("📦 Totale Strumenti", tot_strumenti)
    kp2.metric("🔄 Attualmente Fuori", in_prestito)
    kp3.metric("⚠️ In Ritardo", in_ritardo, delta_color="inverse")
    st.divider()

    # --- AGGIUNTA OGGETTO NUOVO ---
    with st.expander("➕ Aggiungi Oggetto in Elenco", expanded=False):
        with st.form("add_new_obj_list"):
            new_obj_name = st.text_input("Nome Nuovo Oggetto")
            if st.form_submit_button("Salva in Elenco"):
                if new_obj_name:
                    # Lo salviamo in Inventario con Area='Extra' per ritrovarlo
                    save_materiale_avanzato(new_obj_name, "Extra", 1, 1, 0)
                    st.success(f"Oggetto '{new_obj_name}' aggiunto alla lista!")
                    time.sleep(1.0)
                    st.rerun()
                else:
                    st.warning("Scrivi il nome dell'oggetto.")

    tabs = st.tabs(["✋ Strumenti Mano", "⚡ Elettrostimolatore", "🧲 Magnetoterapia", "📦 Extra / Fuori Lista"])
    mappa_tabs = {0: "Strumenti Mano", 1: "Elettrostimolatore", 2: "Magnetoterapia"}
    
    # TAB STANDARD
    for i, tab_name in mappa_tabs.items():
        with tabs[i]:
            strumenti_categoria = INVENTARIO[tab_name]
            for strumento in strumenti_categoria:
                prestito_attivo = pd.DataFrame()
                if not df_pres.empty:
                    prestito_attivo = df_pres[ (df_pres['Oggetto'] == strumento) & (df_pres['Restituito'] != True) ]
                
                with st.container(border=True):
                    c_nome, c_stato = st.columns([1, 2])
                    with c_nome:
                        st.markdown(f"### {strumento}")
                        if prestito_attivo.empty: st.caption("🟢 DISPONIBILE")
                        else: st.caption("🔴 IN PRESTITO")

                    with c_stato:
                        if not prestito_attivo.empty:
                            record = prestito_attivo.iloc[0]
                            scadenza = pd.to_datetime(record['Data_Scadenza']).date() if pd.notnull(record['Data_Scadenza']) else date.today()
                            days_left = (scadenza - date.today()).days
                            bg_color = "rgba(229, 62, 62, 0.2)" if days_left < 0 else "rgba(46, 204, 113, 0.2)"
                            
                            st.markdown(f"""<div style="background-color: {bg_color}; padding: 10px; border-radius: 8px;"><strong>Paziente:</strong> {record.get('Paziente', 'Unknown')}<br><strong>Scadenza:</strong> {scadenza.strftime('%d/%m')} ({days_left} gg)</div>""", unsafe_allow_html=True)
                            
                            if st.button("🔄 Restituisci", key=f"ret_{strumento}", use_container_width=True):
                                with st.spinner("Restituzione in corso..."):
                                    for _, row_to_close in prestito_attivo.iterrows():
                                        update_generic("Prestiti", row_to_close['id'], {"Restituito": True})
                                    st.toast(f"{strumento} restituito!"); time.sleep(1); st.rerun()
                        else:
                            c_paz, c_dur, c_btn = st.columns([2, 1, 1])
                            with c_paz: paz_sel = st.selectbox("Paziente", nomi_paz, key=f"paz_{strumento}", label_visibility="collapsed")
                            with c_dur:
                                cols_d = st.columns(2)
                                num = cols_d[0].number_input("Qta", 1, 52, 1, key=f"n_{strumento}", label_visibility="collapsed")
                                unit = cols_d[1].selectbox("U", ["Sett", "Giorni"], key=f"u_{strumento}", label_visibility="collapsed")
                            with c_btn:
                                if st.button("➕ Presta", key=f"btn_{strumento}", type="primary", use_container_width=True):
                                    if paz_sel != "-- Seleziona --":
                                        delta = timedelta(weeks=num) if unit == "Sett" else timedelta(days=num)
                                        if save_prestito_new(paz_sel, strumento, tab_name, date.today(), date.today() + delta):
                                            st.toast("Prestito registrato!", icon="✅"); st.rerun()
                                    else: st.toast("Seleziona prima un paziente!", icon="⚠️")
    
    # TAB EXTRA (LOGICA DINAMICA)
    with tabs[3]:
        st.subheader("📦 Oggetti Extra")
        df_inv_extra = get_data("Inventario")
        extra_items = []
        if not df_inv_extra.empty:
             # Filtra quelli con Area = "Extra"
             extra_items = df_inv_extra[df_inv_extra['Area'] == "Extra"]['Materiali'].tolist()
        
        if not extra_items:
            st.info("Nessun oggetto extra in elenco. Aggiungine uno dal menu in alto.")
        else:
            for strumento in extra_items:
                prestito_attivo = pd.DataFrame()
                if not df_pres.empty:
                    prestito_attivo = df_pres[ (df_pres['Oggetto'] == strumento) & (df_pres['Restituito'] != True) ]
                
                with st.container(border=True):
                    c_nome, c_stato = st.columns([1, 2])
                    with c_nome:
                        st.markdown(f"### {strumento}")
                        if prestito_attivo.empty: st.caption("🟢 DISPONIBILE")
                        else: st.caption("🔴 IN PRESTITO")

                    with c_stato:
                        if not prestito_attivo.empty:
                            record = prestito_attivo.iloc[0]
                            scadenza = pd.to_datetime(record['Data_Scadenza']).date() if pd.notnull(record['Data_Scadenza']) else date.today()
                            days_left = (scadenza - date.today()).days
                            bg_color = "rgba(229, 62, 62, 0.2)" if days_left < 0 else "rgba(46, 204, 113, 0.2)"
                            
                            st.markdown(f"""
                            <div style="background-color: {bg_color}; padding: 10px; border-radius: 8px;">
                                <strong>Paziente:</strong> {record.get('Paziente', 'Unknown')}<br>
                                <strong>Scadenza:</strong> {scadenza.strftime('%d/%m')} ({days_left} gg)
                            </div>
                            """, unsafe_allow_html=True)
                            
                            if st.button("🔄 Restituisci", key=f"ret_{strumento}", use_container_width=True):
                                with st.spinner("Restituzione..."):
                                    for _, row_to_close in prestito_attivo.iterrows():
                                        update_generic("Prestiti", row_to_close['id'], {"Restituito": True})
                                    st.toast(f"{strumento} restituito!")
                                    time.sleep(1)
                                    st.rerun()
                        else:
                            c_paz, c_dur, c_btn = st.columns([2, 1, 1])
                            with c_paz:
                                paz_sel = st.selectbox("Paziente", nomi_paz, key=f"paz_{strumento}", label_visibility="collapsed")
                            with c_dur:
                                cols_d = st.columns(2)
                                num = cols_d[0].number_input("Qta", 1, 52, 1, key=f"n_{strumento}", label_visibility="collapsed")
                                unit = cols_d[1].selectbox("U", ["Sett", "Giorni"], key=f"u_{strumento}", label_visibility="collapsed")
                            with c_btn:
                                if st.button("➕ Presta", key=f"btn_{strumento}", type="primary", use_container_width=True):
                                    if paz_sel != "-- Seleziona --":
                                        delta = timedelta(weeks=num) if unit == "Sett" else timedelta(days=num)
                                        if save_prestito_new(paz_sel, strumento, "Extra", date.today(), date.today() + delta):
                                            st.toast("Prestito registrato!", icon="✅")
                                            st.rerun()
                                    else: st.toast("Seleziona paziente!", icon="⚠️")

# =========================================================
# SEZIONE 6: SCADENZE (PLANNING FINANZIARIO - VERSIONE PULSANTI & CARD)
# =========================================================
elif menu == "📅 Scadenze":
    st.title("🗓️ Scadenziario Pagamenti")
    
    # --- FORM DI INSERIMENTO ---
    with st.expander("➕ Aggiungi Nuova Scadenza / Spesa", expanded=False):
        with st.form("add_scadenza"):
            c1, c2, c3 = st.columns([2, 1, 1])
            desc = c1.text_input("Descrizione (es. Affitto, Enel, TARI)")
            imp = c2.number_input("Importo (€)", min_value=0.0, step=10.0)
            tipo = c3.selectbox("Frequenza", ["Singola", "Mensile (12 mesi)", "Annuale"])
            data_start = st.date_input("Data Scadenza", date.today())
            
            if st.form_submit_button("Salva Scadenza", type="primary"):
                if desc:
                    # Logica per creare le scadenze
                    if tipo == "Singola":
                        api.table(BASE_ID, "Scadenze").create({
                            "Descrizione": desc, "Importo": imp, 
                            "Data_Scadenza": str(data_start), "Pagato": False, "Ricorrenza": "Singola"
                        }, typecast=True)
                        st.success("Scadenza salvata!")
                    
                    elif tipo == "Mensile (12 mesi)":
                        # Crea 12 record, uno per ogni mese
                        with st.spinner("Creazione piano annuale in corso..."):
                            batch_data = []
                            curr_date = data_start
                            for _ in range(12):
                                batch_data.append({
                                    "Descrizione": desc, "Importo": imp,
                                    "Data_Scadenza": str(curr_date), "Pagato": False, "Ricorrenza": "Mensile"
                                })
                                # Calcolo prossimo mese
                                next_month = curr_date.month % 12 + 1
                                next_year = curr_date.year + (curr_date.month // 12)
                                curr_date = curr_date.replace(year=next_year, month=next_month)
                            
                            # Airtable accetta batch da 10, quindi facciamo un ciclo o chiamate singole
                            for item in batch_data:
                                api.table(BASE_ID, "Scadenze").create(item, typecast=True)
                        st.success("Piano mensile creato per 1 anno!")
                    
                    # ATTESA FONDAMENTALE per il ricaricamento
                    time.sleep(1.5)
                    get_data.clear()
                    st.rerun()
                else:
                    st.warning("Inserisci almeno la descrizione.")

    st.divider()

    # --- VISUALIZZAZIONE MENSILE (CARD) ---
    df_scad = get_data("Scadenze")
    
    if not df_scad.empty and 'Data_Scadenza' in df_scad.columns:
        # Prepara i dati
        df_scad['Data_Scadenza'] = pd.to_datetime(df_scad['Data_Scadenza'], errors='coerce')
        if 'Pagato' not in df_scad.columns: df_scad['Pagato'] = False
        
        # Filtra per Anno Corrente (o seleziona anno)
        anno_corrente = date.today().year
        mesi = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", 
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
        
        # Tabs per i mesi
        tabs_mesi = st.tabs(mesi)
        
        # Calcolo Totale Annuale
        tot_anno = df_scad[df_scad['Data_Scadenza'].dt.year == anno_corrente]['Importo'].sum()

        for i, mese_nome in enumerate(mesi):
            with tabs_mesi[i]:
                # Filtra scadenze di questo mese e anno
                mask_mese = (df_scad['Data_Scadenza'].dt.month == (i + 1)) & (df_scad['Data_Scadenza'].dt.year == anno_corrente)
                items_mese = df_scad[mask_mese].sort_values("Data_Scadenza")
                
                # --- KPI DEL MESE ---
                tot_mese = items_mese['Importo'].sum()
                pagato_mese = items_mese[items_mese['Pagato'] == True]['Importo'].sum()
                da_pagare_mese = tot_mese - pagato_mese
                
                col_kpi1, col_kpi2, col_kpi3 = st.columns(3)
                col_kpi1.metric("🔴 Da Pagare (Mese)", f"{da_pagare_mese:,.2f} €", delta_color="inverse")
                col_kpi2.metric("✅ Saldato (Mese)", f"{pagato_mese:,.2f} €")
                col_kpi3.metric("📅 Totale Anno", f"{tot_anno:,.2f} €", help="Totale spese previste nell'anno")
                
                st.divider()

                if items_mese.empty:
                    st.info(f"Nessuna scadenza a {mese_nome}.")
                else:
                    # Visualizzazione a CARD
                    for _, row in items_mese.iterrows():
                        is_paid = row.get('Pagato') is True
                        
                        # Definisci lo stile della Card
                        border_color = "rgba(46, 204, 113, 0.4)" if is_paid else "rgba(229, 62, 62, 0.4)" 
                        
                        with st.container(border=True):
                            c_info, c_action = st.columns([3, 1])
                            
                            with c_info:
                                data_fmt = row['Data_Scadenza'].strftime('%d')
                                
                                if is_paid:
                                    st.markdown(f"~~📅 {data_fmt} - {row['Descrizione']}~~")
                                    st.caption(f"✅ PAGATO - {row['Importo']} €")
                                else:
                                    st.markdown(f"📅 **{data_fmt}** - **{row['Descrizione']}**")
                                    st.markdown(f"💰 **{row['Importo']} €**")

                            with c_action:
                                if is_paid:
                                    if st.button("↩️ Annulla", key=f"undo_{row['id']}", use_container_width=True):
                                        with st.spinner("Annullamento..."):
                                            update_generic("Scadenze", row['id'], {"Pagato": False})
                                            time.sleep(1.0)
                                            st.rerun()
                                else:
                                    if st.button("✅ Paga", key=f"pay_{row['id']}", type="primary", use_container_width=True):
                                        with st.spinner("Salvataggio..."):
                                            update_generic("Scadenze", row['id'], {"Pagato": True})
                                            time.sleep(1.0)
                                            st.rerun()
                                
                                # Tasto Elimina piccolo sotto
                                if st.button("🗑️", key=f"del_{row['id']}", help="Elimina"):
                                    with st.spinner("Eliminazione..."):
                                        delete_generic("Scadenze", row['id'])
                                        time.sleep(1.0)
                                        st.rerun()
    else:
        st.info("Nessuna scadenza trovata nel database.")
