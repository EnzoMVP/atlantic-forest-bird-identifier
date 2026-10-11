import time
import datetime
import requests as rq
import json
import os
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

api_url = "https://xeno-canto.org/api/3/recordings"

TENTATIVAS = 5
TIMEOUT = 20
PER_PAGE = 500

RAIZ = Path(__file__).resolve().parents[2]
PATH = RAIZ / "data" / "raw" / "metadados" / f"{datetime.date.today().isoformat()}"

def page_request(page_num):
    tempo_espera = 1
    params = {
        "query": 'grp:birds cnt:brazil q:">C"',
        "per_page": PER_PAGE,
        "page": page_num,
        "key": os.getenv("XENO_CANTO_API_KEY")
    }
    for tentativa in range(1, TENTATIVAS+1):
        try:
            response = rq.get(api_url, params=params, timeout=TIMEOUT)
        except (rq.ConnectionError, rq.Timeout) as e:
            logging.warning(f"Tentativa: {tentativa}, Página {page_num}, Erro {type(e).__name__}")
            time.sleep(tempo_espera)
            tempo_espera *= 2
            continue

        if 400 <= response.status_code < 500:
            raise RuntimeError(f"Tentativa: {tentativa}, Página {page_num}, Resposta HTTP: {response.status_code}")
        elif 500 <= response.status_code < 600:
            logging.warning(f"Tentativa: {tentativa}, Página {page_num}, Resposta HTTP: {response.status_code}")
            time.sleep(tempo_espera)
            tempo_espera *= 2
            continue
        return response.json()

    raise RuntimeError(f"Página {page_num} falhou!")

def save_page(page_num, content):
    json_path = PATH / f"page_{page_num:03d}.json"
    with open(json_path, "w", encoding="utf-8") as arq:
        json.dump(content, arq, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    PATH.mkdir(parents=True, exist_ok=True)
    first = page_request(1)
    total = first["numPages"]
    gravacoes = first["numRecordings"]
    save_page(1, first)
    logging.info(f"Página {1}/{total} salva com sucesso!")
    for n in range(2, total+1):
        time.sleep(1)
        page_data = page_request(n)
        save_page(n, page_data)
        logging.info(f"Página {n}/{total} salva com sucesso!")
    logging.info(f"Ingestão concluída: {total} páginas, {gravacoes} gravações! em: {PATH}")