import json
from pathlib import Path
import pandas as pd

# =========================
# Percorsi e costanti
# =========================
FILE_DATI = Path("data/dieta_progressi.csv")
FILE_CONFIG = Path("data/config.json")
COLONNE = ["Data", "Peso", "BMI", "Polso",
           "Torace", "Vita", "Fianchi", "Coscia", "Collo"]
FATTORI_ATTIVITA = {
    "Sedentaria": 1.2,
    "Leggera (1-3 allenamenti/settimana)": 1.375,
    "Moderata (3-5 allenamenti/settimana)": 1.55,
    "Alta (6-7 allenamenti/settimana)": 1.725,
    "Molto alta (lavoro fisico + allenamento)": 1.9,
}


# =========================
# Config utente (JSON)
# =========================
def normalizza_config(config: dict) -> tuple[dict, bool]:
    """
    Normalizza il config in modo retro-compatibile.

    - Nuovo schema: obiettivo + kg_settimana
    - Vecchio schema: perdita_kg_settimana
    """
    changed = False

    if "obiettivo" not in config:
        config["obiettivo"] = "perdere"
        changed = True

    if "kg_settimana" not in config:
        if "perdita_kg_settimana" in config:
            config["kg_settimana"] = float(
                config.get("perdita_kg_settimana", 0.5))
        else:
            config["kg_settimana"] = 0.5
        changed = True

    config["obiettivo"] = str(config.get(
        "obiettivo", "perdere")).strip().lower()
    if config["obiettivo"] not in {"perdere", "aumentare"}:
        config["obiettivo"] = "perdere"
        changed = True

    try:
        config["kg_settimana"] = float(config.get("kg_settimana", 0.5))
    except (TypeError, ValueError):
        config["kg_settimana"] = 0.5
        changed = True

    if config["kg_settimana"] <= 0:
        config["kg_settimana"] = 0.5
        changed = True

    # Tema UI (dark/light + palette)
    temi_validi = {
        "win_dark",
        "yellow_dark",
        "violet_dark",
        "emerald_dark",
        "sunset_dark",
    }
    if "tema" not in config:
        config["tema"] = "win_dark"
        changed = True

    config["tema"] = str(config.get("tema", "win_dark")).strip().lower()
    # Migrazione: vecchio tema "win_light" -> nuovo tema "yellow_dark"
    if config["tema"] == "win_light":
        config["tema"] = "yellow_dark"
        changed = True
    if config["tema"] not in temi_validi:
        config["tema"] = "win_dark"
        changed = True

    return config, changed


def salva_config(config: dict) -> None:
    # Salva il profilo utente (nome, altezza, ecc.) in formato JSON.
    with FILE_CONFIG.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def carica_config() -> dict | None:
    # Se non esiste config, l'app mostrerà il setup iniziale.
    if not FILE_CONFIG.is_file():
        return None

    with FILE_CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)


# =========================
# UI (temi + piccoli helper)
# =========================
# Nota: qui NON importiamo Streamlit. La UI usa queste funzioni per:
# - ottenere la lista temi/etichette
# - generare CSS (stringa) da applicare via st.markdown(..., unsafe_allow_html=True)
# - uniformare la logica di alcune scelte (tabs, metric delta, ecc.)

TEMA_LABEL_TO_KEY = {
    "Blu Notte": "win_dark",
    "Giallo su Nero": "yellow_dark",
    "Colorato Viola": "violet_dark",
    "Colorato Verde": "emerald_dark",
    "Colorato Tramonto": "sunset_dark",
}
TEMA_KEY_TO_LABEL = {v: k for k, v in TEMA_LABEL_TO_KEY.items()}

