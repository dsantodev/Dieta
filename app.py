import streamlit as st
from engine import salva_misurazioni, carica_dati, interpreta_bmi, aggiorna_tutto

st.set_page_config(page_title="Dieta & Progressi", layout="wide")

st.title("🏃‍♂️ Diario Dieta e Misure")

# Sidebar
st.sidebar.header("Inserisci Nuove Misure")
with st.sidebar.form("form_misure", clear_on_submit=True):
    data = st.date_input("Data misurazione")
    peso = st.number_input("Peso (kg)", min_value=40.0,
                           max_value=250.0, value=138.0, step=0.1)
    # ... (tutti gli altri input rimangono uguali)
    collo = st.number_input("Collo (cm)", value=46)
    torace = st.number_input("Torace (cm)", value=135)
    vita = st.number_input("Vita (cm)", value=142)
    fianchi = st.number_input("Fianchi (cm)", value=145)
    coscia = st.number_input("Coscia (cm)", value=74)
    polso = st.number_input("Polso (cm)", value=21)

    submit = st.form_submit_button("Salva Progressi")

if submit:
    salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo)
    st.success("Dati salvati!")
    st.rerun()

df = carica_dati()

if df is not None:
    # --- METRICHE ---
    ultimo_peso = df['Peso'].iloc[-1]
    precedente_peso = df['Peso'].iloc[-2] if len(df) > 1 else ultimo_peso
    delta_peso = round(ultimo_peso - precedente_peso, 2)

    ultimo_bmi = df['BMI'].iloc[-1]

    col1, col2, col3 = st.columns(3)
    col1.metric("Peso Attuale", f"{ultimo_peso} kg",
                delta=f"{delta_peso} kg", delta_color="inverse")
    col2.metric("BMI", ultimo_bmi)
    col3.metric("Stato", interpreta_bmi(ultimo_bmi))

    st.divider()

    # --- TABELLA EDITABILE (Senza Indice) ---
    st.subheader("Storico e Modifica Dati")
    st.info("💡 Puoi modificare i valori direttamente nella tabella qui sotto e cliccare 'Salva Modifiche'.")

    # Usiamo data_editor per permettere correzioni al volo
    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,  # <--- Rimuove l'indice 0, 1, 2
        num_rows="dynamic"  # Permette anche di eliminare righe
    )

    if st.button("Salva Modifiche Tabella"):
        aggiorna_tutto(edited_df)
        st.success("Dati aggiornati correttamente!")
        st.rerun()

    st.divider()

    # --- GRAFICO ---
    st.subheader("Andamento Peso")
    st.line_chart(df, x="Data", y="Peso")

else:
    st.info("Benvenuto! Inserisci la tua prima misurazione.")
