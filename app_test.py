import streamlit as st, sqlite3, pandas as pd, os
from datetime import date, timedelta

# --- CONFIGURATION ---
DB = 'maintenance_TEST.db'
FILE_HISTORIQUE = 'Historique_Correctif.xlsx'
PER = {'Q': 'Quotidienne', 'H': 'Hebdomadaire', 'Quotidienne': 'Quotidienne', 'Hebdomadaire': 'Hebdomadaire'}

def con(): return sqlite3.connect(DB)

def init():
    c = con(); cur = c.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS techniciens_correctif(id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT UNIQUE)')
    cur.execute('CREATE TABLE IF NOT EXISTS referentiel(id INTEGER PRIMARY KEY AUTOINCREMENT, technicien TEXT, equipement TEXT, point_controle TEXT, periodicite TEXT, criticite TEXT DEFAULT "Moyenne", actif INTEGER DEFAULT 1)')
    cur.execute('CREATE TABLE IF NOT EXISTS ref_correctif(id INTEGER PRIMARY KEY AUTOINCREMENT, nom_equipement TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS journal(id INTEGER PRIMARY KEY AUTOINCREMENT, date_realisation TEXT, technicien TEXT, equipement TEXT, point_controle TEXT, periodicite TEXT, realise TEXT, conforme TEXT, observation TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    # Table Corrective avec les nouvelles colonnes
    cur.execute('''CREATE TABLE IF NOT EXISTS corrective(
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        date TEXT, heure_debut TEXT, heure_fin TEXT, 
        equipement TEXT, cause_arret TEXT, description TEXT, 
        pdr_nom TEXT, quantite TEXT, technicien TEXT, specialite TEXT,
        en_marche TEXT, jour_meme TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.commit(); c.close()

def q(sql, params=()):
    c = con(); df = pd.read_sql_query(sql, c, params=params); c.close(); return df

def execsql(sql, params=()):
    c = con(); c.execute(sql, params); c.commit(); c.close()

def load_seed():
    if q('select count(*) n from techniciens_correctif').iloc[0, 0] == 0:
        if os.path.exists(FILE_HISTORIQUE):
            try:
                df_h = pd.read_excel(FILE_HISTORIQUE, header=2)
                if 'Technicien' in df_h.columns:
                    techs_bruts = df_h['Technicien'].dropna().unique()
                    for ligne in techs_bruts:
                        noms_separes = str(ligne).replace('+', ',').split(',')
                        for n in noms_separes:
                            nom_final = n.strip()
                            if nom_final and nom_final.lower() != "inconnu":
                                execsql('INSERT OR IGNORE INTO techniciens_correctif(nom) VALUES(?)', (nom_final,))
                if q('select count(*) n from ref_correctif').iloc[0,0] == 0:
                    df_h.columns = [str(c).strip() for c in df_h.columns]
                    if 'Equipement' in df_h.columns:
                        for e in df_h['Equipement'].dropna().unique():
                            execsql('insert into ref_correctif(nom_equipement) values(?)', (str(e),))
            except: pass

    if q('select count(*) n from referentiel').iloc[0, 0] == 0:
        files = [f for f in os.listdir('.') if f.endswith('.xlsx') and f not in [FILE_HISTORIQUE, 'export_complet_test.xlsx']]
        for f in files:
            tech_file = os.path.splitext(f)[0]
            try: xl = pd.ExcelFile(f); 
            except: continue
            for sh in xl.sheet_names:
                df = pd.read_excel(f, sh, header=None)
                equip = None
                for _, r in df.iterrows():
                    vals = [str(x).strip() for x in r.tolist() if pd.notna(x) and str(x).strip() != '']
                    if not vals: continue
                    first = vals[0]
                    if len(vals) == 1 and len(first) < 80 and not any(w in first.lower() for w in ['gamme','technicien','date']): equip = first
                    per = None
                    for v in vals[1:4]:
                        if v in PER: per = PER[v]
                    if per and len(first) > 8:
                        execsql('insert into referentiel(technicien,equipement,point_controle,periodicite) values(?,?,?,?)', (tech_file, equip or sh, first, per))

# --- PAGES ---

def saisie_corrective():
    st.title('🛠️ Saisie Maintenance Corrective')
    
    # LISTES TRIÉES PAR ORDRE ALPHABÉTIQUE
    equips = sorted(q('select nom_equipement from ref_correctif')['nom_equipement'].tolist())
    techs_correctif = sorted(q('select nom from techniciens_correctif')['nom'].tolist())

    with st.form('f_correctif'):
        # Ligne 1
        col1, col2, col3 = st.columns(3)
        d = col1.date_input('Date', date.today())
        h_deb = col2.text_input('Heure Début (HH:MM)', value="08:00")
        h_fin = col3.text_input('Heure Fin (HH:MM)', value="09:00")
        
        # Ligne 2
        col4, col5, col6 = st.columns([1, 1.5, 1])
        e = col4.selectbox('Équipement (A-Z)', equips)
        t_list = col5.multiselect('Technicien(s) intervenant(s) (A-Z)', techs_correctif)
        spec = col6.selectbox('Spécialité', ['Electrique', 'Mécanique'])

        # NOUVELLE LIGNE : Statuts Oui/Non
        st.write("---")
        c_status1, c_status2 = st.columns(2)
        en_marche = c_status1.radio("L'équipement est-il en marche après intervention ?", ["Oui", "Non"], horizontal=True)
        jour_meme = c_status2.radio("L'intervention a-t-elle été faite le jour même ?", ["Oui", "Non"], horizontal=True)
        st.write("---")
        
        cause = st.text_area('Cause de l\'arrêt / Problème')
        desc = st.text_area('Description de la réparation / Solution')
        
        col7, col8 = st.columns([3, 1])
        pdr = col7.text_input('Pièce de rechange (PDR)')
        qte = col8.text_input('Quantité', "0")
        
        if st.form_submit_button('Enregistrer l\'intervention'):
            if cause and desc and t_list:
                t_string = ", ".join(t_list)
                execsql('''insert into corrective(date, heure_debut, heure_fin, equipement, cause_arret, description, pdr_nom, quantite, technicien, specialite, en_marche, jour_meme) 
                           values(?,?,?,?,?,?,?,?,?,?,?,?)''',
                        (str(d), h_deb, h_fin, e, cause, desc, pdr, qte, t_string, spec, en_marche, jour_meme))
                st.success('Intervention enregistrée !')
                st.rerun()
            else:
                st.error('Veuillez remplir les techniciens, la cause et la description.')

    st.subheader('Dernières pannes enregistrées')
    st.dataframe(q('select * from corrective order by id desc limit 15'), use_container_width=True)

# --- (Les autres fonctions restent identiques) ---
def dashboard():
    st.title('📊 Dashboard'); c1, c2 = st.columns(2); c1.metric("Préventif", q('select count(*) n from journal').iloc[0,0]); c2.metric("Correctif", q('select count(*) n from corrective').iloc[0,0])

def saisie_preventive():
    st.title('📝 Saisie conduite'); ref = q('select * from referentiel where actif=1 order by technicien,equipement')
    if ref.empty: st.warning('Référentiel vide.'); return
    with st.form('s_p'):
        d = st.date_input('Date', date.today()); t = st.selectbox('Technicien', sorted(ref.technicien.unique()))
        e = st.selectbox('Équipement', sorted(ref[ref.technicien==t].equipement.dropna().unique()))
        sub = ref[(ref.technicien==t)&(ref.equipement==e)]; label = st.selectbox('Point de contrôle', [f"{r.id} | {r.point_controle}" for r in sub.itertuples()])
        res = st.radio('Réalisé ?', ['Oui', 'Non'], horizontal=True)
        if st.form_submit_button('Enregistrer'):
            rid = int(label.split('|')[0].strip()); r = ref[ref.id==rid].iloc[0]
            execsql('insert into journal(date_realisation,technicien,equipement,point_controle,periodicite,realise) values(?,?,?,?,?,?)',(str(d),t,e,r.point_controle,r.periodicite,res))
            st.success('Enregistré !')

def referentiel():
    st.title('📋 Référentiels'); t1, t2 = st.tabs(["Préventif", "Correctif"])
    with t1: st.dataframe(q('select * from referentiel'))
    with t2: st.dataframe(q('select * from ref_correctif'))

def export():
    st.title('💾 Exportation'); fname = 'export_complet_test.xlsx'
    with pd.ExcelWriter(fname) as w:
        q('select * from journal').to_excel(w, 'Preventif', index=False)
        q('select * from corrective').to_excel(w, 'Correctif', index=False)
    with open(fname, 'rb') as f: st.download_button('Télécharger Excel', f, fname)

init(); load_seed()
st.sidebar.title('⚙️ Test Maintenance')
page = st.sidebar.radio('Menu', ['Tableau de bord', 'Saisie conduite', 'Saisie corrective', 'Référentiel', 'Exportation'])
mapping = {'Tableau de bord': dashboard, 'Saisie conduite': saisie_preventive, 'Saisie corrective': saisie_corrective, 'Référentiel': referentiel, 'Exportation': export}
mapping[page]()