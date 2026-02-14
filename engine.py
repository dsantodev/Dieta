import pandas as pd
import os

# Costanti
ALTEZZA = 1.76
FILE_DATI = "resources/dieta_progressi.csv"


def calcola_bmi(peso):
    """Calcola il Body Mass Index."""
    bmi = peso / (ALTEZZA ** 2)
    return round(bmi, 2)


def interpreta_bmi(bmi):
    """Restituisce la categoria del BMI."""
    if bmi < 18.5:
        return "Sottopeso"
    elif 18.5 <= bmi < 25:
        return "Normopeso"
    elif 25 <= bmi < 30:
        return "Sovrappeso"
    else:
        return "Obesità"


def salva_misurazioni(data, peso, polso, torace, vita, fianchi, coscia, collo):
    """Salva i dati nel file CSV in resources."""
    bmi = calcola_bmi(peso)

    nuovi_dati = {
        "Data": [data],
        "Peso": [peso],
        "BMI": [bmi],
        "Polso": [polso],
        "Torace": [torace],
        "Vita": [vita],
        "Fianchi": [fianchi],
        "Coscia": [coscia],
        "Collo": [collo]
    }

    df_nuovo = pd.DataFrame(nuovi_dati)

    # Se il file non esiste, lo crea con l'intestazione
    if not os.path.isfile(FILE_DATI):
        df_nuovo.to_csv(FILE_DATI, index=False)
    else:
        # Altrimenti aggiunge i dati senza riscrivere l'intestazione
        df_nuovo.to_csv(FILE_DATI, mode='a', header=False, index=False)


def carica_dati():
    """Carica i dati dal CSV se esiste."""
    if os.path.isfile(FILE_DATI):
        return pd.read_csv(FILE_DATI)
    return None