TEMI = {
    "win_dark": {
        "mode": "dark",
        "bg0": "#0b1220",
        "bg1": "#070a12",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_border_strong": "rgba(255, 255, 255, 0.22)",
        "text0": "#e5e7eb",
        "text1": "rgba(229, 231, 235, 0.78)",
        "accent": "#3b82f6",
        "accent2": "#22c55e",
        "warn": "#f59e0b",
        "bad": "#ef4444",
        "shadow": "0 10px 30px rgba(0,0,0,.35)",
        "plotly_template": "plotly_dark",
        "colorway": [
            "#3b82f6",
            "#22c55e",
            "#a855f7",
            "#f59e0b",
            "#ef4444",
            "#38bdf8",
            "#f472b6",
            "#eab308",
        ],
    },
    "yellow_dark": {
        "mode": "dark",
        "bg0": "#070707",
        "bg1": "#000000",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_border_strong": "rgba(255, 255, 255, 0.22)",
        "text0": "#f9fafb",
        "text1": "rgba(249, 250, 251, 0.78)",
        "accent": "#facc15",  # yellow-400
        "accent2": "#f97316",  # orange-500 (secondario)
        "warn": "#f59e0b",
        "bad": "#ef4444",
        "shadow": "0 10px 30px rgba(0,0,0,.40)",
        "plotly_template": "plotly_dark",
        "colorway": [
            "#facc15",
            "#f97316",
            "#22c55e",
            "#38bdf8",
            "#a855f7",
            "#ef4444",
            "#eab308",
            "#60a5fa",
        ],
    },
    "violet_dark": {
        "mode": "dark",
        "bg0": "#0b1020",
        "bg1": "#070916",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_border_strong": "rgba(255, 255, 255, 0.22)",
        "text0": "#e5e7eb",
        "text1": "rgba(229, 231, 235, 0.78)",
        "accent": "#a855f7",
        "accent2": "#38bdf8",
        "warn": "#f59e0b",
        "bad": "#ef4444",
        "shadow": "0 10px 30px rgba(0,0,0,.35)",
        "plotly_template": "plotly_dark",
        "colorway": [
            "#a855f7",
            "#38bdf8",
            "#22c55e",
            "#f59e0b",
            "#ef4444",
            "#60a5fa",
            "#f472b6",
            "#eab308",
        ],
    },
    "emerald_dark": {
        "mode": "dark",
        "bg0": "#071a16",
        "bg1": "#05110f",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_border_strong": "rgba(255, 255, 255, 0.22)",
        "text0": "#e5e7eb",
        "text1": "rgba(229, 231, 235, 0.78)",
        "accent": "#22c55e",
        "accent2": "#14b8a6",
        "warn": "#f59e0b",
        "bad": "#ef4444",
        "shadow": "0 10px 30px rgba(0,0,0,.35)",
        "plotly_template": "plotly_dark",
        "colorway": [
            "#22c55e",
            "#14b8a6",
            "#38bdf8",
            "#a855f7",
            "#f59e0b",
            "#ef4444",
            "#eab308",
            "#60a5fa",
        ],
    },
    "sunset_dark": {
        "mode": "dark",
        "bg0": "#1b1020",
        "bg1": "#0e0a12",
        "card_bg": "rgba(255, 255, 255, 0.06)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "card_border_strong": "rgba(255, 255, 255, 0.22)",
        "text0": "#e5e7eb",
        "text1": "rgba(229, 231, 235, 0.78)",
        "accent": "#f97316",
        "accent2": "#ec4899",
        "warn": "#eab308",
        "bad": "#ef4444",
        "shadow": "0 10px 30px rgba(0,0,0,.35)",
        "plotly_template": "plotly_dark",
        "colorway": [
            "#f97316",
            "#ec4899",
            "#a855f7",
            "#38bdf8",
            "#22c55e",
            "#eab308",
            "#ef4444",
            "#60a5fa",
        ],
    },
}


def indice_opzione(opzioni: list, valore, fallback_index: int = 0) -> int:
    """
    Ritorna l'indice di `valore` dentro `opzioni` oppure `fallback_index`.

    Utile per selectbox/radio quando il config contiene un valore non più valido.
    """
    if valore in opzioni:
        return opzioni.index(valore)
    return fallback_index


def delta_color_for_obiettivo(obiettivo: str) -> str:
    """
    Colore delta Streamlit:
    - Obiettivo "perdere": un delta negativo è "good" => inverse
    - Obiettivo "aumentare": un delta positivo è "good" => normal
    """
    obiettivo_norm = (obiettivo or "").strip().lower()
    return "inverse" if obiettivo_norm == "perdere" else "normal"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    c = (hex_color or "").strip().lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    r = int(c[0:2], 16)
    g = int(c[2:4], 16)
    b = int(c[4:6], 16)
    return r, g, b


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    return f"rgba({r},{g},{b},{alpha})"


