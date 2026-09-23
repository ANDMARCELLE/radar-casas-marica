#!/usr/bin/env python3
"""
Radar de Casas Maricá — varredura de sites de imóveis.

Procura casas para alugar em Maricá-RJ com quintal, 2+ quartos,
custo total (aluguel + condomínio + IPTU) até R$ 3.500.

Sem chamadas de IA: extrai tudo via regex/heurísticas de texto,
o que é gratuito mas pode quebrar se um site mudar de layout.
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "listings.json"

MAX_TOTAL_PRICE = 3500
IDEAL_PRICE = 2500
GOOD_PRICE = 3000
MIN_BEDROOMS = 2
MAX_DETAIL_PAGES_PER_SITE = 20

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "").strip()

YARD_KEYWORDS = [
    "quintal", "área externa", "area externa", "jardim", "gramado",
    "espaço externo", "espaco externo", "terreno amplo",
]
EXCLUDE_TYPE_KEYWORDS = ["apartamento", "kitnet", "studio", "flat", "sala comercial", "loja", "galpão", "terreno "]

COOKIE_BUTTON_TEXTS = [
    "Aceitar", "Aceitar todos", "Aceitar cookies", "Entendi", "OK", "Concordo",
]


def log(msg):
    print(f"[radar] {msg}", flush=True)


def dismiss_cookie_banner(page):
    for text in COOKIE_BUTTON_TEXTS:
        try:
            btn = page.get_by_text(text, exact=False).first
            if btn.is_visible(timeout=1000):
                btn.click(timeout=1000)
                page.wait_for_timeout(300)
                return
        except Exception:
            continue


def money_to_float(s):
    """'R$ 2.999,00' / 'R$ 2999' / '1.098,11' -> float"""
    if not s:
        return None
    s = s.replace("R$", "").strip()
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(re.search(r"[\d.]+", s).group())
    except Exception:
        return None


def find_prices(text):
    """Return list of monetary values (float) found in a text block."""
    return [money_to_float(m) for m in re.findall(r"R\$\s*[\d.,]+", text)]


def find_bedrooms(text):
    m = re.search(r"(\d+)\s*(?:quarto|dormit[óo]rio)", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def has_yard_mention(text):
    low = text.lower()
    return any(k in low for k in YARD_KEYWORDS)


def looks_like_house(text):
    low = text.lower()
    if any(k in low for k in EXCLUDE_TYPE_KEYWORDS):
        return False
    return True


def slug_id(url):
    """Stable dedupe key from a listing URL."""
    clean = url.split("?")[0].split("#")[0].lower()
    clean = re.sub(r"https?://(www\.)?", "", clean)
    clean = re.sub(r"[^a-z0-9]+", "-", clean).strip("-")
    return clean[:200]


def send_ntfy(title, message, url):
    if not NTFY_TOPIC:
        return
    try:
        req = urllib.request.Request(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title.encode("utf-8"),
                "Click": url,
                "Priority": "high",
                "Tags": "house,rotating_light",
            },
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log(f"falha ao enviar ntfy: {e}")


def load_seen():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def save_seen(listings):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(listings, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Per-site search: return list of candidate detail-page URLs to visit
# ---------------------------------------------------------------------------

def collect_zap(page):
    url = "https://www.zapimoveis.com.br/aluguel/casas/rj+marica/quintal/"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(3000)
    dismiss_cookie_banner(page)
    hrefs = page.eval_on_selector_all(
        "a[href*='/imovel/aluguel-casa']",
        "els => els.map(e => e.href)",
    )
    return list(dict.fromkeys(hrefs))[:MAX_DETAIL_PAGES_PER_SITE]


def collect_chavesnamao(page):
    url = "https://www.chavesnamao.com.br/casas-com-quintal-para-alugar/rj-marica/"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)
    dismiss_cookie_banner(page)
    hrefs = page.eval_on_selector_all(
        "a[href*='/imovel/casa-para-alugar']",
        "els => els.map(e => e.href)",
    )
    return list(dict.fromkeys(hrefs))[:MAX_DETAIL_PAGES_PER_SITE]


def collect_quintoandar(page):
    url = "https://www.quintoandar.com.br/alugar/imovel/marica-rj-brasil/casa"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(3000)
    dismiss_cookie_banner(page)
    hrefs = page.eval_on_selector_all(
        "a[href*='/imovel/'][href*='/alugar/casa']",
        "els => els.map(e => e.href)",
    )
    hrefs = [h.split("?")[0] for h in hrefs]
    return list(dict.fromkeys(hrefs))[:MAX_DETAIL_PAGES_PER_SITE]


def collect_olx(page):
    url = "https://www.olx.com.br/imoveis/aluguel/casas/estado-rj/rio-de-janeiro-e-regiao/itaborai-e-regiao/marica"
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(3000)
    dismiss_cookie_banner(page)
    hrefs = page.eval_on_selector_all(
        "a[href*='olx.com.br'][href*='/imoveis/']",
        "els => els.map(e => e.href)",
    )
    hrefs = [h for h in hrefs if re.search(r"-\d{6,}$", h.split("?")[0])]
    return list(dict.fromkeys(hrefs))[:MAX_DETAIL_PAGES_PER_SITE]


def collect_renatoimoveis(page):
    url = "https://www.renatoimoveis.adm.br/imoveis/locacao/casa/marica/rj"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=45000)
    except Exception as e:
        log(f"Renato Imóveis: página de busca falhou ({e}), pulando site nesta rodada")
        return []
    page.wait_for_timeout(2500)
    dismiss_cookie_banner(page)
    hrefs = page.eval_on_selector_all(
        "a[href*='/imovel/']",
        "els => els.map(e => e.href)",
    )
    return list(dict.fromkeys(hrefs))[:MAX_DETAIL_PAGES_PER_SITE]


SITES = {
    "ZAP Imóveis": collect_zap,
    "Chaves na Mão": collect_chavesnamao,
    "QuintoAndar": collect_quintoandar,
    "OLX": collect_olx,
    "Renato Imóveis": collect_renatoimoveis,
}


def extract_listing(page, site_name, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(1500)
        dismiss_cookie_banner(page)
        text = page.evaluate("document.body.innerText")
    except Exception as e:
        log(f"  falha ao abrir {url}: {e}")
        return None

    if not looks_like_house(text[:600]) and not looks_like_house(page.title() or ""):
        return None

    bedrooms = find_bedrooms(text)
    if bedrooms is None or bedrooms < MIN_BEDROOMS:
        return None

    yard_ok = has_yard_mention(text) or site_name in ("ZAP Imóveis", "Chaves na Mão")
    if not yard_ok:
        return None

    prices = [p for p in find_prices(text) if p and 200 <= p <= 20000]
    if not prices:
        return None
    base_rent = min(prices)

    condo = 0
    m = re.search(r"cond(?:om[íi]nio)?\.?\s*(?:R\$\s*[\d.,]+|isento)", text, re.IGNORECASE)
    if m and "isento" not in m.group(0).lower():
        condo = money_to_float(re.search(r"R\$\s*[\d.,]+", m.group(0)).group()) or 0

    iptu = 0
    m = re.search(r"IPTU\.?\s*(?:R\$\s*[\d.,]+|isento)", text, re.IGNORECASE)
    if m and "isento" not in m.group(0).lower():
        iptu = money_to_float(re.search(r"R\$\s*[\d.,]+", m.group(0)).group()) or 0
        if iptu > base_rent:
            iptu = round(iptu / 12, 2)  # provavelmente valor anual

    total = round(base_rent + condo + iptu, 2)
    if total > MAX_TOTAL_PRICE:
        return None

    title = (page.title() or "Casa em Maricá").split(" - ")[0].split(" | ")[0].strip()
    addr_match = re.search(r"(?:em|,)\s*([A-ZÀ-Ú][\wÀ-ú' ]+,\s*Marica[áa])", text)
    address = addr_match.group(1) if addr_match else "Maricá - RJ"

    return {
        "id": slug_id(url),
        "title": title,
        "address": address,
        "bedrooms": bedrooms,
        "baseRent": base_rent,
        "condo": condo,
        "iptu": iptu,
        "price": total,
        "hasYard": True,
        "site": site_name,
        "url": url,
        "foundAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def main():
    seen = load_seen()
    seen_ids = {item["id"] for item in seen}
    new_items = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            locale="pt-BR",
        )
        page = context.new_page()

        for site_name, collector in SITES.items():
            log(f"Buscando em {site_name}...")
            try:
                urls = collector(page)
            except Exception as e:
                log(f"  erro na busca de {site_name}: {e}")
                continue
            log(f"  {len(urls)} candidatos encontrados")

            for url in urls:
                if slug_id(url) in seen_ids:
                    continue
                item = extract_listing(page, site_name, url)
                if item:
                    if item["id"] in seen_ids:
                        continue
                    log(f"  ✔ NOVO: {item['title']} — R$ {item['price']:.0f} ({site_name})")
                    new_items.append(item)
                    seen_ids.add(item["id"])
                time.sleep(1)

        browser.close()

    if new_items:
        all_items = seen + new_items
        save_seen(all_items)
        log(f"{len(new_items)} anúncio(s) novo(s) salvo(s).")

        new_items.sort(key=lambda x: x["price"])
        for item in new_items:
            tag = "IDEAL" if item["price"] <= IDEAL_PRICE else ("ÓTIMO" if item["price"] <= GOOD_PRICE else "")
            title = f"R$ {item['price']:.0f}/mês — Casa em Maricá" + (f" [{tag}]" if tag else "")
            body = (
                f"{item['address']} • {item['bedrooms']} quartos • {item['site']}\n"
                f"{item['url']}"
            )
            send_ntfy(title, body, item["url"])
    else:
        log("Nenhum anúncio novo nesta rodada.")

    log("Concluído.")


if __name__ == "__main__":
    sys.exit(main())
