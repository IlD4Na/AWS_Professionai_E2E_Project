import json
import boto3
import redshift_connector

# Costanti necessarie per connettersi a Redshift
SECRET_ID = "redshift/adi-data-dev"   # <-- nome del secret di tipo "Amazon Redshift database"
S3_PREFIX     = "s3://profession-ai-adrian-gold/monero/"
IAM = "arn:aws:iam::470880515310:role/RedShift_Bitcoin"
SCHEMA = "crypto_schema"
TABLE = "monero_prices"
REGION = "eu-west-3"


#  Lettura del secret (host, port, dbname, username, password)
sm = boto3.client("secretsmanager", region_name=REGION)
sec = sm.get_secret_value(SecretId=SECRET_ID)

#  Creazione dizionario contenente tutte le info del secret
creds = json.loads(sec["SecretString"])

host = creds.get("host") or creds.get("hostname")

port = int(creds.get("port", 5439))

dbname = creds.get("dbname") or creds.get("database") or "dev"

user = creds["username"]

password = creds["password"]

#  Connessione a Redshift
con = redshift_connector.connect(
    host=host, port=port, database=dbname, user=user, password=password)

cur = con.cursor()

# Crea schema se non esiste
cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}";')

# Tabella con *gli stessi nomi* e *tipi* dei Parquet (nota le virgolette)


cur.execute(f"""
  CREATE TABLE IF NOT EXISTS {SCHEMA}.{TABLE} (
    "Date" TIMESTAMP,
    "Price" DOUBLE PRECISION,
    "interesse_bitcoin" BIGINT
  );
""")

cur.execute(f"""
  COPY {SCHEMA}.{TABLE}
  FROM '{S3_PREFIX}'
  IAM_ROLE '{IAM}'
  FORMAT AS PARQUET;
""")

con.commit()
cur.close();
con.close()
