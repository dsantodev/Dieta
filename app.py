import streamlit as st
import pandas as pd
import plotly.express as px  # <--- Nuova libreria per grafici seri
from engine import salva_misurazioni, carica_dati, interpreta_bmi, aggiorna_tutto

st.set_page_config(page_title="Dieta & Progressi", layout="wide")

# --- CSS Personalizzato per migliorare l'estetica ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05); 
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏃‍♂️ Diario Dieta e Misure")

# --- SIDEBAR ---
with st.sidebar:
    st.header("📏 Nuove Misure")
    with st.form("form_misure", clear_on_submit=True):
        data = st.date_input("Data misurazione")
        peso = st.number_input("Peso (kg)", min_value=50.0,
                               max_value=250.0, value=138.0, step=0.1)

        st.markdown("---")
        polso = st.number_input(
            "Polso (cm)", value=21, help="Misura il polso subito sopra l'osso della mano")
        collo = st.number_input("Collo (cm)", value=46)
        torace = st.number_input("Torace (cm)", value=135)
        vita = st.number_input("Vita (cm)", value=142)
        fianchi = st.number_input("Fianchi (cm)", value=145)
        coscia = st.number_input("Coscia (cm)", value=74)

        submit = st.form_submit_button("💾 Salva Progressi")

if submit:
    # Passiamo correttamente tutti i parametri, incluso il polso
    salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo)
    st.success("Dati salvati con successo!")
    st.rerun()

df = carica_dati()

if df is not None:
    # --- IMPORTANTE: Ordiniamo i dati per data per evitare salti nel grafico ---
    df['Data'] = pd.to_datetime(df['Data'])
    df = df.sort_values(by="Data").reset_index(drop=True)
    # Riportiamo la data a un formato leggibile per la tabella
    df['Data'] = df['Data'].dt.date

    # --- METRICHE ---
    ultimo_peso = df['Peso'].iloc[-1]
    precedente_peso = df['Peso'].iloc[-2] if len(df) > 1 else ultimo_peso
    delta_peso = round(ultimo_peso - precedente_peso, 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Peso Attuale", f"{ultimo_peso} kg",
                delta=f"{delta_peso} kg", delta_color="inverse")
    col2.metric("BMI", df['BMI'].iloc[-1])
    col3.metric("Stato", interpreta_bmi(df['BMI'].iloc[-1]))

    st.divider()

    # --- GRAFICO INTERATTIVO (PLOTLY) ---
    st.subheader("📈 Andamento Peso nel Tempo")

    # Creazione grafico Plotly
    fig = px.line(df, x="Data", y="Peso",
                  markers=True,  # Aggiunge i puntini sulle date
                  text="Peso",   # Mostra il numero sopra il punto
                  title="Variazione Peso Corporeo")

    fig.update_traces(textposition="top center",
                      line_color="#007BFF", marker_size=10)
    fig.update_layout(
        xaxis_title="Data",
        yaxis_title="Peso (kg)",
        hovermode="x unified",  # Quando passi il mouse vedi i dati di quel giorno
        margin=dict(l=20, r=20, t=40, b=20),
        height=500  # Altezza fissa per non dover scrollare troppo
    )

    # Visualizza il grafico
    fig.update_yaxes(range=[df['Peso'].min() - 2, df['Peso'].max() + 2])
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # --- TABELLA EDITABILE ---
    st.subheader("📑 Storico e Correzioni")
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic"
    )

    if st.button("Conferma Modifiche Tabella"):
        aggiorna_tutto(edited_df)
        st.success("Modifiche salvate con successo!")
        st.rerun()
else:
    st.info("Inizia inserendo i tuoi dati nella barra laterale!")
