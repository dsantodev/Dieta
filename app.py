from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st
# import mie funzioni
from engine import (
    FATTORI_ATTIVITA,
    TEMA_KEY_TO_LABEL,
    TEMA_LABEL_TO_KEY,
    aggiorna_tutto,
    calcola_fabbisogno,
    carica_config,
    carica_dati,
    delta_color_for_obiettivo,
    indice_opzione,
    interpreta_bmi,
    last_or_default,
    normalizza_config,
    tema_assets,
    prepara_storico_per_ui,
    salva_config,
    salva_misurazioni,
)

OBIETTIVI_KG_SETTIMANA = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
OBIETTIVO_LABEL_TO_KEY = {
    "Perdere peso": "perdere",
    "Aumentare peso": "aumentare",
}

# =========================
# Streamlit: setup pagina + stile
# =========================
st.set_page_config(page_title="Dieta & Progressi", layout="wide")


# Tema e helper UI sono in `engine.py` (es. `tema_assets`, `indice_opzione`, `delta_color_for_obiettivo`).


# =========================
# Avvio: carico config e dati
# =========================
config = carica_config()
df = carica_dati()

tema = tema_assets((config or {}).get("tema", "win_dark"))
st.markdown(tema["css"], unsafe_allow_html=True)
PLOTLY_TEMPLATE = tema["plotly_template"]
PLOTLY_COLORWAY = tema["plotly_colorway"]

# =========================
# Primo avvio: wizard iniziale (se manca config)
# =========================
if config is None:
    st.title("Setup iniziale Diario Dieta")
    st.info("Compila i dati base. Verrà creato automaticamente il nuovo profilo.")

    with st.form("setup_iniziale"):
        nome = st.text_input("Come ti chiami?", value="")
        eta = st.number_input("Età", min_value=1,
                              max_value=120, value=35, step=1)
        sesso = st.selectbox("Sesso", options=["Uomo", "Donna"], index=0)
        attivita = st.selectbox("Livello attività", options=list(
            FATTORI_ATTIVITA.keys()), index=0)

        obiettivo_label = st.selectbox(
            "Obiettivo",
            options=list(OBIETTIVO_LABEL_TO_KEY.keys()),
            index=0,
        )
        obiettivo = OBIETTIVO_LABEL_TO_KEY[obiettivo_label]
        kg_settimana = st.selectbox(
            "Target (kg/settimana)" if obiettivo == "perdere" else "Target aumento (kg/settimana)",
            options=OBIETTIVI_KG_SETTIMANA,
            index=indice_opzione(OBIETTIVI_KG_SETTIMANA, 0.5, 1),
            format_func=lambda x: f"{x} kg/settimana",
        )

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
        # Normalizzo i dati utente e converto altezza in metri per il calcolo BMI.
        nome_pulito = nome.strip() or "Utente"
        config = {
            "nome": nome_pulito,
            "eta": int(eta),
            "sesso": sesso,
            "attivita": attivita,
            "obiettivo": obiettivo,
            "kg_settimana": float(kg_settimana),
            "altezza_m": round(float(altezza_cm) / 100, 2),
            "peso_iniziale": float(peso_iniziale),
            "tema": "win_dark",
        }
        salva_config(config)

        # Opzionale: crea già la prima riga nello storico per evitare file vuoto.
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

config, config_changed = normalizza_config(config)
if config_changed:
    salva_config(config)


# compiliamo le variabili in base agli inserimenti o al file esistente
nome_utente = config.get("nome", "Utente")
altezza_m = float(config.get("altezza_m", 1.76))
eta = int(config.get("eta", 35))
sesso = config.get("sesso", "Uomo")
attivita = config.get("attivita", "Sedentaria")
obiettivo = str(config.get("obiettivo", "perdere"))
kg_settimana = float(config.get("kg_settimana", 0.5))

# Pulizia base: data valida + ordinamento cronologico (solo se c'è storico).
df = prepara_storico_per_ui(df)


