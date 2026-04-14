import asyncio
import httpx
import re
from datetime import datetime
import os

SOURCE_FILE = 'sources.txt'
OUTPUT_FILE = 'ads.txt'
MAX_CONCURRENT = 10 

# Регулярка для поиска доменов
AD_PATTERNS = re.compile(
    r'https?://(?:www\.)?([\w\-\.]+\.(?:com|net|org|ru|tv|io|biz|info|me|top|xyz|pro|online)(?:/(?:[\\w\-\.]+))?)', 
    re.IGNORECASE
)

# Ключевые слова-паразиты
BLACK_KEYWORDS = ['ads', 'track', 'doubleclick', 'pixel', 'analytics', 'metrics', 'popunder', 'affiliate']

# Список "святых" доменов, которые нельзя банить целиком
TRUSTED_DOMAINS = [
    'yandex.ru', 'yandex.com', 'google.com', 'google.ru', 
    'vk.com', 't.me', 'discord.com', 'github.com', 
    'youtube.com', 'mail.ru', 'rambler.ru', 'ok.ru'
]

async def scrub_fast(client, url, semaphore):
    async with semaphore:
        print(f"📡 Сканирую: {url}")
        found = set()
        try:
            resp = await client.get(f"http://{url}", timeout=10, follow_redirects=True)
            matches = AD_PATTERNS.findall(resp.text)
            
            for link in matches:
                link_lower = link.lower()
                
                # Если нашли паразитное слово
                if any(key in link_lower for key in BLACK_KEYWORDS):
                    domain = link.split('/')[0]
                    
                    # Проверка: не пытаемся ли мы забанить основу гигантов?
                    is_trusted = any(domain == trusted or domain.endswith('.' + trusted) for trusted in TRUSTED_DOMAINS)
                    
                    # Если домен в белом списке И это просто голый домен (без слова ads/track в поддомене) — скипаем
                    # Но если это ads.yandex.ru — разрешаем забанить!
                    if is_trusted:
                        # Разрешаем бан только если ключевое слово — это часть поддомена (например, ads.yandex.ru)
                        subdomain_part = domain.split('.')[0]
                        if any(key in subdomain_part for key in BLACK_KEYWORDS):
                            found.add(domain)
                    else:
                        # Если домена нет в белом списке — баним без пощады
                        found.add(domain)
                        
        except Exception:
            print(f"⚠️ {url} в отказ")
        return found

async def main():
    print("🔮 Ритуал мгновенной очистки V.O.I.D запущен...")
    if not os.path.exists(SOURCE_FILE): return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    async with httpx.AsyncClient(
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}, 
        verify=False
    ) as client:
        tasks = [scrub_fast(client, target, semaphore) for target in targets]
        results = await asyncio.gather(*tasks)

    all_domains = set().union(*results)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(f"# V.O.I.D Fast Scrabber | {datetime.now()}\n")
        f.write("# Автоматический бан-лист рекламных доменов\n\n")
        for d in sorted(all_domains):
            f.write(f"0.0.0.0 {d}\n")
            
    print(f"🔥 Готово! Найдено и обезврежено: {len(all_domains)} доменов.")

if __name__ == "__main__":
    asyncio.run(main())
