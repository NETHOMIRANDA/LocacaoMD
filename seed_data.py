"""
Locação MD – Vistorias
Importa motoristas/veículos do sistema anterior (dados_motoristas.json).
Uso: python seed_data.py "caminho/para/dados_motoristas.json"
"""
import json
import os
import sys

from database import get_connection, init_db


def importar(caminho_json):
    with open(caminho_json, "r", encoding="utf-8") as f:
        conteudo = json.load(f)

    dados = conteudo.get("dados", {})
    init_db()
    conn = get_connection()

    inseridos = 0
    for nome, info in dados.items():
        veiculo = info.get("veiculo", "")
        placa = (info.get("placa") or "").strip()
        if not placa:
            continue
        existente = conn.execute(
            "SELECT id FROM motoristas WHERE placa = ?", (placa,)
        ).fetchone()
        if existente:
            print(f"- {nome} ({placa}) já existe, ignorado")
            continue
        conn.execute(
            "INSERT INTO motoristas (nome, veiculo, placa, ativo) VALUES (?,?,?,1)",
            (nome.strip(), veiculo, placa),
        )
        inseridos += 1
        print(f"+ {nome} | {veiculo} | {placa}")

    conn.commit()
    conn.close()
    print(f"\nImportados {inseridos} motorista(s)/veículo(s).")


if __name__ == "__main__":
    caminho = sys.argv[1] if len(sys.argv) > 1 else ""
    if not caminho or not os.path.exists(caminho):
        print("Informe o caminho do JSON:")
        print('  python seed_data.py "caminho/dados_motoristas.json"')
        sys.exit(1)
    importar(caminho)
