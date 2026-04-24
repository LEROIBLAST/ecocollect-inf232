import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="EcoCollect Pro - Analyse Descriptive",
    page_icon="♻️",
    layout="wide"
)

# --- 2. PARAMÈTRES MÉTIER ---
DB_FILE = "database_collecte.csv"

# Coefficients CO2 et leurs justifications
CO2_DATA = {
    "Métal": {"coeff": 2.5, "desc": "Économise l'extraction minière (Aluminium, Fer)."},
    "Plastique": {"coeff": 1.5, "desc": "Évite la production de polymères issus du pétrole."},
    "Papier/Carton": {"coeff": 0.9, "desc": "Réduit la consommation d'eau et d'arbres."},
    "Organique": {"coeff": 0.5, "desc": "Évite la fermentation et le rejet de méthane."},
    "Verre": {"coeff": 0.3, "desc": "Évite la fusion du sable à très haute température."},
    "Autre": {"coeff": 0.1, "desc": "Estimation minimale pour déchets divers."}
}

# --- 3. LOGIQUE DE DONNÉES ---
def load_data():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            df['Date'] = pd.to_datetime(df['Date'])
            return df
        except Exception:
            return create_empty_df()
    return create_empty_df()

def create_empty_df():
    return pd.DataFrame(columns=["Date", "Agent", "Secteur", "Type_Dechet", "Poids_kg", "CO2_Economise"])

def save_data(df):
    df.to_csv(DB_FILE, index=False)

data = load_data()

# --- 4. INTERFACE : MODE DE FONCTIONNEMENT & INDICATEURS ---
st.title("♻️ EcoCollect Pro : Plateforme de Gestion Environnementale")

with st.expander("📖 Guide d'utilisation & Interprétation des indicateurs", expanded=True):
    col_info1, col_info2 = st.columns([1, 1])
    
    with col_info1:
        st.markdown("""
        ### 🚀 Comment utiliser l'outil ?
        1. **Saisie** : Remplissez le formulaire à gauche (Nom, Nature, Poids).
        2. **Calcul** : Le système calcule automatiquement le **CO2 Économisé** par cette action.
        3. **Visualisation** : Les graphiques analysent vos performances en temps réel.
        
        ### 🔍 Comprendre les indicateurs
        * **CO2 Économisé (Ligne)** : C'est le bénéfice écologique de chaque pesée ($Poids \\times Coeff$).
        * **Impact Global (Somme)** : C'est le succès total de votre collecte. Plus il est haut, plus vous avez sauvé la planète.
        * **Efficacité (Qualité)** : C'est votre score de 'Qualité'. Il divise l'Impact par le Poids. 
            * *Exemple :* Une efficacité de **2.5** signifie que chaque kg ramassé est très précieux (Métal), alors qu'un **0.3** signifie que vous ramassez beaucoup de poids pour peu de gain (Verre).
        """)
        
    with col_info2:
        st.markdown("### 📊 Barème des Coefficients")
        df_expl = pd.DataFrame([
            {"Nature": k, "Coeff (kgCO2/kg)": v["coeff"], "Justification": v["desc"]} 
            for k, v in CO2_DATA.items()
        ])
        st.table(df_expl)

# --- 5. FORMULAIRE DE COLLECTE (SIDEBAR) ---
st.sidebar.header("📥 Enregistrement")
with st.sidebar.form("form_collecte", clear_on_submit=True):
    agent = st.text_input("Identifiant Agent", placeholder="Votre nom")
    date_saisie = st.date_input("Date", datetime.now())
    secteur = st.selectbox("Provenance", ["Ménager", "Industriel", "Hospitalier", "Commercial", "Autre"])
    type_dechet = st.selectbox("Nature du produit", list(CO2_DATA.keys()))
    poids = st.number_input("Masse collectée (kg)", min_value=0.1, step=0.5)
    
    submit = st.form_submit_button("Valider la saisie")

if submit:
    if agent.strip() == "":
        st.sidebar.error("⚠️ Identifiant requis.")
    else:
        # Calcul métier
        impact_individuel = round(poids * CO2_DATA[type_dechet]["coeff"], 2)
        
        new_entry = pd.DataFrame({
            "Date": [pd.to_datetime(date_saisie)],
            "Agent": [agent],
            "Secteur": [secteur],
            "Type_Dechet": [type_dechet],
            "Poids_kg": [poids],
            "CO2_Economise": [impact_individuel]
        })
        
        data = pd.concat([data, new_entry], ignore_index=True)
        save_data(data)
        st.sidebar.success(f"Bravo {agent} ! Impact : +{impact_individuel}kg CO2")
        st.rerun()

# --- 6. ANALYSE DESCRIPTIVE ---
if not data.empty:
    st.markdown("---")
    # Calcul des KPIs globaux
    total_poids = data['Poids_kg'].sum()
    total_impact = data['CO2_Economise'].sum()
    score_efficacite = total_impact / total_poids if total_poids > 0 else 0

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Poids Total", f"{total_poids:.1f} kg", "Masse")
    kpi2.metric("Impact Global", f"{total_impact:.1f} kg CO₂", "Cumul")
    kpi3.metric("Efficacité (Qualité)", f"{score_efficacite:.2f}", "Indice")

    st.markdown("---")
    
    # Graphiques
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.sunburst(data, path=['Secteur', 'Type_Dechet'], values='Poids_kg', 
                                  title="Structure de la Collecte"), use_container_width=True)
    with c2:
        perf = data.groupby('Agent')['Poids_kg'].sum().reset_index()
        st.plotly_chart(px.bar(perf, x='Agent', y='Poids_kg', title="Performance par Agent", color_discrete_sequence=['#2ecc71']), use_container_width=True)

    with st.expander("📂 Consulter la base de données complète"):
        st.dataframe(data.sort_values(by="Date", ascending=False), use_container_width=True)
        
        # Actions de fichier
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter les données (CSV)", csv, "ecocollect_data.csv", "text/csv")
        with col_ex2:
            if st.button("🗑️ Supprimer le dernier enregistrement"):
                if len(data) > 0:
                    data = data[:-1]
                    save_data(data)
                    st.rerun()
else:
    st.info("👋 Bienvenue. Le système attend votre première collecte pour générer les analyses.")
