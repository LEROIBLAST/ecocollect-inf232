import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="EcoCollect Pro - Système Autonome",
    page_icon="♻️",
    layout="wide"
)

# --- 2. PARAMÈTRES TECHNIQUES & MÉTIER ---
DB_FILE = "database_collecte.csv"

# Coefficients CO2 et leurs justifications (Pour l'aspect pédagogique)
CO2_DATA = {
    "Métal": {"coeff": 2.5, "desc": "Économise l'extraction minière très énergivore."},
    "Plastique": {"coeff": 1.5, "desc": "Évite la transformation du pétrole brut."},
    "Papier/Carton": {"coeff": 0.9, "desc": "Réduit la déforestation et l'usage d'eau."},
    "Organique": {"coeff": 0.5, "desc": "Évite le rejet de méthane en décharge."},
    "Verre": {"coeff": 0.3, "desc": "Recyclable à l'infini mais lourd à transporter."},
    "Autre": {"coeff": 0.1, "desc": "Impact environnemental minimal estimé."}
}

# --- 3. GESTION DES DONNÉES (ROBUSTESSE) ---
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

# --- 4. INTERFACE : GUIDE DE FONCTIONNEMENT ---
st.title("♻️ EcoCollect Pro : Collecte & Analyse Descriptive")

with st.expander("📖 Mode de fonctionnement & Justification de l'Impact", expanded=True):
    col_g1, col_g2 = st.columns([1, 1.5])
    
    with col_g1:
        st.markdown("""
        ### Comment utiliser l'application ?
        1. **Identification** : Saisissez votre nom dans le formulaire à gauche.
        2. **Saisie** : Renseignez la nature et le poids du produit collecté.
        3. **Validation** : Cliquez sur 'Enregistrer'. Les données sont stockées instantanément.
        4. **Analyse** : Observez les graphiques de performance et d'impact en temps réel.
        """)
        
    with col_g2:
        st.markdown("### Pourquoi le CO2 varie selon le déchet ?")
        # Création d'un petit tableau explicatif pour le prof
        df_expl = pd.DataFrame([
            {"Nature": k, "Coeff (kgCO2/kg)": v["coeff"], "Explication": v["desc"]} 
            for k, v in CO2_DATA.items()
        ])
        st.table(df_expl)

# --- 5. BARRE LATÉRALE : FORMULAIRE (INPUT) ---
st.sidebar.header("📥 Formulaire de Collecte")
with st.sidebar.form("form_collecte", clear_on_submit=True):
    agent = st.text_input("Nom de l'Agent", placeholder="Ex: Jean Moussa")
    date_saisie = st.date_input("Date de l'opération", datetime.now())
    secteur = st.selectbox("Secteur de provenance", ["Ménager", "Industriel", "Hospitalier", "Commercial", "Autre"])
    type_dechet = st.selectbox("Nature du déchet", list(CO2_DATA.keys()))
    poids = st.number_input("Poids total (kg)", min_value=0.1, step=0.5)
    
    submit_button = st.form_submit_button("Enregistrer la collecte")

if submit_button:
    if agent.strip() == "":
        st.sidebar.error("⚠️ Le nom de l'agent est obligatoire.")
    else:
        # Utilisation du coefficient correspondant
        coeff = CO2_DATA[type_dechet]["coeff"]
        co2_val = round(poids * coeff, 2)
        
        new_row = pd.DataFrame({
            "Date": [pd.to_datetime(date_saisie)],
            "Agent": [agent],
            "Secteur": [secteur],
            "Type_Dechet": [type_dechet],
            "Poids_kg": [poids],
            "CO2_Economise": [co2_val]
        })
        
        data = pd.concat([data, new_row], ignore_index=True)
        save_data(data)
        st.sidebar.success(f"✅ Enregistré ! Impact : +{co2_val}kg CO2")
        st.rerun()

# --- 6. ANALYSE DESCRIPTIVE (OUTPUT) ---
if not data.empty:
    st.markdown("---")
    # KPIs
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Poids Total", f"{data['Poids_kg'].sum():.1f} kg")
    m2.metric("Impact Global", f"{data['CO2_Economise'].sum():.1f} kg CO₂")
    m3.metric("Nb Collectes", len(data))
    m4.metric("Efficacité", f"{(data['CO2_Economise'].sum()/data['Poids_kg'].sum()):.2f} pts")

    # Visualisations
    tab1, tab2 = st.tabs(["📊 Répartitions", "📑 Registre des données"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            fig_sun = px.sunburst(data, path=['Secteur', 'Type_Dechet'], values='Poids_kg', 
                                  title="Hiérarchie Secteur / Nature")
            st.plotly_chart(fig_sun, use_container_width=True)
        with c2:
            df_agent = data.groupby('Agent')['Poids_kg'].sum().reset_index()
            fig_bar = px.bar(df_agent, x='Agent', y='Poids_kg', title="Volume par Agent", color='Agent')
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab2:
        st.dataframe(data.sort_values(by="Date", ascending=False), use_container_width=True)
        
        # Outils de gestion
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            csv = data.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter en CSV", csv, "collecte_eco.csv", "text/csv")
        with col_d2:
            if st.button("🗑️ Supprimer la dernière entrée"):
                if len(data) > 0:
                    data = data[:-1]
                    save_data(data)
                    st.rerun()
else:
    st.info("👋 Système prêt. Enregistrez une collecte pour activer le tableau de bord.")
