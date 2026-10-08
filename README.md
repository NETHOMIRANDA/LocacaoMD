# Locação MD – Vistorias

Aplicativo de controle de vistorias de veículos para **Locação MD**.
O motorista registra a condição física do carro com fotos; o administrador
revisa e controla tudo mensalmente.

## O que o motorista faz
- Entra com seu nome na tela inicial e abre o painel do seu veículo.
- Vê, em destaque, **o dia em que deve fazer a nova vistoria (30 dias)** após a última.
- Registra uma vistoria informando:
  - Km atual
  - Fotos de **todos os ângulos externos** (frente, traseira, lado esq., lado dir.)
  - Fotos dos **4 pneus separadamente**
  - Fotos do **interior**: bancos, porta-malas, teto e piso
  - Foto do **painel**
  - Foto do **motor**
  - Confirma que as fotos foram tiradas **em local claro e durante o dia**
  - Avaliação (Ótimo/Bom/Regular/Ruim) de cada área + observações

As fotos são **tiradas pela câmera no momento da vistoria**
(não dá para anexar fotos antigas): cada foto leva marca d'água
com data/hora, placa, categoria e GPS, e o sistema só aceita
fotos capturadas nos últimos 5 minutos.

## O que o administrador faz
- Área administrativa protegida por senha.
- Painel com: vistorias do mês, vistorias atrasadas, pendências.
- **Controle mensal**: filtra qualquer mês/ano e vê todas as vistorias com miniaturas.
- Abre cada vistoria e vê **todas as fotos organizadas por categoria**.
- **Aprova ou rejeita** cada vistoria com nota.
- Cadastro de motoristas/veículos e importação dos dados do sistema anterior.

## Como executar
```bash
pip install -r requirements.txt
python app.py
```
Abra http://127.0.0.1:5000

**Acesso público temporário (túnel HTTPS):**
para os motoristas usarem de qualquer lugar (a câmera e o GPS
só funcionam em HTTPS), baixe o cloudflared e rode junto:

```
# 1) baixe o cloudflared (uma vez)
#    https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
#    salve como cloudflared.exe na pasta do app
python app.py
cloudflared.exe tunnel --url http://localhost:5000
```
O cloudflared mostra um link tipo
`https://xxxx.trycloudflare.com` — esse é o link "executável"
para enviar aos motoristas (funciona no celular, com câmera e GPS).
O link é temporário: volta a funcionar só enquanto o PC e o
túnel estiverem ligados, e muda a cada reinício.

**Link pessoal de cada motorista:** na tela inicial (e no painel do
administrador) cada motorista tem seu próprio link, ex.:
`http://<ip-do-computador>:5000/m/1`. Envie o link dele para o
motorista (WhatsApp, etc.) — ele abre direto o painel do veículo
dele, com a contagem dos 30 dias.

**Acesso pelo celular na mesma rede:** ao rodar `python app.py`, o
terminal mostra o IP da máquina (ex.: http://10.x.x.x:5000). Use
`http://<ip>:5000/m/<id>` no celular do motorista.

## Primeiros passos
1. **Senha do administrador:** nesta instalação é **`A103114`**.
   Em uma instalação nova (clone do GitHub) a senha padrão é `locaomd123`.
   A senha fica salva no banco e pode ser trocada no painel do
   administrador (sem precisar mexer no código). Para forçar por
   variável de ambiente, defina `LOCAOMD_SENHA` antes de rodar:
   ```
   set LOCAOMD_SENHA=minhaSenhaNova   (Windows)
   export LOCAOMD_SENHA=minhaSenhaNova (Linux/Mac)
   ```
2. **Importar motoristas/veículos existentes** (do sistema Uber):
   ```
   python seed_data.py "C:\Users\netho\OneDrive\Desktop\Uber ok\PAGAMENTO UBER 2321\dados_motoristas.json"
   ```
   Ou use o botão "Importar dados" dentro da área do administrador.

## Estrutura de pastas
- `fotos/<PLACA>/<DATA_HORA>/` – fotos originais da vistoria (não versionadas)
- `fotos/_thumbs/` – miniaturas geradas automaticamente
- `instance/locaomd.db` – banco de dados SQLite

## Regra dos 30 dias
A cada vistoria registrada, o sistema calcula
**próxima vistoria = data da vistoria + 30 dias** e exibe para o motorista
no painel dele (com contagem de dias e aviso de vencimento).

## Fotos ilustrativas (exemplos)
As imagens de `static/exemplos/` são **fotos reais** que mostram ao
motorista o ângulo esperado de cada foto (substituem os desenhos
antigos do `gerar_exemplos.py`, que agora é legado).

Todas vêm de bancos livres (via Openverse.org) e permitem uso
comercial e modificação. **Mantenha os créditos abaixo** (CC BY e
CC BY-SA exigem atribuição):

| Arquivo | Foto | Licença | Fonte |
|---|---|---|---|
| externo_frente.jpg | Exeed E08 (concept car) front view | CC BY | commons.wikimedia.org/w/index.php?curid=147769613 |
| externo_traseira.jpg | GAZ-22171/GAZ-3221 police cars (rear view) | CC BY-SA | commons.wikimedia.org/w/index.php?curid=25205399 |
| externo_lado_esq.jpg | Car side profile | CC BY-SA | flickr.com/photos/60373961@N04/15915784362 |
| externo_lado_dir.jpg | Tesla plug-in electric car, left side profile | CC BY-SA | flickr.com/photos/9998127@N06/4402050357 |
| pneu_dianteiro_esq.jpg | Jowett Jupiter classic sports car | CC BY | flickr.com/photos/40837632@N05/5159348513 |
| pneu_dianteiro_dir.jpg | Car tire closeup | CC BY-SA | commons.wikimedia.org/w/index.php?curid=75863432 |
| pneu_traseiro_esq.jpg | Flat tire | CC BY | flickr.com/photos/39160147@N03/14970342360 |
| pneu_traseiro_dir.jpg | Car tire (ball joint) closeup | CC0 | commons.wikimedia.org/w/index.php?curid=115400396 |
| interno_bancos.jpg | Car cleaning | CC BY | flickr.com/photos/12394349@N06/4849718464 |
| interno_porta_malas.jpg | Car2Go/Smart car trunk | CC BY-SA | flickr.com/photos/25443792@N05/8376082216 |
| interno_teto.jpg | 2005 Mustang concept car interior | CC BY-SA | flickr.com/photos/59398780@N00/2210883440 |
| interno_piso.jpg | 1946 DeSoto Suburban | CC BY | flickr.com/photos/10966541@N02/3073256214 |
| painel.jpg | Car dashboard | CC BY-SA | commons.wikimedia.org/w/index.php?curid=4578366 |
| motor.jpg | Engine bay | Domínio Público (PDM) | flickr.com/photos/45379817@N08/8079130276 |

> Nota: algumas categorias (pneus, piso, bancos) usam fotos de carro
> inteiro por falta de close-ups livres adequados — troque manualmente
> por fotos do seu próprio frota se quiser algo mais fiel.
