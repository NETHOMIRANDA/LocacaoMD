"""
Locação MD – Vistorias
Gera o conjunto de fotos de exemplo (static/exemplos/*.jpg) com IA,
TODAS DO MESMO MODELO DE CARRO, a partir de uma foto "mestre".

Fluxo:
  1. Gera a foto mestre (externo_frente) via gpt-image-1.
  2. Cada uma das outras 13 categorias é gerada POR EDIÇÃO da mestre,
     assim o carro (modelo, cor, rodas) é o mesmo em todas as fotos.
  3. Salva o original em _orig_ia/ e uma versão redimensionada (max 1200px)
     como <chave>.jpg na pasta de saída.

Requer:  pip install openai pillow
         set OPENAI_API_KEY=sk-...   (Windows)

Uso:
  python gerar_exemplos_ia.py                     # gera as 14 (retoma o que faltar)
  python gerar_exemplos_ia.py --forcar            # regera tudo do zero
  python gerar_exemplos_ia.py --cor prata --ano 2024
  python gerar_exemplos_ia.py --saida "static/exemplos/hyundai-creta"
       ^ pasta por modelo: o app usa essa pasta quando ela existe,
         senão usa a raiz de static/exemplos (conjunto padrão).
  python gerar_exemplos_ia.py --dry-run           # só mostra os prompts

Custo estimado: ~US$ 0,80 para as 15 chamadas (gpt-image-1, quality=medium).
"""
import argparse
import base64
import datetime
import io
import json
import sys
import time
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta a Pillow. Instale com:  pip install pillow")

# O SDK da OpenAI só é exigido quando vamos chamar a API
# (o --dry-run funciona sem ele).
OpenAI = RateLimitError = APIStatusError = APIConnectionError = None
try:
    from openai import OpenAI, RateLimitError, APIStatusError, APIConnectionError  # noqa: F811
except ImportError:
    pass

# ----------------------------------------------------------------------
# Configuração (edite aqui ou use os argumentos)
# ----------------------------------------------------------------------
MODELO_CARRO = "Hyundai Creta"
COR = "branco"
ANO = "2023"
MODELO_IA = "gpt-image-1"
TAMANHO = "1536x1024"
QUALIDADE = "medium"
MAX_LADO = 1200

# ----------------------------------------------------------------------
# Prompts: a "âncora" (carro igual) é repetida em todos para o modelo
# de IA manter o mesmo veículo em cada ângulo.
# ----------------------------------------------------------------------
def ancora(modelo=MODELO_CARRO, cor=COR, ano=ANO):
    return (
        f"O MESMO carro de referência: {ano} {modelo} {cor}, SUV compacto, "
        "mesma cor, mesmos faróis, mesmas rodas de liga leve, mesmo para-choque, "
        "placa brasileira genérica ilegível"
    )

PROMPTS = {
    "externo_frente": (
        "Foto realista de um {ano} {modelo} {cor} (SUV compacto), vista frontal "
        "à altura do peito, a cerca de 3 metros: veículo inteiro enquadrado, as duas "
        "rodas dianteiras visíveis, placa dianteira visível, dia claro com luz natural "
        "suave, sem flash, sem contraluz, fundo de rua neutro, sem distorção, "
        "estilo foto de vistoria veicular"
    ),
    "externo_traseira": (
        "{ancora}, agora fotografado pela traseira, a cerca de 3 metros: toda a traseira "
        "enquadrada com lanternas, para-choque e placa traseira visíveis, porta-malas "
        "fechado, dia claro, luz natural suave, estilo foto de vistoria veicular"
    ),
    "externo_lado_esq": (
        "{ancora}, agora em vista de perfil do LADO ESQUERDO, a cerca de 4 metros: carro "
        "inteiro de lado mostrando portas, para-lamas, roda e retrovisor, sem distorção "
        "de ângulo, dia claro, luz natural suave, estilo foto de vistoria veicular"
    ),
    "externo_lado_dir": (
        "{ancora}, agora em vista de perfil do LADO DIREITO, a cerca de 4 metros: carro "
        "inteiro de lado mostrando portas, para-lamas, roda e retrovisor, sem distorção "
        "de ângulo, dia claro, luz natural suave, estilo foto de vistoria veicular"
    ),
    "pneu_dianteiro_esq": (
        "{ancora}, agora um CLOSE do pneu dianteiro esquerdo: banda de rodagem e lateral "
        "do pneu inteiras visíveis e o aro, câmera na altura do pneu (não de cima), "
        "dia claro, estilo foto de vistoria veicular"
    ),
    "pneu_dianteiro_dir": (
        "{ancora}, agora um CLOSE do pneu dianteiro direito: banda de rodagem e lateral "
        "do pneu inteiras visíveis e o aro, câmera na altura do pneu (não de cima), "
        "dia claro, estilo foto de vistoria veicular"
    ),
    "pneu_traseiro_esq": (
        "{ancora}, agora um CLOSE do pneu traseiro esquerdo: banda de rodagem e lateral "
        "do pneu inteiras visíveis e o aro, câmera na altura do pneu (não de cima), "
        "dia claro, estilo foto de vistoria veicular"
    ),
    "pneu_traseiro_dir": (
        "{ancora}, agora um CLOSE do pneu traseiro direito: banda de rodagem e lateral "
        "do pneu inteiras visíveis e o aro, câmera na altura do pneu (não de cima), "
        "dia claro, estilo foto de vistoria veicular"
    ),
    "interno_bancos": (
        "{ancora}, agora o INTERIOR visto a partir do banco do motorista: bancos "
        "dianteiros e traseiros com estofamento e encostos visíveis, dia claro, "
        "luz natural entrando pelo para-brisa, estilo foto de vistoria veicular"
    ),
    "interno_porta_malas": (
        "{ancora}, agora o PORTA-MALAS ABERTO E VAZIO: interior do porta-malas inteiro "
        "visível (lataria, estepe se houver), dia claro, estilo foto de vistoria veicular"
    ),
    "interno_teto": (
        "{ancora}, agora o forro do TETO e as laterais superiores do interior, vistos "
        "de dentro do carro, dia claro, estilo foto de vistoria veicular"
    ),
    "interno_piso": (
        "{ancora}, agora o PISO e o carpete do interior com os tapetes visíveis, vistos "
        "de dentro do carro, dia claro, estilo foto de vistoria veicular"
    ),
    "painel": (
        "{ancora}, agora o PAINEL visto do banco do motorista: volante, painel e "
        "velocímetro/hodômetro visíveis, dia claro, estilo foto de vistoria veicular"
    ),
    "motor": (
        "{ancora}, agora o COMPARTIMENTO DO MOTOR com o capô aberto e apoiado: motor e "
        "compartimentos laterais visíveis, dia claro, estilo foto de vistoria veicular"
    ),
}

