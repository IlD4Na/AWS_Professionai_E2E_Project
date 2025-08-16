import sys
import pandas as pd
import awswrangler as wr
from sklearn.impute import KNNImputer

bronze_path_s3 = "s3://profession-ai-adrian-bronze/bitcoin/"
silver_path_s3 = "s3://profession-ai-adrian-silver/bitcoin/"

# FUNZIONI DI CLEANING E IMPUTING

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
  """Cleans and normalize the dataset.

  This function is tailored  for a dataset with the following 
  columns: `["Date", "Price", "Open", "High", "Low", "Vol.", "Change %"]`.


  Some assumptions on the origin file:
  * `Date` is a string in US format **%m/%d/%Y** (es. "03/25/2025").
  *  Numerical columns could cointain separators like (`,`).
  * `Vol.` it can have suffixes like **K/M/B** (es. "3.39K", "1.2M").
  * `Change %` includes the symbol `%` (es. "2.15%"), which we remove:
    the result is in percentages point (es. 2.15, with no 0.0215).

  Effects:
  - Converts "Date" in "dateime64[ns]"
  - Converts "Price","Open","High","Low" in "float64"
  - Converts "Vol." in full number
  - Converts "Change %" in float (percentages points)
  

  """

  for col in ["Price","Open","High","Low","Vol.","Change %"]:

    if df[col].dtype in ["object","string"]:

      # Tolgo le virgole cosi posso trasformare in float poi
      df[col] = df[col].str.replace(",", "", regex=False)
  
      # Tolgo K e %
      df[col] = df[col].str.replace("%|K|M|B", "", regex=True)

    else: None

  # Lascia solo numeri e /
  df["Date"] = df["Date"].str.replace(r"[-.]", "/", regex=True)

  # Trasforma in datetime la colonna Date
  df["Date"] = pd.to_datetime(df["Date"], format="%m/%d/%Y")

  # cambia formato Date in giorno/mese/anno
  df["Date"] = df["Date"].dt.strftime("%d/%m/%Y")

  # Conversione in datetime di Date
  df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

  # Conversione di tutte le colonne rimaste in float
  df = df.astype({"Price": float, "Open": float, "High": float, "Low": float, "Change %": float, "Vol.": float })

  # moltiplico Vol. x 1000 cosi da avere il numero corretto
  df["Vol."] = df["Vol."] * 1000

  return df

def imputer_dataset(df: pd.DataFrame) -> pd.DataFrame:
  """
  1.Riempie i valori -1 nella colonna 'Price' calcolandoli 
  dal prezzo della riga successiva e dalla variazione in 'Change %'.

  Formula:
        Price_oggi = Price_domani * (1 + Change% / 100)
  
  2. Riempie i NaN in 'Vol.' usando KNNImputer.


  Assunzioni:
    - DataFrame ordinato in data decrescente (prima riga = giorno più recente).
    - 'Change %' è espresso in punti percentuali (es. -1.05 per -1,05%).

  """
  
  df = df.copy()

  # Conversione sicura a numerico
  df["Price"] = pd.to_numeric(df["Price"], errors="coerce")
  df["Change %"] = pd.to_numeric(df["Change %"], errors="coerce")

  # Maschera per i valori da riempire
  mask = df["Price"] == -1

  # Prezzo della riga successiva (nel tempo)
  prezzo_successivo = df["Price"].shift(-1)

  # Calcolo prezzo stimato 
  prezzo_calcolato = (prezzo_successivo * (1 + df["Change %"] / 100)).round(1)

  # Sostituzione solo dove serve
  df.loc[mask, "Price"] = prezzo_calcolato[mask]

  # KNNImputer solo per Vol. 
  imputer = KNNImputer(n_neighbors=14, weights="distance")
  vol_df = df[["Vol."]]  # DataFrame 2D
  vol_imputed = imputer.fit_transform(vol_df)
  df["Vol."] = vol_imputed.round(0)


  return df
  
  
# ETL => Funzione che incorpora tutto 

def main():
    # 1) Leggi tutti i CSV dal prefix bronze (accetta anche wildcard)
    #    Esempio: s3://profession-ai-adrian-bronze/bitcoin/*.csv
    
    df= wr.s3.read_csv(path=bronze_path_s3)
    
    # 2) Applicazione delle funzioni di cleaning e IMPUTING
    
    df = clean_dataset(df)
    
    df = imputer_dataset(df)
    
    # 3) Scrittura dell'output in formato Parquet sul bucket silver (Snappy)
    wr.s3.to_parquet(
        df=df,
        path=silver_path_s3,
        compression="snappy",
        dataset=True)
        
if __name__ == "__main__":
    main()