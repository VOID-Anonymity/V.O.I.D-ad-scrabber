import asyncio
from playwright.async_api import async_playwright
import re
from datetime import datetime
import os

# Конфиг
SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'ads.txt'

# Паттерны для вычисления рекламной нечисти
AD_PATTERNS = re.compile(
    r'(ads?|track|doubleclick|pixel|analytics|metrics|marketing|popunder|banner|affiliate|pangle|adnxs|flurry)', 
    re.IGNORECASE
)

async def scrub_site(browser, url):
    print(f"📡 Вторжение в цифровое пространство: {url}")
    # Контекст с подменой юзер-агента
    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    )
    page = await context.new_page()
    found_in_site = set()

    # Перехват каждого шороха в сети
    page.on("request", lambda request: analyze_request(request.url, found_in_site))

    try:
        # Пытаемся зайти. Ждем networkidle, чтобы отловить отложенную рекламу
        await page.goto(f"http://{url}", wait_until="networkidle", timeout=20000)
        # Прокрутка вниз — триггер для ленивых скриптов
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3) 
    except Exception as e:
        print(f"⚠️  Объект {url} выставил щиты: {e}")
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
    print("🔮 Ритуал обновления артефакта запущен...")

    if not os.path.exists(SOURCE_FILE):
        print(f"❌ Критическая ошибка: {SOURCE_FILE} не найден в корне!")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        all_parasites = set()

        for target in targets:
            results = await scrub_site(browser, target)
            all_parasites.update(results)

        await browser.close()

    # Запись/Обновление файла ads.txt прямо в корне
    mode = 'w' # Всегда перезаписываем свежаком
    with open(OUTPUT_FILE, mode, encoding='utf-8') as f:
        f.write(f"# V.O.I.D ad scrabber | Сформировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# Статус: Активен. Смерть рекламе.\n\n")
        for domain in sorted(all_parasites):
            f.write(f"0.0.0.0 {domain}\n")

    print(f"🔥 Ритуал завершен. Файл {OUTPUT_FILE} обновлен. Обнаружено угроз: {len(all_parasites)}")

if __name__ == "__main__":
    asyncio.run(main())
