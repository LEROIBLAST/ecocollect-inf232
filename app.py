import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="EcoCollect Pro - Gestion & Impact",
    page_icon="♻️",
    layout="wide"
)

# --- 2. PARAMÈTRES TECHNIQUES & MÉTIER ---
DB_FILE = "database_collecte.csv"

# Facteurs d'impact : kg de CO2 économisé par kg de déchet recyclé
CO2_FACTORS = {
    "Plastique": 1.5,
    "Papier/Carton": 0.9,
    "Verre": 0.3,
    "Métal": 2.5,
    "Organique": 0.5,
    "Autre": 0.1
}

# --- 3. FONCTIONS DE GESTION DES DONNÉES (ROBUSTESSE) ---
def load_data():
    """Charge les données depuis le CSV ou crée un DataFrame vide structuré."""
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
    """Sauvegarde les données en temps réel dans le fichier CSV."""
    df.to_csv(DB_FILE, index=False)

# Chargement initial des données
data = load_data()

# --- 4. BARRE LATÉRALE : COLLECTE DES DONNÉES (INPUT) ---
st.sidebar.header("📥 Formulaire de Collecte")
st.sidebar.markdown("Saisissez les informations du produit collecté.")

with st.sidebar.form("form_collecte", clear_on_submit=True):
    # Identification de l'utilisateur (Agent)
    agent = st.text_input("Nom de l'Agent / Collecteur", placeholder="Ex: Jean Moussa")
    
    # Détails de la collecte
    date_saisie = st.date_input("Date de l'opération", datetime.now())
    secteur = st.selectbox("Secteur de provenance", ["Ménager", "Industriel", "Hospitalier", "Commercial", "Autre"])
    type_dechet = st.selectbox("Nature du déchet", list(CO2_FACTORS.keys()))
    poids = st.number_input("Poids total (kg)", min_value=0.1, step=0.5)
    
    submit_button = st.form_submit_button("Enregistrer la collecte")

# Logique d'enregistrement après clic
if submit_button:
    if agent.strip() == "":
        st.sidebar.error("⚠️ Veuillez entrer un nom d'agent.")
    else:
        # Calcul automatique de l'impact
        co2_val = round(poids * CO2_FACTORS[type_dechet], 2)
        
        # Création de la nouvelle ligne
        new_row = pd.DataFrame({
            "Date": [pd.to_datetime(date_saisie)],
            "Agent": [agent],
            "Secteur": [secteur],
            "Type_Dechet": [type_dechet],
            "Poids_kg": [poids],
            "CO2_Economise": [co2_val]
        })
        
        # Mise à jour et sauvegarde immédiate (Temps Réel)
        data = pd.concat([data, new_row], ignore_index=True)
        save_data(data)
        st.sidebar.success(f"✅ Enregistré par {agent} ! (+{co2_val}kg CO2)")

# --- 5. INTERFACE PRINCIPALE : ANALYSE DESCRIPTIVE (OUTPUT) ---
st.title("♻️ EcoCollect Pro : Tableau de Bord")
st.markdown("Analyse descriptive des flux de déchets et de l'impact environnemental.")

if not data.empty:
    # --- SECTION FILTRES ---
    with st.expander("🔍 Filtres de recherche", expanded=False):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            agents_list = st.multiselect("Filtrer par Agent", data["Agent"].unique(), default=data["Agent"].unique())
        with col_f2:
            secteurs_list = st.multiselect("Filtrer par Secteur", data["Secteur"].unique(), default=data["Secteur"].unique())
        with col_f3:
            types_list = st.multiselect("Filtrer par Nature", data["Type_Dechet"].unique(), default=data["Type_Dechet"].unique())

    # Application des filtres
    filtered_df = data[
        (data["Agent"].isin(agents_list)) & 
        (data["Secteur"].isin(secteurs_list)) & 
        (data["Type_Dechet"].isin(types_list))
    ]

    # --- SECTION KPIs (MÉTRIQUES) ---
    st.markdown("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Poids Total", f"{filtered_df['Poids_kg'].sum():.1f} kg")
    m2.metric("CO₂ Économisé", f"{filtered_df['CO2_Economise'].sum():.1f} kg")
    m3.metric("Nb Collectes", len(filtered_df))
    m4.metric("Productivité Moyenne", f"{(filtered_df['Poids_kg'].mean() if len(filtered_df)>0 else 0):.1f} kg/saisie")

    # --- SECTION VISUALISATION ---
    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📊 Analyses Globales", "👤 Performance Agents", "📑 Données Brutes"])

    with tab1:
        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            fig_sun = px.sunburst(filtered_df, path=['Secteur', 'Type_Dechet'], values='Poids_kg', title="Répartition Secteur / Nature")
            st.plotly_chart(fig_sun, use_container_width=True)
        with col_chart2:
            df_time = filtered_df.groupby('Date')['Poids_kg'].sum().reset_index()
            fig_line = px.line(df_time, x='Date', y='Poids_kg', title="Évolution des volumes collectés", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)

    with tab2:
        # Analyse par Agent
        df_agent = filtered_df.groupby('Agent').agg({'Poids_kg': 'sum', 'CO2_Economise': 'sum'}).reset_index()
        fig_bar = px.bar(df_agent, x='Agent', y='Poids_kg', color='CO2_Economise', 
                         title="Volume de collecte par Agent (Couleur = Impact CO2)",
                         text_auto='.1s')
        st.plotly_chart(fig_bar, use_container_width=True)

    with tab3:
        st.dataframe(filtered_df.sort_values(by="Date", ascending=False), use_container_width=True)
        
        # Fonctions de gestion de fichier
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Télécharger l'extraction CSV", csv, "export_eco_collect.csv", "text/csv")
        with col_btn2:
            if st.button("🗑️ Supprimer la dernière entrée"):
                if len(data) > 0:
                    data = data[:-1]
                    save_data(data)
                    st.rerun()

else:
    st.info("👋 Bienvenue ! Le système est prêt. Utilisez le formulaire à gauche pour enregistrer votre première collecte.")