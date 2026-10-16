import sqlite3
import pandas as pd
from pathlib import Path
import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

RAIZ = Path(__file__).resolve().parents[2]
BRZ_PATH = RAIZ / "data" / "bronze" / "metadata"
DB_PATH = RAIZ / "data" / "silver" / "metadata.db"

def latest_snapshot():
    snapshot = max([p for p in BRZ_PATH.iterdir() if p.is_dir()])
    return snapshot

def get_df(path):
    jsons = sorted(path.glob("page_*.json"))
    json_list = []
    for j in jsons:
        with open(j, "r", encoding="utf-8") as arq:
            json_list.extend(json.load(arq)["recordings"])
    df = pd.DataFrame(json_list)
    return df

def time_in_seconds(time_str):
    if pd.isna(time_str):
        return pd.NA
    index = time_str.split(":")
    seconds = 0
    temp = len(index) -1
    for n in range(len(index)):
        seconds += int(index[n]) * 60 ** temp
        temp -= 1
    return seconds

def transform_df(df):
    df["id"] = df["id"].astype(int)
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["smp"] = pd.to_numeric(df["smp"], errors="coerce").astype("Int64")

    df["species"] = df["gen"] + " " + df["sp"]
    df["length_s"] = df["length"].apply(time_in_seconds).astype("Int64")

    df["auto"] = df["auto"].replace("", pd.NA)
    df["dvc"] = df["dvc"].replace("", pd.NA)
    df["mic"] = df["mic"].replace("", pd.NA)
    df["method"] = df["method"].replace("", pd.NA)
    df["type"] = df["type"].replace("", pd.NA)

    df = df.drop(columns=["gen", "sp", "grp", "cnt", "length", "ssp", "sex", "stage",
                          "regnr", "temp", "rmk", "loc", "alt", "en", "animal-seen", "playback-used",
                          "time", "date", "uploaded", "url", "file-name", "_meta", "sono", "osci",
                          "annotation-set"])

    bg_df = df[["id", "also"]].explode("also")
    df = df.drop(columns=["also"])
    bg_df = bg_df.rename(columns={"id":"recording_id", "also":"species"})
    bg_df = bg_df.dropna(subset=["species"])

    df = df.drop_duplicates(subset="id")
    bg_df = bg_df.drop_duplicates()

    return df, bg_df

def load_to_db(recordings_df, bg_df):
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    recordings_df.to_sql("recordings", conn, if_exists="replace", index=False)
    bg_df.to_sql("background_species", conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    logging.info("Iniciando transformação na silver!")
    snapshot_path = latest_snapshot()
    df = get_df(snapshot_path)
    recordings, bg = transform_df(df)
    load_to_db(recordings, bg)
    logging.info(f"Transformação finalizada! recordings: {len(recordings)} dados, background_species: {len(bg)} dados!")