# =========================
# Sidebar: navigazione + input (Diario / Impostazioni)
# =========================
with st.sidebar:
    st.markdown(f"## 🎭 DIETA {nome_utente}", text_alignment='center')
    st.caption(f"> {nome_utente} - {eta} anni - {altezza_m:.2f} m")

    if df is not None and not df.empty and "Peso" in df.columns:
        try:
            ultimo_peso_sidebar = float(df["Peso"].iloc[-1])
            prev_peso_sidebar = float(
                df["Peso"].iloc[-2]) if len(df) > 1 else ultimo_peso_sidebar
            delta_peso_sidebar = float(ultimo_peso_sidebar - prev_peso_sidebar)
            st.metric(
                "⚖️ Peso",
                f"{ultimo_peso_sidebar:.1f} kg",
                f"{delta_peso_sidebar:+.2f} kg",
                delta_color=delta_color_for_obiettivo(obiettivo),
            )
        except Exception:
            pass

    st.divider()
    sezione = st.radio(
        "Navigazione",
        options=["📚 Diario", "⚙️ Impostazioni"],
        index=0,
        label_visibility="collapsed",
        key="nav_sezione",
    )

submit = False
if sezione == "📚 Diario":
    st.title(f"Dieta e Misure di {nome_utente}")

    with st.sidebar:
        tab_inserisci, tab_obiettivo = st.tabs(["Inserisci", "Obiettivo"])

        with tab_inserisci:
            st.markdown("**Misurazioni**")
            with st.form("form_misure", clear_on_submit=False):
                data = st.date_input("Data", value=date.today())
                peso = st.number_input(
                    "Peso (kg)",
                    min_value=40.0,
                    max_value=300.0,
                    value=last_or_default(df, "Peso", float(
                        config.get("peso_iniziale", 100.0))),
                    step=0.1,
                )

                st.markdown("---")
                col_a, col_b = st.columns(2)
                with col_a:
                    vita = st.number_input(
                        "Vita (cm)",
                        min_value=30.0,
                        max_value=250.0,
                        value=last_or_default(df, "Vita", 142.0),
                        step=0.1,
                    )
                    torace = st.number_input(
                        "Torace (cm)",
                        min_value=30.0,
                        max_value=250.0,
                        value=last_or_default(df, "Torace", 135.0),
                        step=0.1,
                    )
                    collo = st.number_input(
                        "Collo (cm)",
                        min_value=10.0,
                        max_value=80.0,
                        value=last_or_default(df, "Collo", 46.0),
                        step=0.1,
                    )
                with col_b:
                    fianchi = st.number_input(
                        "Fianchi (cm)",
                        min_value=30.0,
                        max_value=250.0,
                        value=last_or_default(df, "Fianchi", 145.0),
                        step=0.1,
                    )
                    coscia = st.number_input(
                        "Coscia (cm)",
                        min_value=20.0,
                        max_value=150.0,
                        value=last_or_default(df, "Coscia", 74.0),
                        step=0.1,
                    )
                    polso = st.number_input(
                        "Polso (cm)",
                        min_value=5.0,
                        max_value=40.0,
                        value=last_or_default(df, "Polso", 21.0),
                        step=0.1,
                        help="Misura il polso subito sopra l'osso della mano",
                    )

                submit = st.form_submit_button(
                    "Salva Progressi", use_container_width=True)

        with tab_obiettivo:
            st.markdown("**Calorie & target**")
            sesso_ui = st.selectbox(
                "Sesso",
                options=["Uomo", "Donna"],
                index=indice_opzione(["Uomo", "Donna"], sesso, 0),
                key="goal_sesso_sidebar",
            )
            attivita_ui = st.selectbox(
                "Attività",
                options=list(FATTORI_ATTIVITA.keys()),
                index=indice_opzione(
                    list(FATTORI_ATTIVITA.keys()), attivita, 0),
                key="goal_attivita_sidebar",
            )

            obiettivo_labels = list(OBIETTIVO_LABEL_TO_KEY.keys())
            obiettivo_corrente_label = next(
                (lbl for lbl, key in OBIETTIVO_LABEL_TO_KEY.items() if key == obiettivo),
                obiettivo_labels[0],
            )
            obiettivo_ui_label = st.selectbox(
                "Obiettivo",
                options=obiettivo_labels,
                index=indice_opzione(
                    obiettivo_labels, obiettivo_corrente_label, 0),
                key="goal_obiettivo_sidebar",
            )
            obiettivo_ui = OBIETTIVO_LABEL_TO_KEY[obiettivo_ui_label]
            kg_ui = st.selectbox(
                "Target (kg/settimana)" if obiettivo_ui == "perdere" else "Target aumento (kg/settimana)",
                options=OBIETTIVI_KG_SETTIMANA,
                index=indice_opzione(OBIETTIVI_KG_SETTIMANA, kg_settimana, 1),
                format_func=lambda x: f"{x} kg/settimana",
                key="goal_kg_sidebar",
            )

            st.caption(
                "Suggerimento: usa 0.25–0.75 per un approccio sostenibile.")
            if st.button("Salva Obiettivo", use_container_width=True):
                config["sesso"] = sesso_ui
                config["attivita"] = attivita_ui
                config["obiettivo"] = obiettivo_ui
                config["kg_settimana"] = float(kg_ui)
                salva_config(config)
                st.success("Obiettivo aggiornato.")
                st.rerun()

