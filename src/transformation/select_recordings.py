from pathlib import Path
import logging
import sqlite3
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

RAIZ = Path(__file__).resolve().parents[2]
SILVER_DB = RAIZ / "data" / "silver" / "metadata.db"
GOLD_DB = RAIZ / "data" / "gold" / "gold.db"
QUERY_PATH = Path(__file__).resolve().parent / "sql" / "select_recordings.sql"
SPECIES_YAML = RAIZ / "configs" / "species.yaml"

def load_config():
    with open(RAIZ / "configs" / "selection.yaml", encoding="utf-8") as arq:
        config = yaml.safe_load(arq)
    return config

def load_df(config):
    conn = sqlite3.connect(SILVER_DB)
    conn.execute("ATTACH DATABASE ? AS gold", (str(GOLD_DB),))
    query = QUERY_PATH.read_text(encoding="utf-8")
    df = pd.read_sql(
        query,
        conn,
        params={
            "min_grav_dentro": config["min_recordings_atlantic_forest"],
            "min_aut_brasil": config["min_recordists_brazil"]
        }
    )
    conn.close()
    return df

def save_df(df):
    conn = sqlite3.connect(GOLD_DB)
    df.to_sql("selected_recordings", conn, if_exists="replace", index=False)
    conn.close()
    logging.info(f"{len(df)} gravações de {df["species"].nunique()} espécies em selected_recordings (gold.db)")

def save_species_yaml(df, config):
    nomes_comuns = {}

    if SPECIES_YAML.exists():
        with open(SPECIES_YAML, encoding="utf-8") as arq:
            existing = yaml.safe_load(arq) or {}
        for item in existing.get("species", []):
            nomes_comuns[item["scientific_name"]] = item.get("common_name", "")

    especies = [
        {"scientific_name": sp, "common_name": nomes_comuns.get(sp, "")}
        for sp in sorted(df["species"].unique())
    ]

    data = {
        "criteria": config,
        "species": especies,
    }
    with open(SPECIES_YAML, "w", encoding="utf-8") as arq:
        yaml.safe_dump(data, arq, allow_unicode=True, sort_keys=False)

    logging.info(f"{len(especies)} espécies salvas em {SPECIES_YAML.name}")

if __name__ == "__main__":
    config = load_config()
    df = load_df(config)
    save_df(df)
    save_species_yaml(df, config)