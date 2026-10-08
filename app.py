"""
Locação MD – Vistorias
Aplicativo web para controle de vistorias de veículos.
Execute:  python app.py    ->  http://127.0.0.1:5000
"""
import base64
import datetime
import io
import os
import uuid

from flask import (
    Flask, abort, flash, redirect, render_template, request, send_from_directory,
    session, url_for,
)
from PIL import Image

import database as db

app = Flask(__name__)
app.secret_key = os.environ.get("LOCAOMD_CHAVE", "locaomd-secret-change-me")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FOTOS_DIR = os.path.join(BASE_DIR, "fotos")
THUMBS_DIR = os.path.join(FOTOS_DIR, "_thumbs")
os.makedirs(FOTOS_DIR, exist_ok=True)
os.makedirs(THUMBS_DIR, exist_ok=True)

ADMIN_SENHA_ENV = os.environ.get("LOCAOMD_SENHA")
TAM_MAX = 12 * 1024 * 1024  # 12 MB por foto

db.init_db()


def admin_senha():
    """Senha do administrador: variável de ambiente tem prioridade,
    senão a senha salva no banco (configurável pelo app)."""
    if ADMIN_SENHA_ENV:
        return ADMIN_SENHA_ENV
    return db.get_config("admin_senha", "locaomd123")


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def hoje_str():
    return datetime.date.today().isoformat()


def fmt(data_iso):
    if not data_iso:
        return "—"
    try:
        return datetime.date.fromisoformat(data_iso).strftime("%d/%m/%Y")
    except ValueError:
        return data_iso


def salvar_foto_base64(data_url, placa, data_vistoria, categoria):
    """Decodifica a foto capturada pela câmera (base64) e salva
    original + miniatura. Retorna (caminho, thumb) ou (None, None)."""
    if not data_url:
        return None, None
    if not data_url.startswith("data:image/"):
        raise ValueError("Foto inválida (formato inesperado)")

    cabecalho, b64 = data_url.split(",", 1)
    try:
        dados = base64.b64decode(b64)
    except Exception:
        raise ValueError("Foto inválida (não foi possível decodificar)")

    if len(dados) > TAM_MAX:
        raise ValueError("Foto muito grande (máximo de 12 MB). Tire a foto novamente.")

    ext = ".png" if "png" in cabecalho else ".jpg"
    nome = f"{uuid.uuid4().hex}{ext}"
    sub = os.path.join(placa.strip().upper().replace(" ", "_"), data_vistoria)
    pasta = os.path.join(FOTOS_DIR, sub)
    os.makedirs(pasta, exist_ok=True)

    caminho = os.path.join(pasta, nome)
    try:
        img = Image.open(io.BytesIO(dados))
        img.verify()  # garante que é uma imagem real
        img = Image.open(io.BytesIO(dados))
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(caminho, "JPEG", quality=88)
    except Exception:
        raise ValueError("Foto inválida (arquivo corrompido)")

    thumb_name = f"{uuid.uuid4().hex}_thumb.jpg"
    caminho_thumb = os.path.join(THUMBS_DIR, thumb_name)
    with Image.open(caminho) as img2:
        img2.thumbnail((420, 420))
        if img2.mode != "RGB":
            img2 = img2.convert("RGB")
        img2.save(caminho_thumb, "JPEG", quality=78)

    return (
        os.path.join(sub, nome).replace("\\", "/"),
        caminho_thumb.replace("\\", "/"),
    )


def motorista_por_id(motorista_id):
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM motoristas WHERE id = ?", (motorista_id,)).fetchone()
    conn.close()
    return row


def listar_motoristas(ativos_only=False):
    conn = db.get_connection()
    if ativos_only:
        rows = conn.execute(
            "SELECT * FROM motoristas WHERE ativo = 1 ORDER BY nome"
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM motoristas ORDER BY nome"
        ).fetchall()
    conn.close()
    return rows


def vistorias_motorista(motorista_id):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM vistorias WHERE motorista_id = ? ORDER BY data_vistoria DESC, id DESC",
        (motorista_id,),
    ).fetchall()
    conn.close()
    return rows


