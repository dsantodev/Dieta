from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
from engine import (
    aggiorna_tutto,
    carica_config,
    carica_dati,
    interpreta_bmi,
    salva_config,
    salva_misurazioni,
)

st.set_page_config(page_title="Dieta & Progressi", layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
    }
    [data-testid="stSidebar"] h2 {
        text-align: center;
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

config = carica_config()
df = carica_dati()

if config is None:
    st.title("Setup iniziale Diario Dieta")
    st.info("Compila i dati base. Verrà creato automaticamente il nuovo profilo.")

    with st.form("setup_iniziale"):
        nome = st.text_input("Come ti chiami?", value="")
        eta = st.number_input("Età", min_value=1,
                              max_value=120, value=35, step=1)
        altezza_cm = st.number_input(
            "Altezza (cm)", min_value=120.0, max_value=230.0, value=176.0, step=0.1)
        peso_iniziale = st.number_input(
            "Peso attuale (kg)", min_value=40.0, max_value=300.0, value=100.0, step=0.1)

        st.markdown("---")
        st.caption("Prima misurazione (opzionale ma consigliata)")
        salva_prima_misura = st.checkbox(
            "Salva anche la prima misurazione di oggi", value=True)
        polso = st.number_input(
            "Polso (cm)", min_value=5.0, max_value=40.0, value=21.0, step=0.1)
        collo = st.number_input(
            "Collo (cm)", min_value=10.0, max_value=80.0, value=46.0, step=0.1)
        torace = st.number_input(
            "Torace (cm)", min_value=30.0, max_value=250.0, value=135.0, step=0.1)
        vita = st.number_input("Vita (cm)", min_value=30.0,
                               max_value=250.0, value=142.0, step=0.1)
        fianchi = st.number_input(
            "Fianchi (cm)", min_value=30.0, max_value=250.0, value=145.0, step=0.1)
        coscia = st.number_input(
            "Coscia (cm)", min_value=20.0, max_value=150.0, value=74.0, step=0.1)

        crea_config = st.form_submit_button("Crea profilo")

    if crea_config:
        nome_pulito = nome.strip() or "Utente"
        config = {
            "nome": nome_pulito,
            "eta": int(eta),
            "altezza_m": round(float(altezza_cm) / 100, 2),
            "peso_iniziale": float(peso_iniziale),
        }
        salva_config(config)

        if salva_prima_misura:
            salva_misurazioni(
                date.today(),
                float(peso_iniziale),
                float(polso),
                float(torace),
                float(vita),
                float(fianchi),
                float(coscia),
                float(collo),
                config["altezza_m"],
            )

        st.success("Profilo creato con successo.")
        st.rerun()

    st.stop()

nome_utente = config.get("nome", "Utente")
altezza_m = float(config.get("altezza_m", 1.76))

st.title(f"Diario Dieta e Misure di {nome_utente}")

if df is not None:
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values(
        by="Data").reset_index(drop=True)


def _last_or_default(colonna: str, fallback: float) -> float:
    if df is None or df.empty or colonna not in df.columns:
        return fallback
    valore = df[colonna].iloc[-1]
    if pd.isna(valore):
        return fallback
    return float(valore)


last_date = date.today()
if df is not None and not df.empty:
    last_date = df["Data"].iloc[-1].date()

with st.sidebar:
    st.header("Parametri Biometrici")
    with st.form("form_misure", clear_on_submit=False):
        data = st.date_input("Data misurazione", value=date.today())
        peso = st.number_input(
            "Peso (kg)",
            min_value=40.0,
            max_value=300.0,
            value=_last_or_default("Peso", float(
                config.get("peso_iniziale", 100.0))),
            step=0.1,
        )

        st.markdown("---")
        polso = st.number_input(
            "Polso (cm)",
            min_value=5.0,
            max_value=40.0,
            value=_last_or_default("Polso", 21.0),
            step=0.1,
            help="Misura il polso subito sopra l'osso della mano",
        )
        collo = st.number_input("Collo (cm)", min_value=10.0, max_value=80.0,
                                value=_last_or_default("Collo", 46.0), step=0.1)
        torace = st.number_input("Torace (cm)", min_value=30.0, max_value=250.0,
                                 value=_last_or_default("Torace", 135.0), step=0.1)
        vita = st.number_input("Vita (cm)", min_value=30.0, max_value=250.0,
                               value=_last_or_default("Vita", 142.0), step=0.1)
        fianchi = st.number_input("Fianchi (cm)", min_value=30.0, max_value=250.0,
                                  value=_last_or_default("Fianchi", 145.0), step=0.1)
        coscia = st.number_input("Coscia (cm)", min_value=20.0, max_value=150.0,
                                 value=_last_or_default("Coscia", 74.0), step=0.1)

        submit = st.form_submit_button("Salva Progressi")

if submit:
    salva_misurazioni(data, peso, polso, torace, vita,
                      fianchi, coscia, collo, altezza_m)
    st.success("Dati salvati con successo.")
    st.rerun()

df = carica_dati()

if df is not None:
    df = df.copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df = df.dropna(subset=["Data"]).sort_values(
        by="Data").reset_index(drop=True)

    ultimo_peso = df["Peso"].iloc[-1]
    precedente_peso = df["Peso"].iloc[-2] if len(df) > 1 else ultimo_peso
    delta_peso = round(float(ultimo_peso) - float(precedente_peso), 2)

    col1, col2, col3 = st.columns(3)
    col1.metric("Peso Attuale", f"{ultimo_peso:.1f} kg",
                delta=f"{delta_peso:+.2f} kg", delta_color="inverse")
    col2.metric("BMI", df["BMI"].iloc[-1])
    col3.metric("Stato", interpreta_bmi(float(df["BMI"].iloc[-1])))

    st.divider()

    st.subheader("Andamento Peso nel Tempo")
    min_data = df["Data"].min().date()
    max_data = df["Data"].max().date()

    filtro1, filtro2 = st.columns(2)
    data_da = filtro1.date_input(
        "Dal", value=min_data, min_value=min_data, max_value=max_data)
    data_a = filtro2.date_input(
        "Al", value=max_data, min_value=min_data, max_value=max_data)

    filtro_df = df[(df["Data"].dt.date >= data_da) &
                   (df["Data"].dt.date <= data_a)].copy()
    if filtro_df.empty:
        st.warning("Nessun dato nel range selezionato.")
    else:
        fig = px.line(
            filtro_df,
            x="Data",
            y="Peso",
            markers=True,
            text="Peso",
            title="Variazione Peso Corporeo",
        )
        fig.update_traces(textposition="top center",
                          line_color="#007BFF", marker_size=10)
        fig.update_layout(
            xaxis_title="Data",
            yaxis_title="Peso (kg)",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=40, b=20),
            height=500,
        )
        y_min = float(filtro_df["Peso"].min()) - 2
        y_max = float(filtro_df["Peso"].max()) + 2
        if y_min < y_max:
            fig.update_yaxes(range=[y_min, y_max])

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Aggiornamenti Profilo Corporeo:")
    tabella_df = df.copy()
    tabella_df["Data"] = tabella_df["Data"].dt.date
    edited_df = st.data_editor(
        tabella_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
    )

    if st.button("Conferma Modifiche Tabella"):
        aggiorna_tutto(edited_df, altezza_m)
        st.success("Modifiche salvate con successo.")
        st.rerun()
else:
    st.info("Inizia inserendo i tuoi dati nella barra laterale.")
