import json
from pathlib import Path

import pandas as pd

FILE_DATI = Path("dieta_progressi.csv")
FILE_CONFIG = Path("config.json")
COLONNE = ["Data", "Peso", "BMI", "Polso", "Torace", "Vita", "Fianchi", "Coscia", "Collo"]
FATTORI_ATTIVITA = {
    "Sedentaria": 1.2,
    "Leggera (1-3 allenamenti/settimana)": 1.375,
    "Moderata (3-5 allenamenti/settimana)": 1.55,
    "Alta (6-7 allenamenti/settimana)": 1.725,
    "Molto alta (lavoro fisico + allenamento)": 1.9,
}


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
    perdita_kg_settimana: float,
) -> dict:
    """
    Calcola:
    - BMR (Mifflin-St Jeor)
    - TDEE (BMR * fattore attività)
    - Deficit giornaliero in base al target kg/settimana
    - Calorie target giornaliere
    """
    altezza_cm = float(altezza_m) * 100
    base = 10 * float(peso) + 6.25 * altezza_cm - 5 * int(eta)
    s = -161 if sesso == "Donna" else 5
    bmr = base + s

    fattore = FATTORI_ATTIVITA.get(attivita, 1.2)
    tdee = bmr * fattore

    # 1 kg di grasso ~ 7700 kcal.
    deficit_giornaliero = (float(perdita_kg_settimana) * 7700) / 7
    calorie_target = tdee - deficit_giornaliero

    # Limite prudenziale per evitare target troppo bassi.
    calorie_minime = bmr * 0.8
    calorie_target = max(calorie_target, calorie_minime)

    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "deficit_giornaliero": round(deficit_giornaliero),
        "calorie_target": round(calorie_target),
        "fattore_attivita": fattore,
    }


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
    df = df.sort_values(by="Data").drop_duplicates(subset=["Data"], keep="last")
    df["Data"] = df["Data"].dt.date
    return df.reset_index(drop=True)


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


def carica_dati() -> pd.DataFrame | None:
    # Ritorna None se non c'è ancora storico.
    if not FILE_DATI.is_file():
        return None

    df = pd.read_csv(FILE_DATI)
    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    return df