def normalizza_tema_key(tema_key: str | None) -> str:
    """
    Normalizza la key del tema (compat con versioni vecchie).
    """
    key = str(tema_key or "win_dark").strip().lower()
    if key == "win_light":
        # vecchio nome: ora è "yellow_dark"
        key = "yellow_dark"
    if key not in TEMI:
        key = "win_dark"
    return key


def tema_assets(tema_key: str | None) -> dict:
    """
    Prepara tutto ciò che serve alla UI per applicare il tema.

    Ritorna un dict con:
    - tema_key: key normalizzata
    - tema: dict tema
    - css: stringa <style>...</style>
    - plotly_template: template Plotly
    - plotly_colorway: lista colori Plotly
    """
    key = normalizza_tema_key(tema_key)
    tema = TEMI[key]

    # Colori "soft" per gradienti: moduliamo l'alpha in base al mode.
    accent_soft = _hex_to_rgba(
        tema["accent"], 0.20 if tema["mode"] == "dark" else 0.12)
    accent2_soft = _hex_to_rgba(
        tema["accent2"], 0.14 if tema["mode"] == "dark" else 0.10)
    accent_sidebar = _hex_to_rgba(
        tema["accent"], 0.18 if tema["mode"] == "dark" else 0.10)

    # Piccoli dettagli che cambiano in base al mode (se in futuro aggiungiamo un tema light).
    sidebar_border = "rgba(17,24,39,0.12)" if tema["mode"] == "light" else "rgba(255,255,255,.10)"
    pill_border = "rgba(17,24,39,0.12)" if tema["mode"] == "light" else "rgba(255,255,255,.14)"
    pill_bg = "rgba(255,255,255,.55)" if tema["mode"] == "light" else "rgba(0,0,0,.18)"
    primary_border = "rgba(17,24,39,0.10)" if tema["mode"] == "light" else "rgba(255,255,255,.18)"

    primary_bg = (
        f"linear-gradient(135deg, {_hex_to_rgba(tema['accent'], 0.95)}, {_hex_to_rgba(tema['accent2'], 0.70)})"
        if tema["mode"] == "dark"
        else tema["accent"]
    )
    button_bg = "rgba(17,24,39,.06)" if tema["mode"] == "light" else "rgba(255,255,255,.06)"
    button_bg_hover = "rgba(17,24,39,.10)" if tema["mode"] == "light" else "rgba(255,255,255,.10)"
    button_border = "rgba(17,24,39,.16)" if tema["mode"] == "light" else "rgba(255,255,255,.18)"
    button_border_hover = "rgba(17,24,39,.22)" if tema["mode"] == "light" else "rgba(255,255,255,.28)"

    # Tabs: underline semplice e pulito (niente bordo visibile)
    tab_underline = "#ff4b4b"

    css = f"""
    <style>
    :root {{
        --app-bg-0: {tema['bg0']};
        --app-bg-1: {tema['bg1']};
        --card-bg: {tema['card_bg']};
        --card-border: {tema['card_border']};
        --card-border-strong: {tema['card_border_strong']};
        --text-0: {tema['text0']};
        --text-1: {tema['text1']};
        --accent: {tema['accent']};
        --accent-2: {tema['accent2']};
        --warn: {tema['warn']};
        --bad: {tema['bad']};
        --shadow: {tema['shadow']};
        --radius-card: 10px;
        --radius-input: 4px;
        --radius-tab: 2px;
        --tab-underline: {tab_underline};
    }}

    .stApp {{
        background:
            radial-gradient(1200px 700px at 20% 0%, {accent_soft}, transparent 60%),
            radial-gradient(900px 600px at 90% 10%, {accent2_soft}, transparent 55%),
            linear-gradient(180deg, var(--app-bg-0), var(--app-bg-1));
        color: var(--text-0);
    }}

    h1, h2, h3 {{ letter-spacing: .2px; }}
    h1 {{ text-shadow: 0 2px 18px rgba(0,0,0,.20); }}

    section[data-testid="stSidebar"] {{
        background:
            radial-gradient(800px 500px at 20% 10%, {accent_sidebar}, transparent 55%),
            linear-gradient(180deg, rgba(255,255,255,.04), rgba(255,255,255,.02));
        border-right: 1px solid {sidebar_border};
    }}

    [data-testid="stMetric"] {{
        background-color: var(--card-bg);
        border: 1px solid var(--card-border);
        padding: 15px;
        border-radius: var(--radius-card);
        box-shadow: var(--shadow);
    }}

    [data-testid="stMetricDelta"] > div {{
        display: inline-flex;
        align-items: center;
        gap: .35rem;
        padding: .18rem .55rem;
        border-radius: 999px;
        border: 1px solid {pill_border};
        background: {pill_bg};
        font-weight: 650;
    }}

    /* Tabs: underline pulito, niente bordo "bianco" */
    [data-testid="stTabs"] button {{
        border-radius: var(--radius-tab) var(--radius-tab) 0 0 !important;
        border: 0 !important;
        border-bottom: 2px solid transparent !important;
        background: transparent !important;
        color: var(--text-1) !important;
        box-shadow: none !important;
    }}
    [data-testid="stTabs"] button[aria-selected="true"] {{
        color: var(--text-0) !important;
        border-bottom-color: var(--tab-underline) !important;
    }}
    [data-testid="stTabs"] button:focus-visible {{
        outline: none !important;
        box-shadow: none !important;
    }}

    /* Number input (+/-): niente semicerchi/pill */
    [data-testid="stNumberInput"] input {{
        border-radius: var(--radius-input) !important;
    }}
    [data-testid="stNumberInput"] button {{
        border-radius: var(--radius-input) !important;
    }}
    [data-testid="stNumberInput"] div[data-baseweb="input"] {{
        border-radius: var(--radius-input) !important;
    }}

    /* Bottoni: rendili visivamente cliccabili anche quando non sono "primary" */
    div[data-testid="stButton"] button,
    div[data-testid="stFormSubmitButton"] button {{
        cursor: pointer !important;
        border-radius: 10px !important;
        padding: .55rem .95rem !important;
        border: 1px solid {button_border} !important;
        background: {button_bg} !important;
        font-weight: 750 !important;
        transition: background .15s ease, border-color .15s ease, transform .04s ease;
    }}
    div[data-testid="stButton"] button:hover,
    div[data-testid="stFormSubmitButton"] button:hover {{
        background: {button_bg_hover} !important;
        border-color: {button_border_hover} !important;
    }}
    div[data-testid="stButton"] button:active,
    div[data-testid="stFormSubmitButton"] button:active {{
        transform: translateY(1px);
    }}

    button[kind="primary"] {{
        background: {primary_bg} !important;
        border: 1px solid {primary_border} !important;
        box-shadow: 0 10px 26px rgba(0,0,0,.15);
    }}
    button[kind="primary"]:hover {{ filter: brightness(1.03); }}
    </style>
    """

    return {
        "tema_key": key,
        "tema": tema,
        "css": css,
        "plotly_template": tema["plotly_template"],
        "plotly_colorway": tema["colorway"],
    }


