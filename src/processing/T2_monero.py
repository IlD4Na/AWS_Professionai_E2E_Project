import sys
import pandas as pd
import awswrangler as wr

# From bronze bucket
trend_path = "s3://profession-ai-adrian-bronze/trend_monero/"

# From Silver path
monero_path = "s3://profession-ai-adrian-silver/monero/"

# Path di output

output_path = "s3://profession-ai-adrian-gold/monero/"

# 1) Lettura file 

monero = wr.s3.read_parquet(monero_path)

trend = wr.s3.read_csv(trend_path) 

# 2) Media mobile a 10 giorni (mobile_mean_10)

# Ordinamento per data crescente
monero = monero.sort_values("Date")

# Uso della funzione rolling che ci permette di definire una finestra 
monero["Price"] = monero["Price"].rolling(window=10, min_periods=1).mean()

monero_done = monero[["Date","Price"]].dropna(subset=["Date"])

# 3) Normalizzazione data di trend 

trend["Settimana"] = pd.to_datetime(trend["Settimana"], errors="coerce")

trend.rename(columns={'Settimana': 'Date'}, inplace=True)

# 4) Join usando al data come chiave di join 
final = pd.merge(monero_done,trend,how="inner",on="Date")


# 5) Scrittura del file finale sul bucket gold in Parquet 
wr.s3.to_parquet(
    df=final,
    path=output_path,
    dataset=True,
    compression="snappy")
    
    