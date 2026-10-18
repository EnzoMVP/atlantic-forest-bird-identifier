import sqlite3
import pandas as pd
import geopandas as gpd
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

RAIZ = Path(__file__).resolve().parents[2]
DB_PATH = RAIZ / "data" / "silver" / "metadata.db"
SHAPEFILE_PATH = RAIZ / "data" / "bronze" / "reference" / "biomas_ibge" / "lm_bioma_250.shp"
GOLD_PATH = RAIZ / "data" / "gold" / "gold.db"

def get_recording_pos(db_path):
    conexao = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT r.id, r.lat, r.lon FROM recordings r", conexao)
    df = df.dropna()
    conexao.close()
    return df

def get_biome_pos(shp_path):
    biomes = gpd.read_file(shp_path)
    atlantic_forest = biomes[biomes["Bioma"] == "Mata Atlântica"]
    return atlantic_forest

def load_recording_pos(record_pos, biome_pos):
    pontos = gpd.GeoDataFrame(record_pos[["id"]],
                              geometry=gpd.points_from_xy(x=record_pos["lon"], y=record_pos["lat"]),
                              crs="EPSG:4326")
    pontos = pontos.to_crs(biome_pos.crs)
    comparacao = gpd.sjoin(pontos, biome_pos, how="left", predicate="within")
    comparacao["in_atlantic_forest"] = comparacao["index_right"].notna()
    df = comparacao[["id", "in_atlantic_forest"]]

    GOLD_PATH.parent.mkdir(parents=True, exist_ok=True)
    conex = sqlite3.connect(GOLD_PATH)
    df.to_sql("in_forest", conex, if_exists="replace", index=False)
    conex.close()
    logging.info(f"Junção feita, gravações dentro da mata atlântica: {df["in_atlantic_forest"].sum()}/{len(df)}")

if __name__ == "__main__":
    r_pos = get_recording_pos(DB_PATH)
    b_pos = get_biome_pos(SHAPEFILE_PATH)
    load_recording_pos(r_pos, b_pos)