# =========================
# Calcoli (BMI e fabbisogno)
# =========================
def calcola_bmi(peso: float, altezza_m: float) -> float:
    # BMI = peso / altezza^2 (altezza in metri).
    bmi = float(peso) / (float(altezza_m) ** 2)
    return round(bmi, 2)


def interpreta_bmi(bmi: float) -> str:
    if bmi < 18.5:
        return "Sottopeso"
    if bmi < 25:
        return "Normopeso"
    if bmi < 30:
        return "Sovrappeso"
    return "Obesità"


def calcola_fabbisogno(
    peso: float,
    altezza_m: float,
    eta: int,
    sesso: str,
    attivita: str,
    perdita_kg_settimana: float | None = None,
    *,
    obiettivo: str = "perdere",
    kg_settimana: float | None = None,
) -> dict:
    """
    Calcola:
    - BMR (Mifflin-St Jeor)
    - TDEE (BMR * fattore attività)
    - Delta kcal giornaliero in base al target kg/settimana (deficit o surplus)
    - Calorie target giornaliere (cut o bulk)
    """
    altezza_cm = float(altezza_m) * 100
    base = 10 * float(peso) + 6.25 * altezza_cm - 5 * int(eta)
    s = -161 if sesso == "Donna" else 5
    bmr = base + s

    fattore = FATTORI_ATTIVITA.get(attivita, 1.2)
    tdee = bmr * fattore

    # 1 kg di grasso ~ 7700 kcal.
    if kg_settimana is None:
        kg_settimana = float(
            perdita_kg_settimana) if perdita_kg_settimana is not None else 0.5

    # Compat: se arriva un valore negativo (vecchia logica), lo interpreto come aumento peso.
    if float(kg_settimana) < 0:
        obiettivo = "aumentare"
        kg_settimana = abs(float(kg_settimana))

    obiettivo_norm = str(obiettivo or "perdere").strip().lower()
    if obiettivo_norm not in {"perdere", "aumentare"}:
        obiettivo_norm = "perdere"

    delta_kcal_giorno = (float(kg_settimana) * 7700) / 7
    calorie_target = tdee - \
        delta_kcal_giorno if obiettivo_norm == "perdere" else tdee + delta_kcal_giorno

    # Limite prudenziale per evitare target troppo bassi.
    calorie_minime = bmr * 0.8
    calorie_target = max(calorie_target, calorie_minime)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "delta_giornaliero": round(delta_kcal_giorno),
        "obiettivo": obiettivo_norm,
        "kg_settimana": float(kg_settimana),
        "calorie_target": round(calorie_target),
        "fattore_attivita": fattore,
    }


