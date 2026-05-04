import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date

st.set_page_config(page_title="Maintenance Sync Cloud", layout="wide")

# CONFIGURATION DE LA CONNEXION
# Le code lit maintenant directement le fichier credentials.json que tu as mis sur GitHub
@st.cache_resource
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    return gspread.authorize(creds)

# Nom de ton Google Sheet
SHEET_NAME = "Base_Maintenance_Cloud"

def load_from_gsheet(worksheet_name):
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).worksheet(worksheet_name)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def save_to_gsheet(worksheet_name, new_row_dict):
    client = get_gspread_client()
    sheet = client.open(SHEET_NAME).worksheet(worksheet_name)
    sheet.append_row(list(new_row_dict.values()))

# Chargement des listes d'équipements (Depuis GitHub)
@st.cache_data
def get_lists():
    df_h = pd.read_excel("Historique_Correctif.xlsx", header=2)
    equips = sorted(df_h['Equipement'].dropna().unique().tolist())
    techs = sorted(df_h['Technicien'].dropna().unique().tolist())
    return equips, techs

equips, techs = get_lists()

# --- INTERFACE ---
st.sidebar.title("⚙️ Maintenance Sync")
menu = st.sidebar.radio("Menu", ["Dashboard", "Saisie Corrective"])

if menu == "Saisie Corrective":
    st.title("🛠️ Saisie Maintenance Corrective")
    with st.form("form_correctif"):
        col1, col2 = st.columns(2)
        d = col1.date_input("Date", date.today())
        t_list = col2.multiselect("Techniciens", techs)
        e = st.selectbox("Équipement", equips)
        prob = st.text_area("Problème")
        sol = st.text_area("Solution")
        
        if st.form_submit_button("Enregistrer sur le Cloud"):
            if prob and sol and t_list:
                new_data = {
                    "Date": str(d),
                    "Techniciens": ", ".join(t_list),
                    "Equipement": e,
                    "Probleme": prob,
                    "Solution": sol
                }
                save_to_gsheet("Maintenance_Corrective", new_data)
                st.success("✅ Synchronisé avec Google Sheets !")
            else:
                st.error("Veuillez remplir tous les champs.")

elif menu == "Dashboard":
    st.title("📊 Tableau de Bord")
    try:
        df = load_from_gsheet("Maintenance_Corrective")
        st.dataframe(df.tail(10), use_container_width=True)
    except:
        st.info("Aucune donnée ou erreur de lecture.")
