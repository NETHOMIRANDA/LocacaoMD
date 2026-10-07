"""
Locação MD – Vistorias
Banco de dados SQLite (criado automaticamente na pasta 'instance').
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)

DB_PATH = os.path.join(INSTANCE_DIR, "locaomd.db")

# Intervalo padrão entre vistorias (dias)
DIAS_VISTORIA = 30

# Categorias obrigatórias de fotos da vistoria
CATEGORIAS = [
    ("externo_frente",        "Externo – Frente",        "Foto do ângulo frontal do carro"),
    ("externo_traseira",      "Externo – Traseira",      "Foto do ângulo traseiro do carro"),
    ("externo_lado_esq",      "Externo – Lado esquerdo", "Foto do lado esquerdo inteiro"),
    ("externo_lado_dir",      "Externo – Lado direito",  "Foto do lado direito inteiro"),
    ("pneu_dianteiro_esq",    "Pneu – Dianteiro esq.",   "Pneu dianteiro esquerdo (foto individual)"),
    ("pneu_dianteiro_dir",    "Pneu – Dianteiro dir.",   "Pneu dianteiro direito (sozinho)"),
    ("pneu_traseiro_esq",     "Pneu – Traseiro esq.",    "Pneu traseiro esquerdo (sozinho)"),
    ("pneu_traseiro_dir",     "Pneu – Traseiro dir.",    "Pneu traseiro direito (sozinho)"),
    ("interno_bancos",      "Interno – Bancos",        "Foto dos bancos dianteiros e traseiros"),
    ("interno_porta_malas", "Interno – Porta-malas",   "Foto do porta-malas aberto"),
    ("interno_teto",        "Interno – Teto",          "Foto do teto e forrações"),
    ("interno_piso",        "Interno – Pisos",         "Foto do piso / carpete"),
    ("painel",                "Painel",                  "Foto do painel / velocímetro"),
    ("motor",                 "Motor",                   "Foto do motor (em local claro e de dia)"),
]

GRUPOS_CONDICAO = [
    ("externo",  "Condição do externo"),
    ("pneus",    "Condição dos pneus"),
    ("interno",  "Condição do interior"),
    ("painel",   "Condição do painel"),
    ("motor",    "Condição do motor"),
]

OPCOES_CONDICAO = ["Ótimo", "Bom", "Regular", "Ruim"]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS motoristas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT DEFAULT '',
            fone TEXT DEFAULT '',
            veiculo TEXT NOT NULL,
            placa TEXT NOT NULL UNIQUE,
            cor TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1,
            criado_em TEXT DEFAULT (date('now','localtime'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS vistorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            motorista_id INTEGER NOT NULL,
            placa TEXT NOT NULL,
            data_vistoria TEXT NOT NULL,
            km_atual TEXT DEFAULT '',
            condicao_geral TEXT DEFAULT '',
            cond_externo TEXT DEFAULT '',
            cond_pneus TEXT DEFAULT '',
            cond_interno TEXT DEFAULT '',
            cond_painel TEXT DEFAULT '',
            cond_motor TEXT DEFAULT '',
            dia_claro INTEGER DEFAULT 0,
            observacao TEXT DEFAULT '',
            status TEXT DEFAULT 'pendente',
            nota_admin TEXT DEFAULT '',
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (motorista_id) REFERENCES motoristas(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS fotos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vistoria_id INTEGER NOT NULL,
            categoria TEXT NOT NULL,
            caminho TEXT NOT NULL,
            thumb TEXT DEFAULT '',
            criado_em TEXT DEFAULT (datetime('now','localtime')),
            FOREIGN KEY (vistoria_id) REFERENCES vistorias(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    # migração: adiciona coluna de condição interna em bancos antigos
    try:
        c.execute("ALTER TABLE vistorias ADD COLUMN cond_interno TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # coluna já existe

    conn.commit()
    conn.close()


def get_config(chave, padrao=""):
    conn = get_connection()
    row = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    conn.close()
    return row["valor"] if row else padrao


def set_config(chave, valor):
    conn = get_connection()
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------
# Regras de negócio
# ---------------------------------------------------------------

def ultima_vistoria(motorista_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM vistorias WHERE motorista_id = ? ORDER BY data_vistoria DESC, id DESC LIMIT 1",
        (motorista_id,),
    ).fetchone()
    conn.close()
    return row


def proxima_vistoria(motorista_id):
    """Retorna (data_proxima, dias_restantes, vencida)."""
    import datetime as _dt
    row = ultima_vistoria(motorista_id)
    if not row:
        return None, None, True
    data = _dt.date.fromisoformat(row["data_vistoria"])
    prox = data + _dt.timedelta(days=DIAS_VISTORIA)
    hoje = _dt.date.today()
    return prox.isoformat(), (prox - hoje).days, hoje > prox


if __name__ == "__main__":
    init_db()
    print("Banco criado em:", DB_PATH)
