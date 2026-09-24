# Radar de Casas Maricá

Monitoramento automático de casas com quintal para alugar em Maricá-RJ (ZAP Imóveis, OLX, QuintoAndar, Chaves na Mão, Imovelweb, Renato Imóveis, Kiffer Imóveis). Roda sozinho, de hora em hora, via GitHub Actions — sem depender de nenhuma sessão do Claude ficar aberta.

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

O painel tem um botão **"▶ Rodar varredura agora"**. Ele te leva direto pra aba Actions do GitHub — lá é só clicar em **Run workflow**.

Chegamos a testar um botão 100% dentro da página (sem sair pro GitHub), usando um token de acesso restrito embutido no `index.html`. Não funciona: o próprio GitHub detecta e **revoga automaticamente** qualquer token dele publicado num repositório público, em minutos, como proteção de segurança — não tem como desativar isso nem contornar. Por isso o botão só abre a tela certa; o clique final em "Run workflow" precisa ser manual mesmo.

## Limitações conhecidas

- **ZAP e OLX** bloqueiam acesso automatizado simples; o robô usa um navegador real (Playwright) pra contornar isso, mas não há garantia — sites de anti-robô mudam com frequência.
- **QuintoAndar** não tem filtro de "quintal" na busca, então os anúncios de lá aparecem mesmo quando o quintal não pôde ser confirmado no texto — confira a foto/descrição antes de se empolgar.
- O robô é gratuito (sem chamadas de IA), então usa regras fixas de texto — mais frágil que uma extração inteligente, mas sem custo.