def fotos_vistoria(vistoria_id):
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT * FROM fotos WHERE vistoria_id = ? ORDER BY categoria",
        (vistoria_id,),
    ).fetchall()
    conn.close()
    return rows


def vistorias_por_mes(ano, mes):
    conn = db.get_connection()
    rows = conn.execute(
        """
        SELECT v.*, m.nome AS motorista_nome, m.veiculo, m.placa
        FROM vistorias v
        JOIN motoristas m ON m.id = v.motorista_id
        WHERE strftime('%Y', v.data_vistoria) = ? AND strftime('%m', v.data_vistoria) = ?
        ORDER BY v.data_vistoria DESC, v.id DESC
        """,
        (str(ano), f"{mes:02d}"),
    ).fetchall()

    # anexa miniaturas de até 6 fotos de cada vistoria
    resultado = []
    for row in rows:
        fotos = conn.execute(
            "SELECT thumb, categoria FROM fotos WHERE vistoria_id = ? ORDER BY categoria LIMIT 6",
            (row["id"],),
        ).fetchall()
        resultado.append({"vistoria": row, "thumbs": fotos})

    conn.close()
    return resultado


# ----------------------------------------------------------------------
# Página inicial – escolha do motorista
# ----------------------------------------------------------------------

@app.route("/")
def index():
    motoristas = listar_motoristas(ativos_only=True)
    # acrescenta status da vistoria para facilitar a vida do motorista
    lista = []
    for m in motoristas:
        prox, dias, vencida = db.proxima_vistoria(m["id"])
        lista.append({
            "id": m["id"],
            "nome": m["nome"],
            "veiculo": m["veiculo"],
            "placa": m["placa"],
            "prox": prox,
            "dias": dias,
            "vencida": vencida,
        })
    return render_template("index.html", motoristas=lista, hoje=hoje_str())


@app.route("/m/<int:motorista_id>")
def link_motorista(motorista_id):
    """Link pessoal do motorista (ex.: /m/1). Abre direto o painel dele."""
    return painel_motorista(motorista_id)


# ----------------------------------------------------------------------
# Painel do motorista
# ----------------------------------------------------------------------

@app.route("/motorista/<int:motorista_id>")
def painel_motorista(motorista_id):
    m = motorista_por_id(motorista_id)
    if not m or not m["ativo"]:
        abort(404)

    ultima = db.ultima_vistoria(motorista_id)
    prox, dias, vencida = db.proxima_vistoria(motorista_id)
    historico = vistorias_motorista(motorista_id)

    return render_template(
        "motorista.html",
        motorista=m,
        ultima=ultima,
        prox=prox,
        dias=dias,
        vencida=vencida,
        historico=historico,
        dias_vistoria=db.DIAS_VISTORIA,
        fmt=fmt,
    )


# ----------------------------------------------------------------------
# Nova vistoria (formulário + envio de fotos)
# ----------------------------------------------------------------------

@app.route("/vistoria/nova/<int:motorista_id>", methods=["GET"])
def nova_vistoria(motorista_id):
    m = motorista_por_id(motorista_id)
    if not m or not m["ativo"]:
        abort(404)
    return render_template(
        "nova_vistoria.html",
        motorista=m,
        categorias=db.CATEGORIAS,
        grupos=db.GRUPOS_CONDICAO,
        opcoes=db.OPCOES_CONDICAO,
        hoje=hoje_str(),
    )


