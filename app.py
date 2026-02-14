import streamlit as st
from engine import salva_misurazioni, carica_dati, interpreta_bmi, ALTEZZA

st.set_page_config(page_title="Dieta & Progressi Domenico", layout="wide")

st.title("🏃‍♂️ Diario Dieta e Misure - Domenico")

# Sidebar per inserimento dati
st.sidebar.header("Inserisci Nuove Misure")
with st.sidebar.form("form_misure"):
    data = st.date_input("Data misurazione")
    peso = st.number_input("Peso (kg)", min_value=50.0,
                           max_value=200.0, value=138.35, step=0.1)
    collo = st.number_input("Collo (cm)", value=46)
    torace = st.number_input("Torace (cm)", value=135)
    vita = st.number_input("Vita (cm)", value=142)
    fianchi = st.number_input("Fianchi (cm)", value=145)
    coscia = st.number_input("Coscia (cm)", value=74)
    polso = st.number_input("Polso (cm)", value=21)

    submit = st.form_submit_button("Salva Progressi")

if submit:
    salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo)
    st.success("Dati salvati con successo!")

# Caricamento dati per la visualizzazione
df = carica_dati()

if df is not None:
    # Calcoli ultimi dati
    ultimo_peso = df['Peso'].iloc[-1]
    ultimo_bmi = df['BMI'].iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Peso Attuale", f"{ultimo_peso} kg")
    col2.metric("BMI", ultimo_bmi)
    col3.metric("Stato", interpreta_bmi(ultimo_bmi))

    st.divider()

    st.subheader("Storico Progressi")
    st.dataframe(df, use_container_width=True)

    # Grafico del peso
    st.line_chart(df.set_index("Data")["Peso"])
else:
    st.info("Benvenuto Domenico! Inserisci la tua prima misurazione per iniziare a tracciare i progressi.")
