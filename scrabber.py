import asyncio
from playwright.async_api import async_playwright
import re
from datetime import datetime
import os

# Конфиг
SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'ads.txt'
MAX_CONCURRENT_SITES = 3  # Сколько сайтов парсим одновременно

AD_PATTERNS = re.compile(
    r'(ads?|track|doubleclick|pixel|analytics|metrics|marketing|popunder|banner|affiliate|pangle|adnxs|flurry|yandex.*metrica|google-analytics)', 
    re.IGNORECASE
)

async def scrub_site(browser, url, semaphore):
    async with semaphore:
        print(f"📡 Вторжение: {url}")
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        found_in_site = set()

        # Слушаем сетевые запросы
        page.on("request", lambda request: analyze_request(request.url, found_in_site))

        try:
            # wait_until="domcontentloaded" — это секрет скорости
            await page.goto(f"http://{url}", wait_until="domcontentloaded", timeout=10000)
            # Быстрый скролл для триггера рекламы
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2) 
        except Exception:
            print(f"⚠️  {url} слишком медленный или заблокирован. Пропускаем.")
        finally:
            await page.close()
            await context.close()
        return found_in_site

def analyze_request(request_url, storage):
    match = re.search(r'https?://(?:www\.)?([\w\-\.]+)', request_url)
    if match:
        domain = match.group(1)
        if AD_PATTERNS.search(domain):
            storage.add(domain)

async def main():
    print("🔮 Ритуал обновления артефакта V.O.I.D запущен...")

    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Файл {SOURCE_FILE} не найден!")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_SITES)
        
        # Создаем задачи для всех сайтов
        tasks = [scrub_site(browser, target, semaphore) for target in targets]
        results = await asyncio.gather(*tasks)

        all_parasites = set()
        for res in results:
            all_parasites.update(res)

        await browser.close()

    # Запись в корень репо
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# V.O.I.D ad scrabber | Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Лицензия: МАНИФЕСТ СВОБОДНОЙ ЦИТАДЕЛИ (GPLv3)\n")
        f.write("# Статус: Активен. Смерть рекламе.\n\n")
        for domain in sorted(all_parasites):
            f.write(f"0.0.0.0 {domain}\n")

    print(f"🔥 Ритуал завершен. {OUTPUT_FILE} обновлен. Найдено паразитов: {len(all_parasites)}")

if __name__ == "__main__":
    asyncio.run(main())