@app.route("/vistoria/nova/<int:motorista_id>", methods=["POST"])
def salvar_vistoria(motorista_id):
    m = motorista_por_id(motorista_id)
    if not m or not m["ativo"]:
        abort(404)

    data_vistoria = request.form.get("data_vistoria") or hoje_str()
    try:
        datetime.date.fromisoformat(data_vistoria)
    except ValueError:
        flash("Data de vistoria inválida.", "erro")
        return redirect(url_for("nova_vistoria", motorista_id=motorista_id))

    km = request.form.get("km_atual", "").strip()
    cond_geral = request.form.get("condicao_geral", "")
    dia_claro = 1 if request.form.get("dia_claro") == "on" else 0
    observacao = request.form.get("observacao", "").strip()

    if not dia_claro:
        flash("É obrigatório confirmar que as fotos foram tiradas em local claro e durante o dia.", "erro")
        return redirect(url_for("nova_vistoria", motorista_id=motorista_id))

    # coleta das fotos capturadas em tempo real pela câmera
    fotos_enviadas = {}
    capturas = {}
    gps = {}
    for chave, rotulo, _dica in db.CATEGORIAS:
        b64 = request.form.get(f"foto_b64_{chave}", "").strip()
        captura = request.form.get(f"captura_{chave}", "").strip()
        g = request.form.get(f"gps_{chave}", "").strip()
        if b64:
            fotos_enviadas[chave] = b64
            capturas[chave] = captura
            gps[chave] = g

    # exige todas as categorias
    obrigatorias = [c[0] for c in db.CATEGORIAS]
    faltando = [c for c in obrigatorias if c not in fotos_enviadas]
    if faltando:
        nomes = dict((c[0], c[1]) for c in db.CATEGORIAS)
        flash("Faltam fotos obrigatórias (devem ser tiradas pela câmera agora): "
              + ", ".join(nomes[f] for f in faltando), "erro")
        return redirect(url_for("nova_vistoria", motorista_id=motorista_id))

    # garante que a foto foi tirada AGORA (janela de +-5 minutos do servidor)
    agora_servidor = datetime.datetime.now(datetime.timezone.utc)
    for chave, captura_iso in capturas.items():
        try:
            t = datetime.datetime.fromisoformat(captura_iso.replace("Z", "+00:00"))
        except ValueError:
            flash("Foto sem registro de hora válido. Tire a foto pela câmera agora.", "erro")
            return redirect(url_for("nova_vistoria", motorista_id=motorista_id))
        if abs((agora_servidor - t).total_seconds()) > 300:
            flash("Foto tirada fora do horário permitido (mais de 5 minutos de diferença). "
                  "Tire todas as fotos pela câmera, agora, no momento da vistoria.", "erro")
            return redirect(url_for("nova_vistoria", motorista_id=motorista_id))

    # salva vistoria
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO vistorias
        (motorista_id, placa, data_vistoria, km_atual, condicao_geral,
         cond_externo, cond_pneus, cond_interno, cond_painel, cond_motor,
         dia_claro, observacao, status)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,'pendente')
        """,
        (
            motorista_id, m["placa"], data_vistoria, km, cond_geral,
            request.form.get("cond_externo", ""),
            request.form.get("cond_pneus", ""),
            request.form.get("cond_interno", ""),
            request.form.get("cond_painel", ""),
            request.form.get("cond_motor", ""),
            dia_claro, observacao,
        ),
    )
    vistoria_id = cur.lastrowid

    # salva fotos com registro da hora da captura
    try:
        for chave, b64 in fotos_enviadas.items():
            caminho, thumb = salvar_foto_base64(b64, m["placa"], data_vistoria, chave)
            cur.execute(
                "INSERT INTO fotos (vistoria_id, categoria, caminho, thumb, "
                "captura_em, gps) VALUES (?,?,?,?,?,?)",
                (vistoria_id, chave, caminho, thumb,
                 capturas.get(chave, ""), gps.get(chave, "")),
            )
        conn.commit()
    except Exception as e:
        conn.rollback()
        flash(f"Erro ao salvar fotos: {e}", "erro")
        return redirect(url_for("nova_vistoria", motorista_id=motorista_id))
    finally:
        conn.close()

    prox, dias, _ = db.proxima_vistoria(motorista_id)
    flash(f"Vistoria registrada! Próxima vistoria: {fmt(prox)} (em {db.DIAS_VISTORIA} dias).", "sucesso")
    return redirect(url_for("painel_motorista", motorista_id=motorista_id))


# ----------------------------------------------------------------------
# Área do administrador
# ----------------------------------------------------------------------

@app.route("/admin", methods=["GET"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("admin_dashboard"))
    return render_template("admin_login.html")


@app.route("/admin/entrar", methods=["POST"])
def admin_entrar():
    senha = request.form.get("senha", "")
    if senha == admin_senha():
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    flash("Senha incorreta.", "erro")
    return redirect(url_for("admin_login"))


@app.route("/admin/sair")
def admin_sair():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


def admin_obrigatorio(view):
    from functools import wraps

    @wraps(view)
    def interna(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)

    return interna


@app.route("/admin/dashboard")
@admin_obrigatorio
def admin_dashboard():
    hoje = datetime.date.today()
    conn = db.get_connection()

    total_motoristas = conn.execute(
        "SELECT COUNT(*) AS n FROM motoristas WHERE ativo = 1"
    ).fetchone()["n"]
    vistorias_mes = conn.execute(
        "SELECT COUNT(*) AS n FROM vistorias WHERE strftime('%Y-%m', data_vistoria) = ?",
        (hoje.strftime("%Y-%m"),),
    ).fetchone()["n"]
    pendentes = conn.execute(
        "SELECT COUNT(*) AS n FROM vistorias WHERE status = 'pendente'"
    ).fetchone()["n"]

    # vistorias atrasadas por motorista
    atrasados = []
    for m in listar_motoristas(ativos_only=True):
        prox, dias, vencida = db.proxima_vistoria(m["id"])
        if vencida:
            atrasados.append({
                "id": m["id"], "nome": m["nome"], "placa": m["placa"],
                "veiculo": m["veiculo"], "prox": prox, "dias": dias,
            })

    ultima_por_motorista = {
        m["id"]: db.ultima_vistoria(m["id"]) for m in listar_motoristas()
    }

    conn.close()
    return render_template(
        "admin_dashboard.html",
        total_motoristas=total_motoristas,
        vistorias_mes=vistorias_mes,
        pendentes=pendentes,
        atrasados=atrasados,
        motoristas=listar_motoristas(),
        proxima_por_motorista={m["id"]: db.proxima_vistoria(m["id"]) for m in listar_motoristas()},
        ultima_por_motorista=ultima_por_motorista,
        hoje=hoje_str(),
        fmt=fmt,
        mes_atual=f"{hoje.year:04d}-{hoje.month:02d}",
    )


# ---- controle mensal de fotos --------------------------------------

@app.route("/admin/mes/<ano>/<int:mes>")
@admin_obrigatorio
def admin_mes(ano, mes):
    vistorias = vistorias_por_mes(int(ano), mes)
    return render_template(
        "admin_mes.html",
        vistorias=vistorias,
        ano=int(ano), mes=mes,
        fmt=fmt,
        categorias=dict((c[0], c[1]) for c in db.CATEGORIAS),
    )


# ---- detalhe de uma vistoria (todas as fotos) ---------------------

@app.route("/admin/vistoria/<int:vistoria_id>")
@admin_obrigatorio
def admin_vistoria(vistoria_id):
    conn = db.get_connection()
    v = conn.execute(
        """
        SELECT v.*, m.nome AS motorista_nome, m.veiculo, m.placa, m.cor, m.fone
        FROM vistorias v JOIN motoristas m ON m.id = v.motorista_id
        WHERE v.id = ?
        """,
        (vistoria_id,),
    ).fetchone()
    fotos = conn.execute(
        "SELECT * FROM fotos WHERE vistoria_id = ? ORDER BY categoria",
        (vistoria_id,),
    ).fetchall()
    conn.close()
    if not v:
        abort(404)
    return render_template(
        "admin_vistoria.html",
        v=v, fotos=fotos,
        categorias=dict((c[0], (c[1], c[2])) for c in db.CATEGORIAS),
        fmt=fmt,
    )


# ---- aprovar / rejeitar --------------------------------------------

@app.route("/admin/vistoria/<int:vistoria_id>/status", methods=["POST"])
@admin_obrigatorio
def admin_status(vistoria_id):
    status = request.form.get("status")
    nota = request.form.get("nota_admin", "").strip()
    if status not in ("aprovada", "rejeitada", "pendente"):
        status = "pendente"
    conn = db.get_connection()
    conn.execute(
        "UPDATE vistorias SET status = ?, nota_admin = ? WHERE id = ?",
        (status, nota, vistoria_id),
    )
    conn.commit()
    conn.close()
    flash(f"Vistoria #{vistoria_id} marcada como {status}.", "sucesso")
    return redirect(url_for("admin_vistoria", vistoria_id=vistoria_id))


# ---- cadastro de motoristas ----------------------------------------

@app.route("/admin/motoristas/novo", methods=["POST"])
@admin_obrigatorio
def admin_motorista_novo():
    nome = request.form.get("nome", "").strip()
    veiculo = request.form.get("veiculo", "").strip()
    placa = request.form.get("placa", "").strip()
    if not nome or not placa:
        flash("Nome e placa são obrigatórios.", "erro")
        return redirect(url_for("admin_dashboard"))
    conn = db.get_connection()
    try:
        conn.execute(
            "INSERT INTO motoristas (nome, cpf, fone, veiculo, placa, cor, ativo) VALUES (?,?,?,?,?,?,1)",
            (
                nome, request.form.get("cpf", "").strip(), request.form.get("fone", "").strip(),
                veiculo, placa, request.form.get("cor", "").strip(),
            ),
        )
        conn.commit()
        flash(f"Motorista {nome} cadastrado.", "sucesso")
    except Exception:
        flash("Já existe um veículo com essa placa.", "erro")
    finally:
        conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/motoristas/<int:motorista_id>/toggle", methods=["POST"])
@admin_obrigatorio
def admin_motorista_toggle(motorista_id):
    conn = db.get_connection()
    m = conn.execute("SELECT ativo FROM motoristas WHERE id = ?", (motorista_id,)).fetchone()
    if m:
        conn.execute(
            "UPDATE motoristas SET ativo = ? WHERE id = ?",
            (0 if m["ativo"] else 1, motorista_id),
        )
        conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


# ---- alterar senha do administrador ---------------------------

@app.route("/admin/senha", methods=["POST"])
@admin_obrigatorio
def admin_senha_trocar():
    atual = request.form.get("senha_atual", "")
    nova = request.form.get("senha_nova", "").strip()
    if atual != admin_senha():
        flash("Senha atual incorreta.", "erro")
        return redirect(url_for("admin_dashboard"))
    if len(nova) < 4:
        flash("A nova senha precisa ter pelo menos 4 caracteres.", "erro")
        return redirect(url_for("admin_dashboard"))
    db.set_config("admin_senha", nova)
    flash("Senha do administrador alterada.", "sucesso")
    return redirect(url_for("admin_dashboard"))

# ---- importar dados do sistema anterior -----------------------------

@app.route("/admin/importar", methods=["POST"])
@admin_obrigatorio
def admin_importar():
    caminho = request.form.get("caminho_json", "").strip()
    if not caminho or not os.path.exists(caminho):
        flash("Arquivo JSON não encontrado.", "erro")
        return redirect(url_for("admin_dashboard"))
    try:
        from seed_data import importar as _importar
        import contextlib, io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            _importar(caminho)
        flash("Importação concluída.<br><pre>" + buf.getvalue() + "</pre>", "sucesso")
    except Exception as e:
        flash(f"Erro na importação: {e}", "erro")
    return redirect(url_for("admin_dashboard"))


# ----------------------------------------------------------------------
# Servir fotos e miniaturas
# ----------------------------------------------------------------------

@app.route("/fotos/<path:subpath>")
@admin_obrigatorio
def servir_foto(subpath):
    """Fotos originais só são acessíveis na área do administrador."""
    return send_from_directory(FOTOS_DIR, subpath)


@app.route("/thumbs/<path:filename>")
@admin_obrigatorio
def servir_thumb(filename):
    return send_from_directory(THUMBS_DIR, filename)


# ----------------------------------------------------------------------
if __name__ == "__main__":
    # debug=False: o reloader do Flask reinicia em loop quando o OneDrive
    # toca os arquivos da pasta. Para servir atras do tunel cloudflared,
    # o modo estavel (sem reloader) e o correreto.
    app.run(host="0.0.0.0", port=5000)