ORDEM = [
    "externo_frente", "externo_traseira", "externo_lado_esq", "externo_lado_dir",
    "pneu_dianteiro_esq", "pneu_dianteiro_dir", "pneu_traseiro_esq",
    "pneu_traseiro_dir", "interno_bancos", "interno_porta_malas", "interno_teto",
    "interno_piso", "painel", "motor",
]

CHAVE_MESTRE = "externo_frente"


def montar_prompts(modelo, cor, ano):
    """Renderiza os prompts com a âncora do mesmo carro."""
    a = ancora(modelo, cor, ano)
    prontos = {}
    for chave, molde in PROMPTS.items():
        prontos[chave] = molde.format(ano=ano, modelo=modelo, cor=cor, ancora=a)
    return prontos


def extrair_bytes(resp):
    """gpt-image-1 devolve b64_json (às vezes url). Sempre retorna bytes."""
    item = resp.data[0]
    if getattr(item, "b64_json", None):
        return base64.b64decode(item.b64_json)
    if getattr(item, "url", None):
        import urllib.request
        with urllib.request.urlopen(item.url, timeout=60) as r:
            return r.read()
    raise RuntimeError("resposta sem imagem (sem b64_json nem url)")


def salvar_imagem(dados, pasta: Path, chave, max_lado=MAX_LADO):
    """Salva o original em _orig_ia/ e o JPG redimensionado em pasta/."""
    orig = pasta / "_orig_ia" / f"{chave}.png"
    orig.parent.mkdir(parents=True, exist_ok=True)
    orig.write_bytes(dados)

    img = Image.open(io.BytesIO(dados))
    if img.mode != "RGB":
        img = img.convert("RGB")
    w, h = img.size
    if max(w, h) > max_lado:
        f = max_lado / max(w, h)
        img = img.resize((max(1, int(w * f)), max(1, int(h * f))), Image.LANCZOS)
    destino = pasta / f"{chave}.jpg"
    img.save(destino, "JPEG", quality=88)
    return destino, (w, h)


def chamar_com_retry(fn, tentativas=5):
    """Chama a API com espera progressiva em erros temporários."""
    for i in range(tentativas):
        try:
            return fn()
        except RateLimitError:
            espera = 20 * (i + 1)
            print(f"    ⏳ limite de taxa — aguardando {espera}s")
            time.sleep(espera)
        except APIConnectionError as e:
            espera = 10 * (i + 1)
            print(f"    ⏳ rede: {str(e)[:100]} — aguardando {espera}s")
            time.sleep(espera)
        except APIStatusError as e:
            if e.status_code >= 500:
                espera = 15 * (i + 1)
                print(f"    ⏳ servidor {e.status_code} — aguardando {espera}s")
                time.sleep(espera)
            else:
                raise
    raise RuntimeError("falhou após várias tentativas")


