import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import date

# --- CONFIGURATION CLOUD ---
# Remplace par l'URL de ton Google Sheet partagé
URL_SHEET = "https://docs.google.com/spreadsheets/d/18kJOh6IknPJDF68snoiXVxe-aa923rQAQ1qDaeolXfM/edit?usp=sharing"

st.set_page_config(page_title="Maintenance Sync Cloud", layout="wide")

# Connexion à Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

def load_data(sheet_name):
    try:
        df = conn.read(spreadsheet=URL_SHEET, worksheet=sheet_name)
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# Chargement des listes depuis ton fichier Excel sur GitHub
@st.cache_data
def get_lists():
    try:
        df_h = pd.read_excel("Historique_Correctif.xlsx", header=2)
        equips = sorted(df_h['Equipement'].dropna().unique().tolist())
        techs = sorted(df_h['Technicien'].dropna().unique().tolist())
        return equips, techs
    except:
        return ["Erreur chargement"], ["Erreur chargement"]

equips, techs = get_lists()

# --- INTERFACE ---
st.sidebar.title("⚙️ Maintenance Sync")
menu = st.sidebar.radio("Menu", ["Dashboard", "Saisie Conduite", "Saisie Corrective"])

if menu == "Dashboard":
    st.title("📊 Tableau de Bord")
    c1, c2 = st.columns(2)
    
    df_prev = load_data("Journal_Preventif")
    df_corr = load_data("Maintenance_Corrective")
    
    with c1:
        st.metric("Conduites réalisées", len(df_prev) if not df_prev.empty else 0)
    with c2:
        st.metric("Pannes enregistrées", len(df_corr) if not df_corr.empty else 0)
    
    if not df_corr.empty:
        st.subheader("Dernières pannes (Direct Google Sheets)")
        st.dataframe(df_corr.tail(10), use_container_width=True)

elif menu == "Saisie Conduite":
    st.title("📝 Saisie Conduite (Préventif)")
    st.info("Cette section enregistre les données dans l'onglet 'Journal_Preventif'")
    
    with st.form("form_preventif"):
        d = st.date_input("Date", date.today())
        t = st.selectbox("Technicien", techs)
        e = st.selectbox("Équipement", equips)
        obs = st.text_area("Observations / Points de contrôle")
        etat = st.radio("Conforme ?", ["Oui", "Non", "N/A"], horizontal=True)
        
        if st.form_submit_button("Enregistrer la conduite"):
            new_row = pd.DataFrame([{"Date": str(d), "Technicien": t, "Equipement": e, "Observation": obs, "Conforme": etat}])
            old_df = load_data("Journal_Preventif")
            final_df = pd.concat([old_df, new_row], ignore_index=True)
            conn.update(spreadsheet=URL_SHEET, worksheet="Journal_Preventif", data=final_df)
            st.success("✅ Conduite enregistrée et synchronisée !")

elif menu == "Saisie Corrective":
    st.title("🛠️ Saisie Maintenance Corrective")
    with st.form("form_correctif"):
        col1, col2 = st.columns(2)
        d = col1.date_input("Date de la panne", date.today())
        t_list = col2.multiselect("Technicien(s) intervenant(s)", techs)
        
        e = st.selectbox("Équipement concerné", equips)
        prob = st.text_area("Cause de l'arrêt / Problème")
        sol = st.text_area("Description de la réparation / Solution")
        
        st.write("---")
        c_status1, c_status2 = st.columns(2)
        en_marche = c_status1.radio("L'équipement est-il en marche ?", ["Oui", "Non"], horizontal=True)
        fiche_recue = c_status2.radio("Fiche d'intervention reçue le jour même ?", ["Oui", "Non"], horizontal=True)
        
        if st.form_submit_button("Enregistrer l'intervention"):
            if prob and sol and t_list:
                new_row = pd.DataFrame([{
                    "Date": str(d),
                    "Techniciens": ", ".join(t_list),
                    "Equipement": e,
                    "Probleme": prob,
                    "Solution": sol,
                    "En_Marche": en_marche,
                    "Fiche_Recue": fiche_recue
                }])
                old_df = load_data("Maintenance_Corrective")
                final_df = pd.concat([old_df, new_row], ignore_index=True)
                conn.update(spreadsheet=URL_SHEET, worksheet="Maintenance_Corrective", data=final_df)
                st.success("✅ Panne enregistrée sur le Cloud !")
            else:
                st.error("Veuillez remplir les techniciens, le problème et la solution.")
