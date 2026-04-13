import asyncio
import httpx
import re
from datetime import datetime
import os

SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'ads.txt'
MAX_CONCURRENT = 10 # Можем херачить сразу по 10 сайтов, это же не браузер

AD_PATTERNS = re.compile(
    r'https?://(?:www\.)?([\w\-\.]+\.(?:com|net|org|ru|tv|io|biz|info|me|top|xyz|pro|online)(?:/(?:[\w\-\.]+))?)', 
    re.IGNORECASE
)

# Ключевые слова-паразиты
BLACK_KEYWORDS = ['ads', 'track', 'doubleclick', 'pixel', 'analytics', 'metrics', 'popunder', 'affiliate']

async def scrub_fast(client, url, semaphore):
    async with semaphore:
        print(f"📡 Сканирую: {url}")
        found = set()
        try:
            # Просто тянем текст страницы, не запуская браузер
            resp = await client.get(f"http://{url}", timeout=10, follow_redirects=True)
            
            # Ищем все ссылки в тексте страницы
            matches = AD_PATTERNS.findall(resp.text)
            for link in matches:
                # Если в ссылке есть рекламное слово — забираем домен
                if any(key in link.lower() for key in BLACK_KEYWORDS):
                    domain = link.split('/')[0]
                    found.add(domain)
        except Exception:
            print(f"⚠️ {url} в отказ")
        return found

async def main():
    print("🔮 Ритуал мгновенной очистки запущен...")
    if not os.path.exists(SOURCE_FILE): return

    with open(SOURCE_FILE, 'r') as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient(headers={'User-Agent': 'Mozilla/5.0...'}, verify=False) as client:
        tasks = [scrub_fast(client, target, semaphore) for target in targets]
        results = await asyncio.gather(*tasks)

    all_domains = set().union(*results)

    with open(OUTPUT_FILE, 'w') as f:
        f.write(f"# V.O.I.D Fast Scrabber | {datetime.now()}\n\n")
        for d in sorted(all_domains):
            f.write(f"0.0.0.0 {d}\n")
    print(f"🔥 Готово! Найдено: {len(all_domains)}")

if __name__ == "__main__":
    asyncio.run(main())
