from sqlalchemy import create_engine
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_db_conn():
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
    )
    return conn

def get_alchemy_engine():
    db_url = (
        f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    return create_engine(db_url)

def geodataframe_to_postgis(gdf):
    engine = get_alchemy_engine()
    gdf.to_postgis("segments", engine, if_exists="replace")
    print(f"Data saved successfully.")