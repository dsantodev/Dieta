import json
from pathlib import Path

import pandas as pd

FILE_DATI = Path("dieta_progressi.csv")
FILE_CONFIG = Path("config.json")
COLONNE = ["Data", "Peso", "BMI", "Polso", "Torace", "Vita", "Fianchi", "Coscia", "Collo"]


def salva_config(config: dict) -> None:
    with FILE_CONFIG.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def carica_config() -> dict | None:
    if not FILE_CONFIG.is_file():
        return None

    with FILE_CONFIG.open("r", encoding="utf-8") as f:
        return json.load(f)


def calcola_bmi(peso: float, altezza_m: float) -> float:
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


def _normalizza_dataframe(df: pd.DataFrame, altezza_m: float) -> pd.DataFrame:
    for col in COLONNE:
        if col not in df.columns:
            df[col] = pd.NA

    df = df[COLONNE].copy()
    df["Data"] = pd.to_datetime(df["Data"], errors="coerce")
    df["Peso"] = pd.to_numeric(df["Peso"], errors="coerce")
    for col in ["Polso", "Torace", "Vita", "Fianchi", "Coscia", "Collo"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Data", "Peso"])
    df["BMI"] = df["Peso"].apply(lambda p: calcola_bmi(p, altezza_m))
    df = df.sort_values(by="Data").drop_duplicates(subset=["Data"], keep="last")
    df["Data"] = df["Data"].dt.date
    return df.reset_index(drop=True)


def salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo, altezza_m: float):
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
    pulito = _normalizza_dataframe(df.copy(), altezza_m)
    pulito.to_csv(FILE_DATI, index=False)


def carica_dati() -> pd.DataFrame | None:
    if not FILE_DATI.is_file():
        return None

    df = pd.read_csv(FILE_DATI)
    if df.empty:
        return None

    df["Data"] = pd.to_datetime(df["Data"], errors="coerce").dt.date
    return df