else:
    st.title("Impostazioni utente")
    st.caption(
        "Modifica i dati del profilo. Ricorda di salvare le modifiche.")

    st.sidebar.caption(
        "Nella pagina a destra, seleziona le tab per modificare profilo, target e aspetto.")
    profilo_tab, target_tab, aspetto_tab = st.tabs(
        ["Profilo", "Target", "Tema"])

    with profilo_tab:
        with st.form("form_impostazioni_profilo"):
            nome_ui = st.text_input(
                "Nome", value=str(config.get("nome", "Utente")))
            eta_ui = st.number_input(
                "Età", min_value=1, max_value=120, value=int(config.get("eta", 35)), step=1)
            altezza_cm_ui = st.number_input(
                "Altezza (cm)",
                min_value=120.0,
                max_value=230.0,
                value=float(config.get("altezza_m", 1.76)) * 100,
                step=0.1,
            )
            peso_iniziale_ui = st.number_input(
                "Peso iniziale (kg)",
                min_value=40.0,
                max_value=300.0,
                value=float(config.get("peso_iniziale", 100.0)),
                step=0.1,
            )
            salva_profilo = st.form_submit_button(
                "Salva Profilo", use_container_width=True)

        if salva_profilo:
            nuova_altezza_m = round(float(altezza_cm_ui) / 100, 2)
            altezza_cambiata = abs(
                nuova_altezza_m - float(config.get("altezza_m", nuova_altezza_m))) > 1e-6

            config["nome"] = (nome_ui or "Utente").strip() or "Utente"
            config["eta"] = int(eta_ui)
            config["altezza_m"] = nuova_altezza_m
            config["peso_iniziale"] = float(peso_iniziale_ui)
            salva_config(config)

            if altezza_cambiata:
                df_corrente = carica_dati()
                if df_corrente is not None and not df_corrente.empty:
                    aggiorna_tutto(df_corrente, nuova_altezza_m)

            st.success("Profilo salvato.")
            st.rerun()

    with target_tab:
        st.markdown("### Target calorico")
        with st.form("form_impostazioni_target"):
            sesso_ui = st.selectbox(
                "Sesso",
                options=["Uomo", "Donna"],
                index=indice_opzione(["Uomo", "Donna"], sesso, 0),
                key="goal_sesso_settings",
            )
            attivita_ui = st.selectbox(
                "Attività",
                options=list(FATTORI_ATTIVITA.keys()),
                index=indice_opzione(
                    list(FATTORI_ATTIVITA.keys()), attivita, 0),
                key="goal_attivita_settings",
            )

            obiettivo_labels = list(OBIETTIVO_LABEL_TO_KEY.keys())
            obiettivo_corrente_label = next(
                (lbl for lbl, key in OBIETTIVO_LABEL_TO_KEY.items() if key == obiettivo),
                obiettivo_labels[0],
            )
            obiettivo_ui_label = st.selectbox(
                "Obiettivo",
                options=obiettivo_labels,
                index=indice_opzione(
                    obiettivo_labels, obiettivo_corrente_label, 0),
                key="goal_obiettivo_settings",
            )
            obiettivo_ui = OBIETTIVO_LABEL_TO_KEY[obiettivo_ui_label]
            kg_ui = st.selectbox(
                "Target (kg/settimana)" if obiettivo_ui == "perdere" else "Target aumento (kg/settimana)",
                options=OBIETTIVI_KG_SETTIMANA,
                index=indice_opzione(OBIETTIVI_KG_SETTIMANA, kg_settimana, 1),
                format_func=lambda x: f"{x} kg/settimana",
                key="goal_kg_settings",
            )
            sesso_save = st.form_submit_button(
                "Salva Target", use_container_width=True)

        if sesso_save:
            config["sesso"] = sesso_ui
            config["attivita"] = attivita_ui
            config["obiettivo"] = obiettivo_ui
            config["kg_settimana"] = float(kg_ui)
            salva_config(config)
            st.success("Target salvato.")
            st.rerun()

    with aspetto_tab:
        st.markdown("### Aspetto Tema")
        with st.form("form_impostazioni_aspetto"):
            tema_labels = list(TEMA_LABEL_TO_KEY.keys())
            tema_corrente_key = str(config.get(
                "tema", "win_dark")).strip().lower()
            if tema_corrente_key == "win_light":
                tema_corrente_key = "yellow_dark"
            tema_corrente_label = TEMA_KEY_TO_LABEL.get(
                tema_corrente_key, tema_labels[0])
            tema_ui_label = st.selectbox(
                "Tema",
                options=tema_labels,
                index=indice_opzione(tema_labels, tema_corrente_label, 0),
                help="Scegli una palette. Le opzioni 'Windows' sono più neutre; le 'Colorato' danno più carattere.",
            )
            salva_tema = st.form_submit_button(
                "Salva Tema", use_container_width=True)

        if salva_tema:
            config["tema"] = TEMA_LABEL_TO_KEY.get(tema_ui_label, "win_dark")
            salva_config(config)
            st.success("Tema salvato.")
            st.rerun()

    st.stop()

