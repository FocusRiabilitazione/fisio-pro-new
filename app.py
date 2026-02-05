import streamlit as st
from pyairtable import Api
import time

st.set_page_config(page_title="Test Connessione", layout="centered")

st.title("🔌 Test Diagnostico Unico")
st.write("Questo test interroga Airtable UNA sola volta per verificare se il blocco 429 è passato.")

# 1. Recupero Credenziali
try:
    API_KEY = st.secrets["AIRTABLE_TOKEN"]
    BASE_ID = st.secrets["AIRTABLE_BASE_ID"]
    st.success("✅ Chiavi trovate nel sistema.")
except:
    st.warning("Chiavi non trovate nei secrets.")
    API_KEY = st.text_input("Token (pat...)", type="password")
    BASE_ID = st.text_input("Base ID (app...)")

# 2. Pulsante di Test Manuale
if st.button("LANCIA TEST CONNESSIONE (Clicca una volta sola)"):
    if not API_KEY or not BASE_ID:
        st.error("Mancano le chiavi.")
        st.stop()
    
    api = Api(API_KEY)
    
    try:
        with st.spinner("Contatto Airtable..."):
            # Proviamo a scaricare SOLO la tabella Pazienti, una sola volta
            table = api.table(BASE_ID, "Pazienti")
            records = table.all()
            
            st.balloons()
            st.success(f"✅ CONNESSIONE RIUSCITA! Scaricati {len(records)} pazienti.")
            st.write("Il sistema funziona. Il problema di prima era solo la velocità di richiesta.")
            
            # Mostra i primi 3 dati per conferma
            if records:
                st.write("Primi 3 dati trovati:", records[:3])
            
    except Exception as e:
        st.error("❌ ERRORE ANCORA PRESENTE")
        st.code(str(e))
        
        if "401" in str(e):
            st.error("Diagnosi: 401 = IL TOKEN È SBAGLIATO O SCADUTO. Devi rigenerarlo su Airtable.")
        elif "404" in str(e):
            st.error("Diagnosi: 404 = BASE ID SBAGLIATO oppure la tabella 'Pazienti' non esiste con questo nome esatto.")
        elif "429" in str(e):
            st.error("Diagnosi: 429 = SEI ANCORA IN PUNIZIONE. Aspetta altri 5 minuti senza toccare nulla.")
