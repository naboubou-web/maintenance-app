import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURATION CLOUD ---
# Remplace par l'URL de ton Google Sheet que tu as copié à l'étape 1
URL_SHEET = "https://docs.google.com/spreadsheets/d/18kJOh6IknPJDF68snoiXVxe-aa923rQAQ1qDaeolXfM/edit?usp=sharing"

st.set_page_config(page_title="Maintenance Cloud", layout="wide")

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        return conn.read(spreadsheet=URL_SHEET, worksheet=sheet_name)
    except:
        return pd.DataFrame()

# --- INTERFACE ---
st.sidebar.title("⚙️ Maintenance Sync")
menu = st.sidebar.radio("Menu", ["Dashboard", "Saisie Conduite", "Saisie Corrective"])

# On charge les équipements depuis ton fichier Excel que tu as mis sur GitHub
@st.cache_data
def get_lists():
    df_h = pd.read_excel("Historique_Correctif.xlsx", header=2)
    equips = sorted(df_h['Equipement'].dropna().unique().tolist())
    techs = sorted(df_h['Technicien'].dropna().unique().tolist())
    return equips, techs

equips, techs = get_lists()

if menu == "Saisie Corrective":
    st.title("🛠️ Saisie Maintenance Corrective")
    with st.form("correctif"):
        d = st.date_input("Date", date.today())
        t = st.multiselect("Techniciens", techs)
        e = st.selectbox("Équipement", equips)
        prob = st.text_area("Problème / Cause d'arrêt")
        sol = st.text_area("Solution / Réparation")
        
        if st.form_submit_button("Enregistrer sur le Cloud"):
            if prob and sol and t:
                # Préparation de la nouvelle ligne
                new_row = pd.DataFrame([{
                    "Date": str(d),
                    "Techniciens": ", ".join(t),
                    "Equipement": e,
                    "Probleme": prob,
                    "Solution": sol
                }])
                # Lecture de l'existant et ajout
                old_df = load_data("Maintenance_Corrective")
                final_df = pd.concat([old_df, new_row], ignore_index=True)
                # Sauvegarde sur Google Sheets
                conn.update(spreadsheet=URL_SHEET, worksheet="Maintenance_Corrective", data=final_df)
                st.success("✅ Données synchronisées pour tout le monde !")
            else:
                st.error("Veuillez remplir tous les champs.")

elif menu == "Dashboard":
    st.title("📊 État de la Maintenance")
    df = load_data("Maintenance_Corrective")
    if not df.empty:
        st.write("Dernières pannes enregistrées (Direct depuis Google Sheets) :")
        st.dataframe(df.tail(10), use_container_width=True)
    else:
        st.info("Aucune donnée pour le moment.")