if submit:
    # Tutte le misure passano da engine, che normalizza e ricalcola BMI.
    salva_misurazioni(data, peso, polso, torace, vita,
                      fianchi, coscia, collo, altezza_m)
    st.success("Dati salvati con successo.")
    st.rerun()

df = carica_dati()
df = prepara_storico_per_ui(df)

if df is not None:
    # Ricarico dal file dopo eventuali salvataggi per vedere sempre dati reali.
    ultimo_peso = float(df["Peso"].iloc[-1])
    precedente_peso = float(
        df["Peso"].iloc[-2]) if len(df) > 1 else ultimo_peso
    delta_peso = round(ultimo_peso - precedente_peso, 2)

    fabbisogno = calcola_fabbisogno(
        peso=ultimo_peso,
        altezza_m=altezza_m,
        eta=eta,
        sesso=config.get("sesso", "Uomo"),
        attivita=config.get("attivita", "Sedentaria"),
        obiettivo=str(config.get("obiettivo", "perdere")),
        kg_settimana=float(config.get("kg_settimana", 0.5)),
    )

    col1, col2, col3 = st.columns(3)
    delta_color = delta_color_for_obiettivo(fabbisogno.get("obiettivo"))
    col1.metric("⚖️ Peso Attuale", f"{ultimo_peso:.1f} kg",
                delta=f"{delta_peso:+.2f} kg", delta_color=delta_color)
    col2.metric("📏 BMI", df["BMI"].iloc[-1])
    col3.metric("🏷️ Stato", interpreta_bmi(float(df["BMI"].iloc[-1])))

    st.divider()

    st.subheader("Fabbisogno e Target Calorico")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "🔥 BMR",
        f"{fabbisogno['bmr']} kcal",
        help="Metabolismo basale: calorie stimate che il corpo consuma a riposo completo.",
    )
    k2.metric(
        "⚡ TDEE",
        f"{fabbisogno['tdee']} kcal",
        help="Fabbisogno giornaliero totale: BMR moltiplicato per il livello di attività.",
    )
    tipo_delta = "Deficit" if fabbisogno.get(
        "obiettivo") == "perdere" else "Surplus"
    tipo_delta = ("⬇️ " if fabbisogno.get("obiettivo")
                  == "perdere" else "⬆️ ") + tipo_delta
    valore_delta = f"-{fabbisogno['delta_giornaliero']} kcal" if fabbisogno.get(
        "obiettivo") == "perdere" else f"+{fabbisogno['delta_giornaliero']} kcal"
    k3.metric(
        tipo_delta,
        valore_delta,
        help="Differenza calorica giornaliera teorica per raggiungere il target (deficit per perdere peso, surplus per aumentare peso).",
    )
    k4.metric(
        "🎯 Calorie Target",
        f"{fabbisogno['calorie_target']} kcal",
        help="Calorie giornaliere consigliate dopo il deficit, con limite minimo prudenziale.",
    )

    st.caption(
        f"Profilo: {config.get('sesso', 'Uomo')}, attività: {config.get('attivita', 'Sedentaria')}, "
        f"obiettivo: {config.get('obiettivo', 'perdere')} {float(config.get('kg_settimana', 0.5))} kg/settimana"
    )

    st.divider()

    st.subheader("Visualizza il grafico in base ad un periodo")
    # Filtro intervallo date direttamente da UI per leggere meglio i trend.
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
        metriche_opzioni = [
            c for c in ["Peso", "Vita", "Fianchi", "Torace", "Coscia", "Polso", "Collo", "BMI"]
            if c in filtro_df.columns
        ]
        default_metriche = [c for c in [
            "Peso", "Vita", "Fianchi"] if c in metriche_opzioni]
        if not default_metriche and metriche_opzioni:
            default_metriche = [metriche_opzioni[0]]

        metriche = st.multiselect(
            "Misure da sovrapporre",
            options=metriche_opzioni,
            default=default_metriche,
        )
        normalizza = st.toggle("Confronto trend (indice 100)", value=True)

        if not metriche:
            st.warning("Seleziona almeno una misura da visualizzare.")
        else:
            plot_df = filtro_df.sort_values(by="Data").copy()
            for col in metriche:
                plot_df[col] = pd.to_numeric(plot_df[col], errors="coerce")
            raw_df = plot_df.copy()

            if normalizza:
                for col in metriche:
                    serie = plot_df[col].dropna()
                    if serie.empty:
                        continue
                    base = float(serie.iloc[0])
                    if base != 0:
                        plot_df[col] = (plot_df[col] / base) * 100

            long_df = plot_df.melt(
                id_vars=["Data"],
                value_vars=metriche,
                var_name="Misura",
                value_name="Valore",
            ).dropna(subset=["Valore"])

            fig = px.line(
                long_df,
                x="Data",
                y="Valore",
                color="Misura",
                markers=True,
                title="Andamento misure Biometriche",
            )
            fig.update_layout(
                template=PLOTLY_TEMPLATE,
                colorway=PLOTLY_COLORWAY,
                xaxis_title="Data",
                yaxis_title="Indice (prima data = 100)" if normalizza else "Valore",
                hovermode="x unified",
                margin=dict(l=20, r=20, t=40, b=20),
                height=520,
            )
            st.plotly_chart(fig, use_container_width=True)

            # Tabella statistiche nel range selezionato
            righe = []
            for col in metriche:
                serie = pd.to_numeric(raw_df[col], errors="coerce").dropna()
                if serie.empty:
                    continue
                righe.append({
                    "Misura": col,
                    "Primo": float(serie.iloc[0]),
                    "Ultimo": float(serie.iloc[-1]),
                    "Delta": float(serie.iloc[-1] - serie.iloc[0]),
                    "Min": float(serie.min()),
                    "Max": float(serie.max()),
                    "Media": float(serie.mean()),
                })

            if righe:
                st.markdown("**Statistiche Target**",
                            help="La tabella rappresenta le misure selezionate per la sovrapposizione del grafico")
                stats_df = pd.DataFrame(righe).set_index("Misura")
                st.dataframe(stats_df.round(2), use_container_width=True)

    st.divider()

    st.subheader("Storico misure",
                 help="La presente tabella, rappresenta l'archivio che per necessità puoi modificare.")
    # L'editor permette correzioni storiche; il salvataggio ricalcola sempre il BMI.
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

    peso_stimato = float(config.get("peso_iniziale", 100.0))
    fabbisogno = calcola_fabbisogno(
        peso=peso_stimato,
        altezza_m=altezza_m,
        eta=eta,
        sesso=config.get("sesso", "Uomo"),
        attivita=config.get("attivita", "Sedentaria"),
        obiettivo=str(config.get("obiettivo", "perdere")),
        kg_settimana=float(config.get("kg_settimana", 0.5)),
    )
    st.subheader("Fabbisogno e Target Calorico")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(
        "🔥 BMR",
        f"{fabbisogno['bmr']} kcal",
        help="Metabolismo basale: calorie stimate che il corpo consuma a riposo completo.",
    )
    k2.metric(
        "⚡ TDEE",
        f"{fabbisogno['tdee']} kcal",
        help="Fabbisogno giornaliero totale: BMR moltiplicato per il livello di attività.",
    )
    tipo_delta = "Deficit" if fabbisogno.get(
        "obiettivo") == "perdere" else "Surplus"
    tipo_delta = ("⬇️ " if fabbisogno.get("obiettivo")
                  == "perdere" else "⬆️ ") + tipo_delta
    valore_delta = f"-{fabbisogno['delta_giornaliero']} kcal" if fabbisogno.get(
        "obiettivo") == "perdere" else f"+{fabbisogno['delta_giornaliero']} kcal"
    k3.metric(
        tipo_delta,
        valore_delta,
        help="Differenza calorica giornaliera teorica per raggiungere il target (deficit per perdere peso, surplus per aumentare peso).",
    )
    k4.metric(
        "🎯 Calorie Target",
        f"{fabbisogno['calorie_target']} kcal",
        help="Calorie giornaliere consigliate dopo il deficit, con limite minimo prudenziale.",
    )
