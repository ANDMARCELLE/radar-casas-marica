# Radar de Casas Maricá

Monitoramento automático de casas com quintal para alugar em Maricá-RJ (ZAP Imóveis, OLX, QuintoAndar, Chaves na Mão, Renato Imóveis). Roda sozinho, de hora em hora, via GitHub Actions — sem depender de nenhuma sessão do Claude ficar aberta.

- **Critérios**: casa, 2+ quartos, com quintal, custo total (aluguel + condomínio + IPTU) até R$ 3.500 — destaque para até R$ 2.500.
- **Aviso**: push via [ntfy.sh](https://ntfy.sh) (celular, grátis, sem cadastro) + notificação no navegador enquanto a página do painel estiver aberta (PC).
- **Painel**: página estática (`index.html`) publicada via GitHub Pages, lê `data/listings.json`.
- **Robô**: `scraper.py`, roda dentro do GitHub Actions (`.github/workflows/scan.yml`), sem custo de IA — usa regras de texto (regex), então pode falhar se algum site mudar de layout.

## Colocar no ar (uma vez só)

1. **Criar o repositório**: crie um repositório novo e **vazio** no GitHub chamado `radar-casas-marica` (não marque "adicionar README").
2. **Subir este código**, no Terminal, dentro desta pasta:
   ```bash
   git init
   git add .
   git commit -m "Radar de Casas Maricá — versão inicial"
   git branch -M main
   git remote add origin https://github.com/SEU-USUARIO/radar-casas-marica.git
   git push -u origin main
   ```
3. **Ativar o GitHub Pages**: no repositório, vá em **Settings → Pages** → em "Build and deployment", escolha **Deploy from a branch**, branch `main`, pasta `/ (root)` → Save. Em 1-2 minutos o painel fica em `https://SEU-USUARIO.github.io/radar-casas-marica/`.
4. **(Opcional) Trocar o tópico do ntfy**: o tópico padrão é `radar-marica-0e5a3b9c` (já vem configurado em `index.html`). Tópicos do ntfy.sh são públicos — qualquer um que souber o nome exato pode ler os avisos. Se quiser um nome só seu, troque a linha `NTFY_TOPIC` no topo de `index.html` E crie um **Secret** no repositório (`Settings → Secrets and variables → Actions → New repository secret`) chamado `NTFY_TOPIC` com o mesmo valor.
5. **Instalar o app ntfy** no celular ([iOS](https://apps.apple.com/us/app/ntfy/id1625396347) / [Android](https://play.google.com/store/apps/details?id=io.heckel.ntfy)) e se inscrever no tópico configurado.

## Rodar uma varredura na hora ("botão")

O painel tem um botão **"▶ Rodar varredura agora"**. Pra ele disparar a varredura sem sair da página, precisa de um token de acesso **bem restrito** colado direto no `index.html`:

1. Vá em [github.com/settings/personal-access-tokens/new](https://github.com/settings/personal-access-tokens/new) (token **fine-grained**, não o "classic")
2. Nome: `radar-casas-marica-dispatch`
3. Expiration: 90 dias (vai precisar trocar depois de vencer)
4. Repository access: **Only select repositories** → escolha `radar-casas-marica`
5. Em **Permissions → Repository permissions**, ache **Actions** e mude para **Read and write** (é a única permissão que precisa marcar)
6. **Generate token** e copie o valor
7. No GitHub, abra `index.html` → ícone de lápis (editar) → ache a linha `const GITHUB_TOKEN = "COLE_SEU_TOKEN_AQUI";` → troque pelo token → **Commit changes** direto na `main`

⚠️ **Esse token fica visível pra qualquer um que abrir o código-fonte da página** (ela é pública). Por isso ele só pode ter permissão de "Actions: Read and write" nesse único repositório — nunca use um token "classic" ou com escopo `repo` aqui. Na pior das hipóteses, alguém que pegasse esse token só conseguiria disparar varreduras à toa (grátis, sem custo, repositório público) — não consegue ler nada privado nem alterar código.

Se preferir não fazer isso, o botão continua funcionando do jeito simples: ele te leva pra aba Actions do GitHub, onde é só clicar em **Run workflow**.

## Limitações conhecidas

- **ZAP e OLX** bloqueiam acesso automatizado simples; o robô usa um navegador real (Playwright) pra contornar isso, mas não há garantia — sites de anti-robô mudam com frequência.
- **QuintoAndar** não tem filtro de "quintal" na busca, então os anúncios de lá aparecem mesmo quando o quintal não pôde ser confirmado no texto — confira a foto/descrição antes de se empolgar.
- O robô é gratuito (sem chamadas de IA), então usa regras fixas de texto — mais frágil que uma extração inteligente, mas sem custo.