def main():
    ap = argparse.ArgumentParser(description="Gera as fotos de exemplo do LocacaoMD com IA")
    ap.add_argument("--modelo", default=MODELO_CARRO, help="modelo do carro (ex.: 'Hyundai Creta')")
    ap.add_argument("--cor", default=COR, help="cor do carro (ex.: branco, prata, preto)")
    ap.add_argument("--ano", default=ANO, help="ano do carro (ex.: 2023)")
    ap.add_argument("--saida", default="static/exemplos",
                    help="pasta de saída (raiz ou static/exemplos/<modelo>)")
    ap.add_argument("--modelo-ia", default=MODELO_IA)
    ap.add_argument("--tamanho", default=TAMANHO, choices=["1024x1024", "1536x1024", "1024x1536"])
    ap.add_argument("--qualidade", default=QUALIDADE, choices=["low", "medium", "high"])
    ap.add_argument("--forcar", action="store_true", help="regera tudo, mesmo o que já existe")
    ap.add_argument("--dry-run", action="store_true", help="só mostra os prompts, sem chamar a API")
    args = ap.parse_args()

    prompts = montar_prompts(args.modelo, args.cor, args.ano)

    if args.dry_run:
        print("=== DRY-RUN: prompts que serão usados ===\n")
        for chave in ORDEM:
            print(f"[{chave}]\n{prompts[chave]}\n")
        return

    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("Defina a variável de ambiente OPENAI_API_KEY antes de rodar.\n"
                 "  set OPENAI_API_KEY=sk-...   (Windows)")

    if OpenAI is None:
        sys.exit("Falta o SDK da OpenAI. Instale com:  pip install openai")

    pasta = Path(args.saida)
    pasta.mkdir(parents=True, exist_ok=True)
    client = OpenAI()

    n_faltantes = sum(1 for c in ORDEM if args.forcar or not (pasta / f"{c}.jpg").exists())
    estimativa = n_faltantes * {"low": 0.019, "medium": 0.053, "high": 0.167}[args.qualidade]
    print(f"Modelo do carro: {args.ano} {args.modelo} {args.cor}")
    print(f"Pasta de saída: {pasta.resolve()}")
    print(f"Fotos a gerar: {n_faltantes}  (custo estimado ≈ US$ {estimativa:.2f})\n")

    if input("Continuar? [s/N] ").strip().lower() not in ("s", "sim"):
        print("Abortado.")
        return

    creditos_path = pasta / "_creditos_ia.json"
    creditos = json.loads(creditos_path.read_text(encoding="utf-8")) if creditos_path.exists() else []

    # --- 1. Foto mestre -------------------------------------------------
    mestre_png = pasta / "_orig_ia" / f"{CHAVE_MESTRE}.png"
    if args.forcar or not (pasta / f"{CHAVE_MESTRE}.jpg").exists() or not mestre_png.exists():
        print(f"\n① Gerando a FOTO MESTRE ({CHAVE_MESTRE})...")
        resp = chamar_com_retry(lambda: client.images.generate(
            model=args.modelo_ia,
            prompt=prompts[CHAVE_MESTRE],
            size=args.tamanho,
            quality=args.qualidade,
            n=1,
        ))
        mestre = extrair_bytes(resp)
        destino, original = salvar_imagem(mestre, pasta, CHAVE_MESTRE)
        print(f"   ✔ salvo: {destino} (original {original[0]}x{original[1]})")
        creditos.append(registro(CHAVE_MESTRE, prompts[CHAVE_MESTRE], args, "geração", original))
    else:
        mestre = mestre_png.read_bytes()
        print(f"① Foto mestre já existe: {mestre_png}")

    # --- 2. As outras 13, por edição da mestre --------------------------
    for chave in ORDEM:
        if chave == CHAVE_MESTRE:
            continue
        destino_jpg = pasta / f"{chave}.jpg"
        if not args.forcar and destino_jpg.exists():
            print(f"✔ {chave}: já existe (use --forcar para refazer)")
            continue
        print(f"\n② Gerando {chave} (edição da mestre)...")
        # BytesIO é consumido pela requisição: crie um novo a cada tentativa
        resp = chamar_com_retry(lambda: client.images.edit(
            model=args.modelo_ia,
            image=("master.png", io.BytesIO(mestre), "image/png"),
            prompt=prompts[chave],
            size=args.tamanho,
            quality=args.qualidade,
            n=1,
        ))
        dados = extrair_bytes(resp)
        destino, original = salvar_imagem(dados, pasta, chave)
        print(f"   ✔ salvo: {destino} (original {original[0]}x{original[1]})")
        creditos.append(registro(chave, prompts[chave], args, "edição da mestre", original))

    creditos_path.write_text(json.dumps(creditos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ Concluído. Metadados em: {creditos_path}")


def registro(chave, prompt, args, metodo, original):
    return {
        "arquivo": f"{chave}.jpg",
        "modelo_carro": f"{args.ano} {args.modelo} {args.cor}",
        "modelo_ia": args.modelo_ia,
        "metodo": metodo,
        "tamanho_gerado": f"{args.tamanho} / {args.qualidade}",
        "resolucao_original": f"{original[0]}x{original[1]}",
        "gerado_em": datetime.datetime.now().isoformat(timespec="seconds"),
        "prompt": prompt,
        "licenca": "Gerado por IA (OpenAI) — uso interno Locação MD",
    }


if __name__ == "__main__":
    main()
