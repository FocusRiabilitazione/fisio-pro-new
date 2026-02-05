import streamlit as st
from pyairtable import Api
import pandas as pd
from datetime import date, datetime, timedelta
import time
import base64

# =========================================================
# CONFIGURAZIONE PAGINA
# =========================================================
st.set_page_config(page_title="Gestionale Fisio Pro", page_icon="🏥", layout="wide")

# =========================================================
# GESTIONE CONNESSIONE E ERRORI (Retry Logic)
# =========================================================
try:
    API_KEY = st.secrets["AIRTABLE_TOKEN"]
    BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
except:
    # Se non ci sono i secrets, usa i placeholder (non blocca l'app all'avvio)
    API_KEY = ""
    BASE_ID = ""

# Se l'utente vuole forzare le chiavi manuali dalla sidebar
with st.sidebar:
    st.title("🏥 Focus Rehab")
    
    # Se le chiavi non sono nei secrets, mostriamo i campi
    if not API_KEY or not BASE_ID:
        st.warning("⚠️ Configurazione Mancante")
        API_KEY = st.text_input("Token (pat...)", type="password")
        BASE_ID = st.text_input("Base ID (app...)")
    
    menu = st.radio("Menu", ["🏠 Home", "👥 Pazienti", "💳 Preventivi", "📨 Consegne", "📦 Magazzino", "🔄 Prestiti", "📅 Scadenze"])
    st.divider()
    st.caption("Mode: Lazy Loading (Anti-429)")

# Se mancano ancora le chiavi, ferma tutto qui
if not API_KEY or not BASE_ID:
    st.info("👈 Inserisci le chiavi API nella barra laterale per iniziare.")
    st.stop()

api = Api(API_KEY)

# =========================================================
# FUNZIONI DI CARICAMENTO (Una alla volta)
# =========================================================

def get_data_one_table(table_name):
    """Scarica UNA sola tabella con gestione errori avanzata"""
    try:
        table = api.table(BASE_ID, table_name)
        # Nessun time.sleep qui, perché carichiamo una tabella alla volta solo quando serve
        records = table.all()
        if not records: return pd.DataFrame()
        return pd.DataFrame([{'id': r['id'], **r['fields']} for r in records])
    except Exception as e:
        if "429" in str(e):
            st.error(f"🚦 Traffico intenso su Airtable. Riprova tra 30 secondi. (Errore sulla tabella: {table_name})")
        elif "404" in str(e):
            st.error(f"❌ Tabella '{table_name}' non trovata. Controlla il nome su Airtable.")
        elif "401" in str(e):
            st.error("🔒 Token non autorizzato. Controlla le chiavi.")
        else:
            st.error(f"Errore generico {table_name}: {e}")
        return pd.DataFrame() # Ritorna vuoto per non crashare

def safe_create(table, fields):
    try:
        api.table(BASE_ID, table).create(fields, typecast=True)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False

def safe_update(table, rid, fields):
    try:
        api.table(BASE_ID, table).update(rid, fields, typecast=True)
        return True
    except Exception as e:
        st.error(f"Errore aggiornamento: {e}")
        return False

def safe_delete(table, rid):
    try:
        api.table(BASE_ID, table).delete(rid)
        return True
    except: return False

# =========================================================
# LOGICA DELLE PAGINE (Carica SOLO ciò che serve)
# =========================================================

# --- HOME / DASHBOARD ---
if menu == "🏠 Home":
    st.header("🏠 Dashboard Studio")
    st.info("ℹ️ I dati vengono caricati solo quando apri le sezioni specifiche per evitare blocchi.")
    
    # Carichiamo solo i dati essenziali per la dashboard se l'utente vuole
    if st.button("🔄 Aggiorna Statistiche Dashboard"):
        with st.spinner("Analisi dati in corso..."):
            df_paz = get_data_one_table("Pazienti")
            df_pres = get_data_one_table("Prestiti")
            
            c1, c2 = st.columns(2)
            c1.metric("Totale Pazienti", len(df_paz) if not df_paz.empty else 0)
            
            scaduti = 0
            if not df_pres.empty:
                df_pres['Data_Scadenza'] = pd.to_datetime(df_pres['Data_Scadenza'], errors='coerce')
                mask = (df_pres.get('Restituito') != True) & (df_pres['Data_Scadenza'] < pd.Timestamp.now().normalize())
                scaduti = len(df_pres[mask])
            c2.metric("Prestiti Scaduti", scaduti, delta_color="inverse")

# --- PAZIENTI ---
elif menu == "👥 Pazienti":
    st.header("Gestione Pazienti")
    
    # 1. Carico Dati
    df_paz = get_data_one_table("Pazienti")
    
    # 2. Form Nuovo
    with st.expander("➕ Nuovo Paziente"):
        c1, c2 = st.columns(2)
        n = c1.text_input("Nome"); c = c2.text_input("Cognome")
        a = st.multiselect("Area", ["Mano-Polso", "Colonna", "ATM", "Muscolo-Scheletrico", "Ortopedico"])
        if st.button("Salva Paziente"):
            if safe_create("Pazienti", {"Nome": n, "Cognome": c, "Area": a, "Disdetto": False}):
                st.success("Salvato! Ricarica la pagina."); time.sleep(1); st.rerun()

    # 3. Tabella
    if not df_paz.empty:
        search = st.text_input("Cerca paziente...")
        if search: df_paz = df_paz[df_paz['Cognome'].astype(str).str.contains(search, case=False, na=False)]
        
        st.dataframe(df_paz[['Nome', 'Cognome', 'Area', 'Disdetto']], use_container_width=True)

