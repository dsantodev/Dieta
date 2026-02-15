import pandas as pd
import os

ALTEZZA = 1.76
FILE_DATI = "resources/dieta_progressi.csv"


def calcola_bmi(peso):
    bmi = peso / (ALTEZZA ** 2)
    return round(bmi, 2)


def interpreta_bmi(bmi):
    if bmi < 18.5:
        return "Sottopeso"
    elif 18.5 <= bmi < 25:
        return "Normopeso"
    elif 25 <= bmi < 30:
        return "Sovrappeso"
    else:
        return "Obesità"


def salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo):
    bmi = calcola_bmi(peso)
    nuovi_dati = pd.DataFrame([{
        "Data": data, "Peso": peso, "BMI": bmi, "Polso": polso,
        "Torace": torace, "Vita": vita, "Fianchi": fianchi,
        "Coscia": coscia, "Collo": collo
    }])

    if not os.path.isfile(FILE_DATI):
        nuovi_dati.to_csv(FILE_DATI, index=False)
    else:
        nuovi_dati.to_csv(FILE_DATI, mode='a', header=False, index=False)


def aggiorna_tutto(df):
    """Sovrascrive il CSV con i dati modificati dall'editor."""
    df.to_csv(FILE_DATI, index=False)


def carica_dati():
    if os.path.isfile(FILE_DATI):
        df = pd.read_csv(FILE_DATI)
        # Assicuriamoci che la data sia in formato datetime per i grafici
        df['Data'] = pd.to_datetime(df['Data']).dt.date
        return df
    return None
