#!/usr/bin/env python3
"""Baixa o CSV de reunioes publicas da ANEEL e gera processos_data.js."""

import requests
import csv
import io
import re
import os
from datetime import datetime

CSV_URL = (
    "https://dadosabertos.aneel.gov.br/dataset/"
    "a9fb5b4b-59ca-4be8-9690-876d9547271d/resource/"
    "43386a8b-4781-44ec-a082-fa7fdfe33186/download/"
    "pautas-atas-reunioes-publicas-diretoria.csv"
)
MIN_YEAR = 2024

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))


def esc(s):
    s = str(s).strip()
    s = s.replace("\\", "\\\\")
    s = s.replace('"', '\\"')
    s = s.replace("\n", " ").replace("\r", "")
    return s


def parse_date(raw):
    raw = raw.strip()
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", raw)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return raw[:10]
    return raw


def main():
    print("Baixando CSV da ANEEL...")
    resp = requests.get(CSV_URL, timeout=180)
    resp.encoding = "iso-8859-1"
    print(f"Download concluido: {len(resp.text):,} caracteres")

    reader = csv.DictReader(io.StringIO(resp.text), delimiter=";")

    records = []
    for row in reader:
        date = parse_date(row.get("DatReuniao", ""))
        year = int(date[:4]) if len(date) >= 4 and date[:4].isdigit() else 0
        if year < MIN_YEAR:
            continue

        records.append({
            "dr":      date,
            "rp":      row.get("IdeReuniao", "").strip(),
            "st":      row.get("IdcSituacao", "").strip(),
            "dir":     row.get("NomDiretorRelator", "").strip(),
            "proc":    row.get("NumProcesso", "").strip(),
            "ass":     row.get("NomClassificacaoAssunto", "").strip(),
            "dec":     row.get("TxtDecisaoJulgamento", "").strip(),
            "ord":     row.get("NumOrdem", "").strip(),
            "ato":     row.get("NumAtoAdministrativo", "").strip(),
            "tipoAto": row.get("NomTipoAtoAdministrativo", "").strip(),
            "txt":     row.get("TxtAssunto", "").strip(),
            "res":     row.get("DscResultadoJulgamento", "").strip(),
        })

    print(f"{len(records):,} registros de {MIN_YEAR}+ encontrados")

    # Gera processos_data.js
    js_path = os.path.join(ROOT, "processos_data.js")
    lines = ["const PROCESSOS=[\n"]
    for r in records:
        fields = ",".join(
            f'"{k}":"{esc(v)}"'
            for k, v in r.items()
            if v and v not in ("0", "")
        )
        lines.append(f"  {{{fields}}},\n")
    lines.append("];\n")

    with open(js_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Arquivo gerado: {js_path}")

    # Atualiza badge de data no index.html
    idx_path = os.path.join(ROOT, "index.html")
    with open(idx_path, "r", encoding="utf-8") as f:
        html = f.read()

    today = datetime.utcnow().strftime("%d/%m/%Y")
    html_new = re.sub(r"Atualizado \d{2}/\d{2}/\d{4}", f"Atualizado {today}", html)

    with open(idx_path, "w", encoding="utf-8") as f:
        f.write(html_new)
    print(f"index.html atualizado com a data {today}")


if __name__ == "__main__":
    main()
