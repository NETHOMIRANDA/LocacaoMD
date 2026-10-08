"""
Gera as imagens ilustrativas de como tirar cada foto da vistoria.
Saída: static/exemplos/<categoria>.png
"""
import math
import os

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(BASE, "static", "exemplos")
os.makedirs(SAIDA, exist_ok=True)

W, H = 800, 460
CEU = (186, 225, 245)
CHAO = (148, 163, 184)
GRAMA = (134, 200, 140)
AZUL = (37, 99, 235)
VERDE = (16, 185, 129)
AMARELO = (245, 158, 11)


def fonte(tamanho=20, negrito=True):
    caminhos = [
        r"C:\Windows\Fonts\msbd.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for c in caminhos:
        if os.path.exists(c):
            return ImageFont.truetype(c, tamanho)
    return ImageFont.load_default()


def base(titulo, subtitulo):
    img = Image.new("RGB", (W, H), CEU)
    d = ImageDraw.Draw(img)
    # sol
    d.ellipse([W - 120, 20, W - 60, 80], fill=(253, 224, 71))
    # grama e chão
    d.rectangle([0, H - 70, W, H - 40], fill=GRAMA)
    d.rectangle([0, H - 40, W, H], fill=CHAO)
    # faixa de título
    d.rectangle([0, 0, W, 64], fill=(15, 23, 42))
    d.text((20, 10), titulo, font=fonte(24), fill=(248, 250, 252))
    d.text((20, 38), subtitulo, font=fonte(15, negrito=False), fill=(148, 163, 184))
    return img, d


def seta(d, x1, y1, x2, y2, cor=VERDE, largura=6):
    d.line([x1, y1, x2, y2], fill=cor, width=largura)
    ang = math.atan2(y2 - y1, x2 - x1)
    for a in (ang + math.radians(150), ang - math.radians(150)):
        d.line([x2, y2, x2 + 26 * math.cos(a), y2 + 26 * math.sin(a)],
               fill=cor, width=largura)


def camera(d, cx, cy, s=1.0):
    d.rounded_rectangle([cx - 16 * s, cy - 11 * s, cx + 16 * s, cy + 11 * s],
                        radius=6 * s, fill=(17, 24, 39))
    d.ellipse([cx - 7 * s, cy - 6 * s, cx + 7 * s, cy + 6 * s], fill=AZUL)
    d.rectangle([cx + 16 * s, cy - 8 * s, cx + 23 * s, cy - 2 * s], fill=AMARELO)


def roda(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(31, 41, 55))
    d.ellipse([cx - r * .55, cy - r * .55, cx + r * .55, cy + r * .55],
              fill=(156, 163, 175))
    d.ellipse([cx - r * .16, cy - r * .16, cx + r * .16, cy + r * .16],
              fill=(75, 85, 99))


def carro_lado(d, x, y, s, cor):
    d.rounded_rectangle([x, y + 40 * s, x + 200 * s, y + 108 * s],
                        radius=14 * s, fill=cor)
    d.polygon([(x + 48 * s, y + 42 * s), (x + 68 * s, y + 4 * s),
               (x + 138 * s, y + 4 * s), (x + 158 * s, y + 42 * s)], fill=cor)
    d.polygon([(x + 56 * s, y + 40 * s), (x + 72 * s, y + 10 * s),
               (x + 94 * s, y + 10 * s), (x + 94 * s, y + 40 * s)], fill=(191, 227, 248))
    d.polygon([(x + 102 * s, y + 10 * s), (x + 136 * s, y + 10 * s),
               (x + 152 * s, y + 40 * s), (x + 102 * s, y + 40 * s)], fill=(191, 227, 248))
    d.ellipse([x + 6 * s, y + 72 * s, x + 22 * s, y + 88 * s], fill=(253, 224, 71))
    d.ellipse([x + 182 * s, y + 72 * s, x + 198 * s, y + 88 * s], fill=(239, 68, 68))
    roda(d, x + 54 * s, y + 108 * s, 22 * s)
    roda(d, x + 150 * s, y + 108 * s, 22 * s)


def carro_frente(d, x, y, s, cor):
    d.rounded_rectangle([x, y + 34 * s, x + 150 * s, y + 118 * s],
                        radius=22 * s, fill=cor)
    d.rounded_rectangle([x + 18 * s, y + 8 * s, x + 132 * s, y + 52 * s],
                        radius=12 * s, fill=(191, 227, 248))
    d.ellipse([x + 4 * s, y + 58 * s, x + 32 * s, y + 80 * s], fill=(253, 224, 71))
    d.ellipse([x + 118 * s, y + 58 * s, x + 146 * s, y + 80 * s], fill=(253, 224, 71))
    d.rectangle([x + 48 * s, y + 62 * s, x + 102 * s, y + 100 * s], fill=(51, 65, 85))
    d.rectangle([x + 62 * s, y + 70 * s, x + 88 * s, y + 76 * s], fill=(148, 163, 184))
    d.rectangle([x - 6 * s, y + 92 * s, x + 16 * s, y + 126 * s], fill=(31, 41, 55))
    d.rectangle([x + 134 * s, y + 92 * s, x + 156 * s, y + 126 * s], fill=(31, 41, 55))


def carro_traseira(d, x, y, s, cor):
    d.rounded_rectangle([x, y + 34 * s, x + 150 * s, y + 118 * s],
                        radius=22 * s, fill=cor)
    d.rounded_rectangle([x + 18 * s, y + 8 * s, x + 132 * s, y + 50 * s],
                        radius=12 * s, fill=(191, 227, 248))
    d.rectangle([x + 6 * s, y + 60 * s, x + 26 * s, y + 76 * s], fill=(239, 68, 68))
    d.rectangle([x + 124 * s, y + 60 * s, x + 144 * s, y + 76 * s], fill=(239, 68, 68))
    d.rectangle([x + 52 * s, y + 62 * s, x + 98 * s, y + 96 * s], fill=(51, 65, 85))
    d.rectangle([x + 60 * s, y + 70 * s, x + 90 * s, y + 76 * s], fill=(148, 163, 184))
    d.rectangle([x - 6 * s, y + 92 * s, x + 16 * s, y + 126 * s], fill=(31, 41, 55))
    d.rectangle([x + 134 * s, y + 92 * s, x + 156 * s, y + 126 * s], fill=(31, 41, 55))


def banco(d, cx, cy, s, cor=(120, 72, 40)):
    d.rounded_rectangle([cx - 34 * s, cy - 70 * s, cx + 34 * s, cy + 10 * s],
                        radius=12 * s, fill=cor)
    d.rounded_rectangle([cx - 44 * s, cy + 6 * s, cx + 44 * s, cy + 34 * s],
                        radius=10 * s, fill=tuple(min(255, c + 25) for c in cor))
    d.line([cx, cy - 70 * s, cx, cy + 10 * s], fill=(90, 54, 30), width=int(3 * s))


def volante(d, cx, cy, s):
    d.ellipse([cx - 40 * s, cy - 40 * s, cx + 40 * s, cy + 40 * s],
              outline=(31, 41, 55), width=int(10 * s))
    d.ellipse([cx - 8 * s, cy - 8 * s, cx + 8 * s, cy + 8 * s], fill=(31, 41, 55))
    d.line([cx, cy, cx, cy + 38 * s], fill=(31, 41, 55), width=int(8 * s))


def velocimetro(d, cx, cy, s):
    d.ellipse([cx - 46 * s, cy - 46 * s, cx + 46 * s, cy + 46 * s],
              fill=(229, 231, 235), outline=(31, 41, 55), width=int(6 * s))
    for i in range(9):
        a = math.radians(135 + i * 45)
        d.line([cx + 34 * s * math.cos(a), cy + 34 * s * math.sin(a),
                cx + 42 * s * math.cos(a), cy + 42 * s * math.sin(a)],
               fill=(31, 41, 55), width=int(3 * s))
    a = math.radians(200)
    d.line([cx, cy, cx + 32 * s * math.cos(a), cy + 32 * s * math.sin(a)],
           fill=(239, 68, 68), width=int(5 * s))


def painel_completo(d, x, y, s):
    d.rounded_rectangle([x, y, x + 380 * s, y + 90 * s], radius=14 * s,
                        fill=(51, 65, 85))
    d.rounded_rectangle([x + 14 * s, y + 10 * s, x + 180 * s, y + 80 * s],
                        radius=10 * s, fill=(31, 41, 55))
    velocimetro(d, x + 96 * s, y + 45 * s, .75 * s)
    d.rounded_rectangle([x + 200 * s, y + 14 * s, x + 250 * s, y + 76 * s],
                        radius=8 * s, fill=(17, 24, 39))
    d.rounded_rectangle([x + 262 * s, y + 14 * s, x + 312 * s, y + 76 * s],
                        radius=8 * s, fill=(17, 24, 39))
    d.rounded_rectangle([x + 324 * s, y + 14 * s, x + 366 * s, y + 76 * s],
                        radius=8 * s, fill=(17, 24, 39))
    d.ellipse([x + 330 * s, y + 20 * s, x + 360 * s, y + 50 * s], fill=(74, 222, 128))


def motor_bay(d, x, y, s):
    d.rounded_rectangle([x, y, x + 420 * s, y + 130 * s], radius=12 * s,
                        fill=(226, 232, 240))
    d.rectangle([x + 20 * s, y + 20 * s, x + 120 * s, y + 70 * s], fill=(37, 99, 235))
    d.text((x + 34 * s, y + 38 * s), "BATERIA", font=fonte(14), fill=(255, 255, 255))
    d.rounded_rectangle([x + 150 * s, y + 16 * s, x + 240 * s, y + 60 * s],
                        radius=8 * s, fill=(156, 163, 175))
    d.text((x + 162 * s, y + 32 * s), "MOTOR", font=fonte(14), fill=(31, 41, 55))
    d.ellipse([x + 270 * s, y + 24 * s, x + 330 * s, y + 84 * s],
              fill=(203, 213, 225), outline=(100, 116, 139), width=int(4 * s))
    for i in range(4):
        d.arc([x + 30 * s + i * 90 * s, y + 84 * s, x + 100 * s + i * 90 * s,
               y + 130 * s], 0, 180, fill=(100, 116, 139), width=int(4 * s))
    d.rectangle([x + 350 * s, y + 20 * s, x + 400 * s, y + 110 * s], fill=(245, 158, 11))
    d.text((x + 352 * s, y + 60 * s), "OLEO", font=fonte(12), fill=(31, 41, 55))


def tapete(d, x, y, s):
    d.rounded_rectangle([x, y, x + 420 * s, y + 150 * s], radius=10 * s,
                        fill=(75, 85, 99))
    for i in range(1, 4):
        d.line([x, y + i * 36 * s, x + 420 * s, y + i * 36 * s],
               fill=(107, 114, 128), width=int(3 * s))
    for i in range(1, 6):
        d.line([x + i * 66 * s, y, x + i * 66 * s, y + 150 * s],
               fill=(107, 114, 128), width=int(2 * s))
    d.text((x + 150 * s, y + 62 * s), "PISO / CARPETE", font=fonte(18),
           fill=(209, 213, 219))


def teto(d, x, y, s):
    d.rounded_rectangle([x, y, x + 420 * s, y + 150 * s], radius=60 * s,
                        fill=(100, 116, 139))
    d.rounded_rectangle([x + 40 * s, y + 30 * s, x + 380 * s, y + 120 * s],
                        radius=40 * s, fill=(148, 163, 184))
    d.text((x + 120 * s, y + 66 * s), "TETO / FORRAÇÃO", font=fonte(18),
           fill=(31, 41, 55))


def porta_malas(d, x, y, s):
    d.rounded_rectangle([x, y + 40 * s, x + 420 * s, y + 150 * s], radius=14 * s,
                        fill=(51, 65, 85))
    d.polygon([(x + 20 * s, y + 44 * s), (x + 60 * s, y - 20 * s),
               (x + 380 * s, y - 20 * s), (x + 400 * s, y + 44 * s)],
              fill=(71, 85, 105))
    d.rectangle([x + 30 * s, y + 56 * s, x + 390 * s, y + 138 * s], fill=(31, 41, 55))
    d.text((x + 130 * s, y + 88 * s), "PORTA-MALAS VAZIO", font=fonte(18),
           fill=(209, 213, 219))


def salvar(img, nome):
    img.save(os.path.join(SAIDA, nome + ".png"))
    print("OK:", nome + ".png")


# ------------------------------------------------------------------
# 1. Externo – frente
img, d = base("Externo – FRENTE", "Tire de frente para o carro, em local claro e de dia")
carro_frente(d, 300, 150, 1.7, (37, 99, 235))
camera(d, 400, 395, 1.3)
seta(d, 400, 360, 400, 330)
d.text((330, 415), "📷 você fica aqui, de frente", font=fonte(16), fill=(21, 128, 61))
salvar(img, "externo_frente")

# 2. Externo – traseira
img, d = base("Externo – TRASEIRA", "Tire de trás para o carro, mostrando a traseira inteira")
carro_traseira(d, 300, 150, 1.7, (37, 99, 235))
camera(d, 400, 395, 1.3)
seta(d, 400, 360, 400, 330)
d.text((330, 415), "📷 você fica atrás do carro", font=fonte(16), fill=(21, 128, 61))
salvar(img, "externo_traseira")

# 3. Externo – lado esquerdo
img, d = base("Externo – LADO ESQUERDO", "Tire de lado, vendo o carro inteiro pela lateral esquerda")
carro_lado(d, 180, 170, 1.9, (37, 99, 235))
camera(d, 120, 395, 1.3)
seta(d, 140, 360, 200, 320)
d.text((60, 415), "📷 fique ao lado esquerdo", font=fonte(16), fill=(21, 128, 61))
salvar(img, "externo_lado_esq")

# 4. Externo – lado direito
img, d = base("Externo – LADO DIREITO", "Tire de lado, vendo o carro inteiro pela lateral direita")
carro_lado(d, 180, 170, 1.9, (220, 38, 38))
camera(d, 680, 395, 1.3)
seta(d, 660, 360, 600, 320)
d.text((520, 415), "📷 fique ao lado direito", font=fonte(16), fill=(21, 128, 61))
salvar(img, "externo_lado_dir")

# 5-8. Pneus
PNEUS = [
    ("pneu_dianteiro_esq", "Pneu DIANTEIRO ESQUERDO", "Foto de perto, só do pneu dianteiro esquerdo", (152, 254), "LADO ESQUERDO"),
    ("pneu_dianteiro_dir", "Pneu DIANTEIRO DIREITO", "Foto de perto, só do pneu dianteiro direito", (152, 254), "LADO DIREITO"),
    ("pneu_traseiro_esq", "Pneu TRASEIRO ESQUERDO", "Foto de perto, só do pneu traseiro esquerdo", (262, 254), "LADO ESQUERDO"),
    ("pneu_traseiro_dir", "Pneu TRASEIRO DIREITO", "Foto de perto, só do pneu traseiro direito", (262, 254), "LADO DIREITO"),
]
for chave, titulo, sub, alvo, lado in PNEUS:
    img, d = base(titulo, sub)
    # carro visto de cima com as 4 rodas marcadas
    carro_lado(d, 90, 130, 1.15, (100, 116, 139))
    cx, cy = alvo
    d.ellipse([cx - 34, cy - 34, cx + 34, cy + 34], outline=VERDE, width=6)
    seta(d, cx - 70, cy - 80, cx - 28, cy - 30, cor=VERDE, largura=5)
    d.text((cx - 130, cy - 110), "ESTE!", font=fonte(18), fill=(21, 128, 61))
    d.text((100, 118), ">>> " + lado + " <<<", font=fonte(16), fill=(30, 64, 175))
    # close-up do pneu
    roda(d, 620, 300, 95)
    d.text((500, 415), "📷 foto de perto, só o pneu", font=fonte(16),
           fill=(21, 128, 61))
    salvar(img, chave)

# 9. Interno – bancos
img, d = base("Interno – BANCOS", "De dentro do carro, mostrando os bancos dianteiros e traseiros")
d.rectangle([0, 64, W, H], fill=(120, 72, 40))
banco(d, 220, 260, 1.6)
banco(d, 560, 260, 1.6)
d.text((250, 400), "📷 de dentro, olhando os bancos", font=fonte(16),
       fill=(255, 255, 255))
salvar(img, "interno_bancos")

# 10. Interno – porta-malas
img, d = base("Interno – PORTA-MALAS", "Porta-malas aberto, mostrando se está vazio ou com algo dentro")
d.rectangle([0, 64, W, H], fill=(51, 65, 85))
porta_malas(d, 190, 240, 1.4)
d.text((220, 420), "📷 porta-malas aberto", font=fonte(16), fill=(255, 255, 255))
salvar(img, "interno_porta_malas")

# 11. Interno – teto
img, d = base("Interno – TETO", "De dentro, olhando para o teto e forrações")
d.rectangle([0, 64, W, H], fill=(71, 85, 105))
teto(d, 190, 150, 1.4)
d.text((250, 400), "📷 olhe para cima, dentro do carro", font=fonte(16),
       fill=(255, 255, 255))
salvar(img, "interno_teto")

# 12. Interno – pisos
img, d = base("Interno – PISOS", "Piso / carpete do carro (dianteiro e traseiro)")
d.rectangle([0, 64, W, H], fill=(71, 85, 105))
tapete(d, 190, 150, 1.4)
d.text((260, 400), "📷 chão do carro", font=fonte(16), fill=(255, 255, 255))
salvar(img, "interno_piso")

# 13. Painel
img, d = base("Painel", "Foto do painel com o velocímetro (carro ligado, de dia)")
d.rectangle([0, 64, W, H], fill=(31, 41, 55))
painel_completo(d, 210, 130, 1.5)
volante(d, 210, 330, 1.2)
d.text((240, 420), "📷 foto do painel por dentro", font=fonte(16),
       fill=(255, 255, 255))
salvar(img, "painel")

# 14. Motor
img, d = base("Motor", "Capô aberto, motor visível, em local claro e de dia")
d.rectangle([0, 64, W, H], fill=(226, 232, 240))
motor_bay(d, 190, 140, 1.5)
camera(d, 400, 400, 1.3)
d.text((250, 430), "📷 capô aberto, de dia", font=fonte(16), fill=(21, 128, 61))
salvar(img, "motor")

print("\nImagens ilustrativas criadas em static/exemplos/")