# =========================
# Dati (CSV) + normalizzazione
# =========================
def last_or_default(df: pd.DataFrame | None, colonna: str, fallback: float) -> float:
    # Usato per precompilare i campi con l'ultima misura disponibile.
    if df is None or df.empty or colonna not in df.columns:
        return fallback
    valore = df[colonna].iloc[-1]
    if pd.isna(valore):
        return fallback
    return float(valore)


def prepara_storico_per_ui(df: pd.DataFrame | None) -> pd.DataFrame | None:
    """
    Prepara il dataframe per l'uso lato UI:
    - Data in datetime
    - drop righe senza Data
    - ordine cronologico
    """
    if df is None or df.empty:
        return None

    out = df.copy()
    out["Data"] = pd.to_datetime(out["Data"], errors="coerce")
    out = out.dropna(subset=["Data"]).sort_values(
        by="Data").reset_index(drop=True)
    return out


def _normalizza_dataframe(df: pd.DataFrame, altezza_m: float) -> pd.DataFrame:
    # Garanzia schema: se mancano colonne, le creo.
    for col in COLONNE:
        if col not in df.columns:
            df[col] = pd.NA

    # Conversioni sicure per evitare problemi da modifiche manuali in tabella.
    df = df[COLONNE].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")
    for col in ["Polso", "Torace", "Vita", "Fianchi", "Coscia", "Collo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Data", "Peso"])
    # Il BMI viene sempre ricalcolato lato engine, mai fidarsi del valore in input.
    df["BMI"] = df["Peso"].apply(lambda p: calcola_bmi(p, altezza_m))
    # Se la stessa data è inserita più volte, tengo l'ultima versione.
    df = df.sort_values(by="Data").drop_duplicates(
        subset=["Data"], keep="last")
    df["Data"] = df["Data"].dt.date
    return df.reset_index(drop=True)


def carica_dati() -> pd.DataFrame | None:
    # Ritorna None se non c'è ancora storico.
    if not FILE_DATI.is_file():
        return None

    df = pd.read_csv(FILE_DATI)
    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    return df


def salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo, altezza_m: float):
    # Salvataggio "append logico": unisco al vecchio storico e poi ripulisco tutto.
    nuovi_dati = pd.DataFrame([{
        "Data": data,
        "Peso": peso,
        "Polso": polso,
        "Torace": torace,
        "Vita": vita,
        "Fianchi": fianchi,
        "Coscia": coscia,
        "Collo": collo,
    }])

    esistente = carica_dati()
    if esistente is not None:
        combinato = pd.concat([esistente, nuovi_dati], ignore_index=True)
    else:
        combinato = nuovi_dati

    pulito = _normalizza_dataframe(combinato, altezza_m)
    pulito.to_csv(FILE_DATI, index=False)


def aggiorna_tutto(df: pd.DataFrame, altezza_m: float):
    """Sovrascrive il CSV con i dati modificati dall'editor, ricalcolando il BMI."""
    # Usato dal data_editor: normalizza e riscrive l'intero storico.
    pulito = _normalizza_dataframe(df.copy(), altezza_m)
    pulito.to_csv(FILE_DATI, index=False)
