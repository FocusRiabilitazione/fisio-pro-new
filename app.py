import streamlit as st
import streamlit.components.v1 as components
from pyairtable import Api
import pandas as pd
from datetime import date, datetime, timedelta
import base64
import time 

# =========================================================
# 0. CONFIGURAZIONE
# =========================================================
st.set_page_config(page_title="Gestionale Fisio Pro", page_icon="🏥", layout="wide")

# CSS ESSENZIALE
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    div[data-testid="stSidebar"] { background-color: #262730; }
    h1, h2, h3 { color: white !important; }
    .alert-box { padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid #444; }
    .success { background-color: rgba(46, 204, 113, 0.2); border-left: 5px solid #2ecc71; }
    .error { background-color: rgba(231, 76, 60, 0.2); border-left: 5px solid #e74c3c; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 1. GESTIONE CONNESSIONE (DEBUG)
# =========================================================
st.sidebar.title("🔧 Configurazione")

# Tenta di leggere dai secrets, altrimenti usa input manuale
try:
    API_KEY = st.secrets["AIRTABLE_TOKEN"]
    BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
    st.sidebar.success("✅ Chiavi trovate nei Secrets")
except:
    st.sidebar.warning("⚠️ Chiavi non trovate. Inseriscile manuale:")
    API_KEY = st.sidebar.text_input("Token (pat...)", type="password")
    BASE_ID = st.sidebar.text_input("Base ID (app...)")

if not API_KEY or not BASE_ID:
    st.error("⛔ MANCANO LE CHIAVI DI ACCESSO. Inseriscile nella barra laterale.")
    st.stop()

api = Api(API_KEY)

# =========================================================
# 2. FUNZIONI (SENZA CACHE PER EVITARE ERRORI)
# =========================================================

def get_data_safe(table_name):
    """Scarica i dati con un forte ritardo per evitare errore 429"""
    try:
        # RITARDO DI 1 SECONDO (Molto conservativo ma sicuro)
        time.sleep(1.0) 
        table = api.table(BASE_ID, table_name)
        records = table.all()
        if not records: return pd.DataFrame()
        return pd.DataFrame([{'id': r['id'], **r['fields']} for r in records])
    except Exception as e:
        st.error(f"❌ Errore caricamento '{table_name}': {str(e)}")
        return pd.DataFrame()

def safe_update(table, record_id, fields):
    try:
        api.table(BASE_ID, table).update(record_id, fields, typecast=True)
        time.sleep(1) # Pausa dopo aggiornamento
        return True
    except Exception as e:
        st.error(f"Errore aggiornamento: {e}")
        return False

def safe_create(table, fields):
    try:
        api.table(BASE_ID, table).create(fields, typecast=True)
        time.sleep(1)
        return True
    except Exception as e:
        st.error(f"Errore creazione: {e}")
        return False

def safe_delete(table, record_id):
    try:
        api.table(BASE_ID, table).delete(record_id)
        time.sleep(1)
        return True
    except: return False

def get_logo():
    try:
        with open("logo.png", "rb") as f:
            return base64.b64encode(f.read()).decode()
    except: return ""

LOGO_B64 = get_logo()

# =========================================================
# 3. CARICAMENTO DATI (CON BARRA PROGRESSO)
# =========================================================
# Carichiamo i dati all'inizio per vedere se si blocca
with st.sidebar:
    st.write("---")
    st.write("📡 Stato Connessione:")
    status_text = st.empty()

# Caricamento sequenziale protetto
status_text.text("⏳ Caricamento Pazienti...")
df_paz = get_data_safe("Pazienti")

status_text.text("⏳ Caricamento Inventario...")
df_inv = get_data_safe("Inventario")

status_text.text("⏳ Caricamento Consegne...")
df_cons = get_data_safe("Consegne")

status_text.text("⏳ Caricamento Prestiti...")
df_pres = get_data_safe("Prestiti")

status_text.text("⏳ Caricamento Scadenze...")
df_scad = get_data_safe("Scadenze")

status_text.text("✅ Dati Aggiornati")

# =========================================================
# 4. INTERFACCIA PRINCIPALE
# =========================================================

menu = st.sidebar.radio("Navigazione", 
    ["Dashboard", "Pazienti", "Preventivi", "Consegne", "Magazzino", "Prestiti", "Scadenze"])

# --- DASHBOARD ---
if menu == "Dashboard":
    st.title("⚡ Dashboard")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Pazienti Totali", len(df_paz) if not df_paz.empty else 0)
    
    scaduti = 0
    if not df_pres.empty:
        df_pres['Data_Scadenza'] = pd.to_datetime(df_pres['Data_Scadenza'], errors='coerce')
        # Filtra non restituiti e scaduti
        mask = (df_pres.get('Restituito') != True) & (df_pres['Data_Scadenza'] < pd.Timestamp.now().normalize())
        scaduti = len(df_pres[mask])
    
    col2.metric("Prestiti Scaduti", scaduti, delta_color="inverse")
    
    pendenti = len(df_cons[df_cons.get('Completato') != True]) if not df_cons.empty else 0
    col3.metric("Consegne Pendenti", pendenti)

    st.divider()
    
    # AVVISI
    st.subheader("⚠️ Avvisi Importanti")
    
    # 1. Prestiti Scaduti
    if not df_pres.empty and scaduti > 0:
        st.error(f"Ci sono {scaduti} strumenti non restituiti in tempo!")
        bad_pres = df_pres[(df_pres.get('Restituito') != True) & (df_pres['Data_Scadenza'] < pd.Timestamp.now().normalize())]
        for _, r in bad_pres.iterrows():
            st.write(f"🔴 **{r.get('Paziente')}**: {r.get('Oggetto')} (Scaduto il {r['Data_Scadenza'].date()})")

    # 2. Consegne
    if not df_cons.empty and pendenti > 0:
        st.info(f"Ci sono {pendenti} consegne da effettuare.")
        for _, r in df_cons[df_cons.get('Completato')!=True].iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"📨 **{r.get('Paziente')}**: {r.get('Indicazione')}")
            if c2.button("Fatto", key=f"ok_dash_{r['id']}"):
                safe_update("Consegne", r['id'], {"Completato": True})
                st.rerun()

# --- PAZIENTI ---
elif menu == "Pazienti":
    st.title("👥 Pazienti")
    
    with st.expander("➕ Nuovo Paziente"):
        with st.form("add_paz"):
            n = st.text_input("Nome")
            c = st.text_input("Cognome")
            area = st.multiselect("Area", ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Ortopedico"])
            if st.form_submit_button("Salva"):
                if n and c:
                    safe_create("Pazienti", {"Nome": n, "Cognome": c, "Area": area, "Disdetto": False})
                    st.success("Salvato!")
                    time.sleep(1)
                    st.rerun()
                else: st.warning("Inserisci nome e cognome")

    if not df_paz.empty:
        search = st.text_input("🔍 Cerca Paziente")
        df_view = df_paz
        if search:
            df_view = df_paz[df_paz['Cognome'].astype(str).str.contains(search, case=False, na=False)]
        
        # Editor semplice
        edited = st.data_editor(
            df_view[['Nome', 'Cognome', 'Area', 'Disdetto', 'Data_Disdetta', 'id']], 
            key="editor_paz", 
            hide_index=True,
            column_config={
                "Disdetto": st.column_config.CheckboxColumn("Disdetto?", default=False),
                "id": None
            }
        )
        
        if st.button("💾 Salva Modifiche Tabella"):
            for i, row in edited.iterrows():
                # Controllo se è cambiato qualcosa (semplificato)
                original = df_paz[df_paz['id'] == row['id']].iloc[0]
                if row['Disdetto'] != original['Disdetto']:
                    safe_update("Pazienti", row['id'], {"Disdetto": row['Disdetto']})
            st.success("Aggiornato!")
            time.sleep(1)
            st.rerun()

# --- PREVENTIVI ---
elif menu == "Preventivi":
    st.title("💳 Preventivi")
    
    # Caricamento servizi solo quando serve
    df_serv = get_data_safe("Servizi")
    
    c1, c2 = st.columns(2)
    paz_list = []
    if not df_paz.empty:
        paz_list = sorted((df_paz['Cognome'] + " " + df_paz['Nome']).tolist())
    
    paziente = c1.selectbox("Paziente", [""] + paz_list)
    
    servizi_list = []
    prezzi = {}
    if not df_serv.empty:
        for _, r in df_serv.iterrows():
            nome = str(r.get('Servizio', ''))
            prz = float(r.get('Prezzo', 0))
            if nome:
                servizi_list.append(nome)
                prezzi[nome] = prz
    
    scelti = c2.multiselect("Trattamenti", sorted(servizi_list))
    note = st.text_area("Note Cliniche")
    
    righe = []
    totale = 0
    
    if scelti:
        st.write("---")
        st.write("### Dettaglio Costi")
        
        for s in scelti:
            cc1, cc2, cc3 = st.columns([3, 1, 1])
            cc1.write(f"**{s}**")
            p_unit = prezzi.get(s, 0)
            
            qty = cc2.number_input(f"Qta {s}", 1, 50, 1)
            costo = p_unit * qty
            totale += costo
            cc3.write(f"{costo:.2f} €")
            
            righe.append(f"{s} x{qty} ({costo}€)")
            
        st.markdown(f"### TOTALE: {totale:.2f} €")
        
        if st.button("💾 Salva Preventivo"):
            if paziente:
                dettagli_str = " | ".join(righe)
                safe_create("Preventivi_Salvati", {
                    "Paziente": paziente,
                    "Dettagli": dettagli_str,
                    "Totale": totale,
                    "Note": note,
                    "Data_Creazione": str(date.today())
                })
                st.success("Salvato!")
            else:
                st.error("Seleziona un paziente")

    # Archivio
    st.divider()
    st.subheader("Archivio")
    df_prev = get_data_safe("Preventivi_Salvati")
    if not df_prev.empty:
        for _, r in df_prev.iterrows():
            with st.expander(f"{r.get('Paziente')} - {r.get('Totale')}€"):
                st.write(r.get('Dettagli'))
                st.caption(r.get('Note'))
                if st.button("🗑️ Elimina", key=f"del_prev_{r['id']}"):
                    safe_delete("Preventivi_Salvati", r['id'])
                    st.rerun()

# --- CONSEGNE ---
elif menu == "Consegne":
    st.title("📨 Consegne")
    
    with st.form("add_cons"):
        c1, c2 = st.columns(2)
        paz = c1.selectbox("Paziente", sorted(df_paz['Cognome'] + " " + df_paz['Nome']) if not df_paz.empty else [])
        area = c2.selectbox("Area", ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"])
        obj = st.text_input("Oggetto da consegnare")
        dt = st.date_input("Entro il", date.today() + timedelta(days=3))
        
        if st.form_submit_button("Aggiungi Consegna"):
            safe_create("Consegne", {
                "Paziente": paz, "Area": area, 
                "Indicazione": obj, "Data_Scadenza": str(dt), 
                "Completato": False
            })
            st.rerun()
            
    if not df_cons.empty:
        st.write("---")
        tabs = st.tabs(["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"])
        areas = ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Segreteria"]
        
        # Pulizia dati per evitare errori
        if 'Area' not in df_cons.columns: df_cons['Area'] = "Altro"
        if 'Completato' not in df_cons.columns: df_cons['Completato'] = False
        
        for i, a in enumerate(areas):
            with tabs[i]:
                items = df_cons[(df_cons['Area'] == a) & (df_cons['Completato'] != True)]
                if items.empty:
                    st.info("Nessuna consegna.")
                else:
                    for _, r in items.iterrows():
                        c1, c2 = st.columns([4, 1])
                        c1.markdown(f"**{r.get('Paziente')}**: {r.get('Indicazione')} (Entro: {r.get('Data_Scadenza')})")
                        if c2.button("✅", key=f"ok_{r['id']}"):
                            safe_update("Consegne", r['id'], {"Completato": True})
                            st.rerun()

# --- MAGAZZINO ---
elif menu == "Magazzino":
    st.title("📦 Magazzino")
    
    with st.expander("Nuovo Prodotto"):
        n_mat = st.text_input("Nome Materiale")
        n_area = st.selectbox("Area", ["Mano", "Stanze", "Segreteria", "Pulizie"])
        n_qty = st.number_input("Quantità", 1)
        if st.button("Crea"):
            safe_create("Inventario", {"Materiali": n_mat, "Area": n_area, "Quantità": n_qty, "Obiettivo": 5, "Soglia_Minima": 2})
            st.rerun()
            
    if not df_inv.empty:
        # Pulisci nomi colonne se necessario
        if 'Quantità' in df_inv.columns: df_inv = df_inv.rename(columns={'Quantità': 'Quantita'})
        
        for _, r in df_inv.iterrows():
            with st.container():
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{r.get('Materiali')}**")
                
                qty = int(r.get('Quantita', 0) or 0)
                c2.write(f"Qta: {qty}")
                
                with c3:
                    sc1, sc2 = st.columns(2)
                    if sc1.button("➖", key=f"sub_{r['id']}"):
                        safe_update("Inventario", r['id'], {"Quantità": max(0, qty - 1)})
                        st.rerun()
                    if sc2.button("➕", key=f"add_{r['id']}"):
                        safe_update("Inventario", r['id'], {"Quantità": qty + 1})
                        st.rerun()
                st.divider()

# --- PRESTITI ---
elif menu == "Prestiti":
    st.title("🔄 Prestiti")
    
    # 1. Aggiunta Rapida Oggetto Extra
    with st.expander("➕ Aggiungi Oggetto 'Extra'"):
        new_extra = st.text_input("Nome Oggetto")
        if st.button("Aggiungi alla lista"):
            safe_create("Inventario", {"Materiali": new_extra, "Area": "Extra", "Quantità": 1, "Obiettivo": 1, "Soglia_Minima": 0})
            st.success("Aggiunto!")
            time.sleep(1)
            st.rerun()

    # 2. Tabs Categorie
    tabs = st.tabs(["Mano", "Elettro", "Magneto", "Extra"])
    
    # Liste manuali per sicurezza
    CATS = {
        0: ["Flex-Bar Gialla", "Flex-Bar Verde", "Flex-Bar Rossa", "Flex-Bar Blu", "Dinamometro"],
        1: ["Compex 1", "Compex 2", "Tens"],
        2: ["Magneto A", "Magneto B"],
        3: [] # Extra da DB
    }
    
    # Popola extra
    if not df_inv.empty:
        extras = df_inv[df_inv['Area'] == "Extra"]['Materiali'].tolist()
        CATS[3] = extras
        
    paz_nomi = sorted(df_paz['Cognome'] + " " + df_paz['Nome']) if not df_paz.empty else []
    
    # Gestione anti-crash per colonne mancanti
    if not df_pres.empty:
        if 'Restituito' not in df_pres.columns: df_pres['Restituito'] = False
    
    for i, tab in enumerate(tabs):
        with tab:
            for item in CATS[i]:
                # Cerca se prestato
                attivo = pd.DataFrame()
                if not df_pres.empty:
                    attivo = df_pres[(df_pres['Oggetto'] == item) & (df_pres['Restituito'] != True)]
                
                with st.container():
                    st.markdown(f"#### {item}")
                    
                    if not attivo.empty:
                        r = attivo.iloc[0]
                        st.error(f"🔴 Prestato a: **{r.get('Paziente')}** (Scad: {r.get('Data_Scadenza')})")
                        if st.button("Restituisci", key=f"ret_{item}"):
                            safe_update("Prestiti", r['id'], {"Restituito": True})
                            st.rerun()
                    else:
                        st.success("🟢 Disponibile")
                        c1, c2, c3 = st.columns([2, 1, 1])
                        p = c1.selectbox("Chi?", paz_nomi, key=f"p_{item}")
                        d = c2.number_input("Giorni", 7, 60, 30, key=f"d_{item}")
                        if c3.button("Presta", key=f"btn_{item}"):
                            safe_create("Prestiti", {
                                "Paziente": p, "Oggetto": item, 
                                "Data_Prestito": str(date.today()),
                                "Data_Scadenza": str(date.today() + timedelta(days=d)),
                                "Restituito": False,
                                "Categoria": "Generico"
                            })
                            st.rerun()
                    st.divider()

# --- SCADENZE ---
elif menu == "Scadenze":
    st.title("🗓️ Scadenze")
    
    with st.expander("Nuova Spesa"):
        d = st.text_input("Descrizione")
        imp = st.number_input("Importo", 0.0)
        dt = st.date_input("Data Scadenza")
        if st.button("Salva Spesa"):
            safe_create("Scadenze", {"Descrizione": d, "Importo": imp, "Data_Scadenza": str(dt), "Pagato": False})
            st.rerun()
            
    if not df_scad.empty:
        df_scad['Data_Scadenza'] = pd.to_datetime(df_scad['Data_Scadenza'], errors='coerce')
        df_scad = df_scad.sort_values('Data_Scadenza')
        
        for _, r in df_scad.iterrows():
            pagato = r.get('Pagato') is True
            color = "green" if pagato else "red"
            
            with st.container():
                c1, c2 = st.columns([4, 1])
                c1.markdown(f":{color}[**{r.get('Descrizione')}**] - {r.get('Importo')}€ (Scad: {r['Data_Scadenza'].date()})")
                
                if not pagato:
                    if c2.button("Paga", key=f"pay_{r['id']}"):
                        safe_update("Scadenze", r['id'], {"Pagato": True})
                        st.rerun()
                else:
                    if c2.button("Annulla", key=f"undo_{r['id']}"):
                        safe_update("Scadenze", r['id'], {"Pagato": False})
                        st.rerun()
                st.divider()