# --- MAGAZZINO ---
elif menu == "📦 Magazzino":
    st.header("Magazzino")
    
    df_inv = get_data_one_table("Inventario")
    
    with st.expander("➕ Nuovo Articolo"):
        n_mat = st.text_input("Nome Materiale")
        n_area = st.selectbox("Stanza", ["Mano", "Stanze", "Segreteria", "Pulizie"])
        n_qty = st.number_input("Qta Iniziale", 1)
        if st.button("Crea Articolo"):
            safe_create("Inventario", {"Materiali": n_mat, "Area": n_area, "Quantità": n_qty, "Obiettivo": 5, "Soglia_Minima": 2})
            st.rerun()

    if not df_inv.empty:
        # Normalizza colonna
        if 'Quantità' in df_inv.columns: df_inv = df_inv.rename(columns={'Quantità': 'Quantita'})
        if 'Quantita' not in df_inv.columns: df_inv['Quantita'] = 0
        
        for i, row in df_inv.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"**{row.get('Materiali')}**")
                
                qty = int(row.get('Quantita') or 0)
                c2.write(f"Scorta: **{qty}**")
                
                with c3:
                    sc1, sc2 = st.columns(2)
                    if sc1.button("➖", key=f"dec_{row['id']}"):
                        safe_update("Inventario", row['id'], {"Quantità": max(0, qty - 1)})
                        st.rerun()
                    if sc2.button("➕", key=f"inc_{row['id']}"):
                        safe_update("Inventario", row['id'], {"Quantità": qty + 1})
                        st.rerun()

# --- PRESTITI ---
elif menu == "🔄 Prestiti":
    st.header("Prestiti")
    
    # Carica solo il necessario
    df_pres = get_data_one_table("Prestiti")
    df_paz = get_data_one_table("Pazienti") # Serve per il menu a tendina
    
    paz_list = sorted(df_paz['Cognome'] + " " + df_paz['Nome']) if not df_paz.empty else []
    
    st.subheader("Nuovo Prestito")
    c1, c2, c3 = st.columns(3)
    p = c1.selectbox("Paziente", [""] + paz_list)
    obj = c2.text_input("Oggetto")
    days = c3.number_input("Durata (gg)", 30)
    
    if st.button("Registra Prestito"):
        if p and obj:
            safe_create("Prestiti", {
                "Paziente": p, 
                "Oggetto": obj, 
                "Data_Prestito": str(date.today()),
                "Data_Scadenza": str(date.today() + timedelta(days=days)),
                "Restituito": False
            })
            st.success("Registrato!"); st.rerun()
            
    st.divider()
    st.subheader("In Corso")
    if not df_pres.empty:
        # Filtra attivi
        active = df_pres[df_pres.get('Restituito') != True]
        for _, r in active.iterrows():
            col1, col2 = st.columns([4, 1])
            col1.warning(f"🔴 **{r.get('Paziente')}** ha: {r.get('Oggetto')} (Scad: {r.get('Data_Scadenza')})")
            if col2.button("Restituisci", key=f"ret_{r['id']}"):
                safe_update("Prestiti", r['id'], {"Restituito": True})
                st.rerun()

# --- PREVENTIVI ---
elif menu == "💳 Preventivi":
    st.header("Preventivi")
    # Carica solo servizi
    df_serv = get_data_one_table("Servizi")
    
    prezzi = {}
    if not df_serv.empty:
        for _, r in df_serv.iterrows():
            prezzi[str(r.get('Servizio'))] = float(r.get('Prezzo', 0))
            
    servizi = st.multiselect("Seleziona Servizi", sorted(prezzi.keys()))
    totale = 0
    if servizi:
        st.write("---")
        for s in servizi:
            c1, c2 = st.columns([3, 1])
            c1.write(s)
            c2.write(f"{prezzi[s]} €")
            totale += prezzi[s]
        st.subheader(f"Totale: {totale} €")

# --- CONSEGNE ---
elif menu == "📨 Consegne":
    st.header("Consegne")
    df_cons = get_data_one_table("Consegne")
    
    if not df_cons.empty:
        pend = df_cons[df_cons.get('Completato') != True]
        for _, r in pend.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.info(f"Consegnare a **{r.get('Paziente')}**: {r.get('Indicazione')}")
            if c2.button("Fatto", key=f"ok_cons_{r['id']}"):
                safe_update("Consegne", r['id'], {"Completato": True})
                st.rerun()

# --- SCADENZE ---
elif menu == "📅 Scadenze":
    st.header("Scadenze")
    df_scad = get_data_one_table("Scadenze")
    
    if not df_scad.empty:
        df_scad['Data_Scadenza'] = pd.to_datetime(df_scad['Data_Scadenza'], errors='coerce')
        df_scad = df_scad.sort_values('Data_Scadenza')
        
        for _, r in df_scad.iterrows():
            pagato = r.get('Pagato') is True
            color = ":green" if pagato else ":red"
            st.markdown(f"{color}[**{r.get('Descrizione')}**] - {r.get('Importo')}€ (Scad: {r['Data_Scadenza'].date()})")
