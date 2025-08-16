# 📊 Progetto Pipeline End to End in AWS

Qui troverai un progetto di **data engineering** che mostra come costruire una pipeline dati su **AWS End to End**, con l’obiettivo di raccogliere, trasformare e caricare (ETL) dati relativi a <span style="color:red">**Bitcoin**</span> e <span style="color:red">**Monero**</span> in simultanea in un database Serverless **Amazon Redshift**.


## Servizi utilizzati 
- **AWS S3** (Servizio cloud di archiviazione object oriented)
- **AWS Glue ETL** (Servizio Serverless che facilita l'ELT, permette la creazione di job in Python Shell o Spark Shell)
- **AWS Secret Manager** (Servizio di gestione sicura dei segreti ovvero dei dati sensibili come utenti e password per accedere ad un database)
- **AWS Step Functions** (Servizio di orchestrazione interno ad AWS simile ad Apache Airflow)
- **AWS Redshift Serverless** (Servizio di datawarehousing distribuito colonnare, noi useremo però la versione Serverless)
-**IAM Roles** (Servizio di Identity and Access Management)


---
## 🎯 Obiettivi del progetto

- **Acquisizione dei dati**

Raccogliere file grezzi su prezzi delle criptovalute (BTC ed XMR) e su Google Trends, caricandoli in un bucket S3 (raw/bronze).

- **Pulizia e trasformazione**

Gestire valori mancanti nei prezzi (-1) con varie strategie.

- **Convertire i dati in formato Parquet e salvarli in un bucket S3 “argento”.**

Applicare smoothing (es. media mobile a 10 giorni) per ridurre il rumore nei prezzi.

- **Unificazione dei dataset**

Eseguire il join tra prezzi e Google Trends (consapevoli della diversa granularità temporale).

Produrre un file strutturato con: data, prezzo, indice_google_trend.

- **Caricamento e analisi**

Caricare i dati finali su Amazon Redshift, pronti per query SQL e analisi.

**(Opzionale)** Creare dashboard interattive con Amazon QuickSight per esplorare pattern e trend.

- **Architettura della pipeline**

Due pipeline parallele, una per BTC e una per XMR, indipendenti ma con struttura analoga.

Orchestrazione tramite AWS Step Functions.

Scelta tra AWS Glue ETL o Amazon EMR per la fase di trasformazione.

- **Valore e benefici**

Automazione completa del processo end-to-end (da dati grezzi a insight).

Scalabilità, per gestire grandi volumi e aggiungere altre criptovalute facilmente.

Flessibilità nelle trasformazioni (diversi approcci a pulizia e smoothing).

Insight immediati su Redshift/QuickSight a supporto di trader, analisti e aziende.

--- 

## 📂 Struttura della Repository

```text
AWS_PROFESSIONAI_PROJECT/
├─ README.md
├─ requirements.txt
├─ Esplorazione_1_Pipeline.ipynb
├─ src/
│  ├─ Load_file_in_S3.py    # Upload dati grezzi in bucket bronze
│  ├─ processing/
│  │   ├─ T1_bitcoin.py     # 1 Pipeline dataset bitcoin   
│  │   ├─ T1_monero.py      # 1 Pipeline dataset monero
│  │   ├─ T2_bitcoin.py     # 2 Pipeline dataset bitcoin
│  │   ├─ T2_monero.py      # 2 Pipeline dataset monero
│  │   ├─ Load_bitcoin.py   # 3 Pipeline dataset bitcoin (Load)
│  │   └─ Load_monero.py    # 3 Pipeline dataset monero (Load)
│  ├─ orchestration/
│  │   ├─ Step_F_graph.svg  # Immagine dell'orchestrazione      
│  │   └─ Step_F_def.json   # orchestrazione con Step Functions
│  └─ analytics/            # Quicksight
├─ data/                    # dati originali
│  ├─ BTC_EUR_Historical_Data.csv
│  ├─ XMR_EUR Kraken Historical Data.csv
│  ├─ google_trend_bitcoin.csv
│  └─ google_trend_monero.csv               
└─ docs/                    # altro
```


## 📌 Spiegazione del workflow 

### Upload dei dati grezzi nel bucket bronze

Prima di partire con la creazione della 1*Pipeline ho creato 3 bucket:
- **Bucket Bronze** => **Bucket Silver** => **Bucket Gold** 


Verrà seguito questo schema per il salvataggio dei vari file .parquet che si creeranno. 

Ho eseguito l'upload dei dati grezzi nel bucket S3 tramite ```Load_file_in_S3.py```. 




### 1* Pipeline
Moduli da mettere nella sezione 'Additional Python modules path' del job.
```pandas==2.2.2,awswrangler==3.11.0,pyarrow==16.1.0,scikit-learn==1.4.2```

Inizialmente ho effettuato un'esplorazione dei dataset su GoogleColab cosi da notare le varie anomalie presenti nei 4 file csv di tipo raw. In seguito ho creato due funzioni ```clean_dataset``` e ```imputer_dataset``` che ho incorporato nei Glue ETL job **T1_bitcoin.py** e **T1_monero.py**
- ```clean_dataset``` => Pulisce e normalizza un dataset formato dalle seguenti colonne columns: `["Date", "Price", "Open", "High", "Low", "Vol.", "Change %"]`, con le seguenti assunzioni:
 1. Date è una stringa in formato US %m/%d/%Y (es. "25/03/2025").
2. Le colonne numeriche possono contenere separatori come (,).
3. Vol. può avere suffissi come K/M/B (es. "3.39K", "1.2M").
4. Change % include il simbolo % (es. "2.15%"), che rimuoviamo:
il risultato è espresso in punti percentuali (es. 2.15, non 0.0215). 
- ```imputer_dataset``` => Riempie i valori -1 nella colonna 'Price' calcolandoli dal prezzo della riga successiva e dalla variazione in 'Change %' ed inoltre riempie i NaN in 'Vol.' usando KNNImputer.

I Glue JOB ETL **T1_bitcoin.py** e **T1_monero.py**  avranno come input i file caricati sul bucket bronze rispettivamente nelle cartelle:
- bucket_bronze/bitcoin/file.csv
- bucket_bronze/monero/file.csv

Come **output** salverà i dati in formato .snappy.parquet nel bucket silver rispettivamente:

- bucket_silver/bitcoin/file.snappy.parquet
- bucket_silver/monero/file.snappy.parquet


### 2* Pipeline 
Moduli da mettere nella sezione 'Additional Python modules path' del job.
```awswrangler==3.11.0,pandas==2.2.2,pyarrow==16.1.0```

Per la seconda pipeline ho fatto delle prove direttamente su Glue ETL, questa pipeline calcolerà una media mobile a 10 giorni e farà il merge tra i due file per ottenere un file parquet con 3 colonne: Data, prezzo,  bitcoin_interesse.

I Glue JOB ETL **T2_bitcoin.py** e **T2_monero.py**  avranno come input i file caricati sul bucket silver rispettivamente nelle cartelle:

- bucket_silver/bitcoin/file.snappy.parquet
- bucket_bronze/trend_bitcoin/file.csv
- bucket_silver/monero/file.snappy.parquet
- bucket_bronze/trend_monero/file.csv

Come **output** salverà i dati in formato .snappy.parquet nel bucket silver rispettivamente:

- bucket_gold/bitcoin/file.parquet
- bucket_gold/monero/file.parquet

### 3* Pipeline 
Moduli da mettere nella sezione 'Additional Python modules path' del job.
 
 ```redshift-connector==2.1.2```

 Prima di procedere con la terza pipeline ho dovuto in ordine:
 - Creare uno spazio di lavoro creare uno spazio dei nomi
 - Creare un gruppo di lavoro (ho usato il database di default)
 - Creato un secret_id con secret manager cosi da usarlo per collegarmi al database su redshift serverless ma in maniera sicura senza esporre nel codice gli username e le password

I Glue JOB ETL **Load_bitcoin.py** e **Load_monero.py**  avranno come input i file parquet caricati sul bucket gold rispettivamente nelle cartelle:
- bucket_gold/bitcoin/file.parquet
- bucket_gold/monero/file.parquet

Come **output** salverà i dati nel database di destinazione presente in Redshift. A questo punto si potranno interrogare i dati direttamente dalla console di Redshift tramite SQL. 

### Assemblamento in AWS Step Functions

Per l'assemblamento si trova la configurazione scritta in ```Step_F_def.json``` e lo schema si trova in ```Step_F_graph.svg```. 

Si è optato per una parallelizzazione dei due flow direttamente in AWS Step Functions dato che i vari script sono scritto in Python Shell, perchè i file di input non richiedono altissima elaborazione. 
### QuickSight 

Nella cartella analytics/ ci sono due grafici creati con QuickSight in diretto contatto con AWS Redshift. 

E notiamo dai due grafici che vi è una certa correlazione a prima vista tra il trend ed il prezzo della criptovaluta sia in Bitcoin che in Monero. 

--- 
## POSSIBILI MIGLIORAMENTI 

- Tutta la pipeline è stata elaborata usando ruoli IAM con policy che davano il completo accesso a tutti i servizi in maniera da rendere eseguibile tutta la Pipeline senza errori di policy. Un possibile miglioramento potrebbe essere determinare dei ruoli IAM che abbiano delle policy limitate ma essenziali per il singolo Glue ETL job oppure per per i vari servizi che si sono usati. 
- Aggiunta di una funzione lambda che determine l'uso di file sulla base della data di aggiunta, ovvero vengono presi i file in input che sono stati caricati per ultimi, in questa maniera si potrebbe garantire un continuo uso della pipeline senza modifiche manuali a livello dei Glue ETL jobs. 
