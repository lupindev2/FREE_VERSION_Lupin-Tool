import re
import threading
import queue
from urllib.parse import quote_plus, unquote
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

PLATFORMS = [
    ("Instagram", "instagram.com"),
    ("TikTok", "tiktok.com"),
    ("Twitter/X", "twitter.com"),
    ("Facebook", "facebook.com"),
    ("GitHub", "github.com"),
    ("Snapchat", "snapchat.com"),
    ("LinkedIn", "linkedin.com"),
    ("Reddit", "reddit.com"),
    ("Pinterest", "pinterest.com"),
    ("YouTube", "youtube.com"),
    ("Twitch", "twitch.tv"),
]

def _http_get(url, timeout=5):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ""

def _ddg(query, max_results=5):
    url = "https://html.duckduckgo.com/html/?q=" + quote_plus(query)
    html = _http_get(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for a in soup.select("a.result__a")[:max_results]:
        href = a.get("href", "")
        m = re.search(r"uddg=([^&]+)", href)
        if m:
            href = unquote(m.group(1))
        title = a.get_text(strip=True)
        if href.startswith("http"):
            out.append((title, href))
    return out

def _bing(query, max_results=5):
    url = "https://www.bing.com/search?q=" + quote_plus(query)
    html = _http_get(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for li in soup.select("li.b_algo")[:max_results]:
        a = li.find("a")
        if a and a.get("href", "").startswith("http"):
            out.append((a.get_text(strip=True), a["href"]))
    return out

SEARCH_ENGINES = [_ddg, _bing]

def _fetch_page_metadata(url):
    html = _http_get(url, timeout=4)
    if not html:
        return None
    try:
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.get_text(strip=True) if soup.title else ""
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
        phones = re.findall(r'0[1-9](?:[ .-]?[0-9]{2}){4}', html)
        socials = re.findall(r'https?://(?:www\.)?(?:instagram|tiktok|twitter|x|facebook|snapchat|linkedin|youtube|twitch|discord|reddit|pinterest|tumblr|threads)\.com/[^\s"\'<>]+', html)
        return {
            "title": title,
            "emails": list(set(emails))[:3],
            "phones": list(set(phones))[:3],
            "socials": list(set(socials))[:3],
        }
    except Exception:
        return None

class OsintEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = None
        self.running = False
        self.stop_flag = False

    def start(self, identity):
        if not HAS_REQUESTS:
            self.queue.put(("error", "pip install requests beautifulsoup4"))
            return
        self.running = True
        self.stop_flag = False
        self.thread = threading.Thread(target=self._run, args=(identity,), daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_flag = True

    def _emit(self, kind, label, data=None):
        self.queue.put((kind, label, data))

    def _search_all_engines(self, query, max_per_engine=4):
        results = []
        seen = set()
        def run_engine(engine):
            try:
                return engine(query, max_per_engine)
            except Exception:
                return []
        with ThreadPoolExecutor(max_workers=len(SEARCH_ENGINES)) as ex:
            futures = [ex.submit(run_engine, eng) for eng in SEARCH_ENGINES]
            for future in as_completed(futures):
                if self.stop_flag:
                    break
                for title, url in future.result():
                    if url in seen:
                        continue
                    seen.add(url)
                    results.append((title, url))
        return results

    def _run(self, identity):
        pseudo = identity.get("pseudo", "").strip()
        mail = identity.get("mail", "").strip()
        nom = identity.get("nom", "").strip()
        prenom = identity.get("prenom", "").strip()
        tel = identity.get("tel", "").strip()

        total = 0
        found = 0

        def do_search(label, query):
            nonlocal total, found
            if self.stop_flag:
                return []
            self._emit("log", f"Recherche : {label}")
            res = self._search_all_engines(query)
            urls = []
            for title, url in res:
                if "bing.com" in url or "google.com" in url:
                    continue
                total += 1
                found += 1
                self._emit("result", f"{label} : {title}", {"title": title, "url": url, "source": label})
                urls.append(url)
            return urls

        urls_to_fetch = []

        if pseudo:
            self._emit("log", f"Scan des réseaux pour le pseudo : {pseudo}")
            for platform_name, domain in PLATFORMS:
                urls_to_fetch += do_search(f"Profil {platform_name}", f'"{pseudo}" site:{domain}')
            urls_to_fetch += do_search("Forums & Fuites", f'"{pseudo}" forum OR pastebin')

        if nom or prenom:
            full = f"{prenom} {nom}".strip()
            self._emit("log", f"Scan de l'identité : {full}")
            urls_to_fetch += do_search("Nom complet", f'"{full}"')
            urls_to_fetch += do_search("Documents", f'"{full}" filetype:pdf OR filetype:doc')

        if tel:
            self._emit("log", f"Scan du numéro : {tel}")
            urls_to_fetch += do_search("Numéro de téléphone", f'"{tel}"')

        if mail:
            self._emit("log", f"Scan de l'email : {mail}")
            urls_to_fetch += do_search("Email exposé", f'"{mail}"')

        self._emit("log", "Extraction des données (deep scan)...")
        unique_urls = list(dict.fromkeys(urls_to_fetch))[:30]

        def fetch_one(u):
            if self.stop_flag:
                return u, None
            return u, _fetch_page_metadata(u)

        with ThreadPoolExecutor(max_workers=15) as ex:
            futures = {ex.submit(fetch_one, u): u for u in unique_urls}
            for future in as_completed(futures):
                if self.stop_flag:
                    break
                u, meta = future.result()
                if meta:
                    total += 1
                    if meta["emails"] or meta["phones"] or meta["socials"]:
                        found += 1
                        if meta["emails"]:
                            self._emit("extracted", f"Email trouvé : {meta['emails'][0]}", {"title": "Email", "url": u, "source": "Extraction"})
                        if meta["phones"]:
                            self._emit("extracted", f"Téléphone trouvé : {meta['phones'][0]}", {"title": "Téléphone", "url": u, "source": "Extraction"})
                        if meta["socials"]:
                            self._emit("extracted", f"Réseau trouvé : {meta['socials'][0]}", {"title": meta['socials'][0].split('/')[2], "url": meta['socials'][0], "source": "Extraction"})

        self._emit("stats", f"{found} résultats", (found, total))
        self._emit("done", "Scan terminé")
        self.running = False

    def poll(self):
        items = []
        while True:
            try:
                items.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return items