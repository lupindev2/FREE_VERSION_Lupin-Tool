import base64
import json
import os
import sys
import threading
import http.cookiejar
import urllib.error
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import pygame

                                                                        
                                                
                                                                        
BG        = (8, 8, 8)
PANEL     = (12, 12, 12)
CARD      = (16, 16, 16)
CARD_HOV  = (22, 22, 22)
BORDER    = (28, 28, 28)
BORDER_HI = (44, 44, 44)
WHITE     = (235, 235, 235)
GREY      = (150, 150, 150)
MUTED     = (90, 90, 90)
DIM       = (55, 55, 55)
GREEN     = (120, 200, 120)

                                                                        
                    
                                                                        
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
_DEFAULT_API_URL = base64.b64decode(
    "aHR0cHM6Ly9zY3Jh" "cGh1Yi13ZWItYmFja2VuZC5mbHku" "ZGV2L2FwaQ=="
).decode("ascii")

def load_env(path: Path):
    if not path.is_file(): return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception as e:
        print(f"[.env] Erreur de lecture : {e}", file=sys.stderr)

load_env(ENV_PATH)

                                                                        
                     
                                                                        
def _request_json(opener, url, payload):
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with opener.open(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            d = json.loads(raw)
            msg = d.get("error") or d.get("message") or raw
        except json.JSONDecodeError:
            msg = raw or str(e.reason)
        raise RuntimeError(f"HTTP {e.code}: {msg}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"API injoignable: {e}") from e

class ScraphubClient:
    def __init__(self):
        api_url = os.getenv("SCRAPHUB_API_URL") or _DEFAULT_API_URL
        self.api_url = api_url.rstrip("/")
        self.email = os.getenv("SCRAPHUB_EMAIL")
        self.password = os.getenv("SCRAPHUB_PASSWORD")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self._logged = False

    def _check_env(self):
        if not self.email or not self.password:
            raise RuntimeError(f"Identifiants absents. Vérifie {ENV_PATH}")
        if not self.api_url.startswith("https://"):
            raise RuntimeError("SCRAPHUB_API_URL doit utiliser HTTPS.")

    def login(self):
        self._check_env()
        _request_json(self.opener, f"{self.api_url}/auth/login", {"email": self.email, "password": self.password})
        self._logged = True

    def search(self, query, exact=False, limit=100):
        if not self._logged: self.login()
        return _request_json(self.opener, f"{self.api_url}/sqlite/search", {"query": query, "exactMatch": exact, "limit": limit})

                                                                        
                                                     
                                                                        
def extract_person_info(item):
    info = {"nom": "", "prenom": "", "full": "", "allocataire": "", "details": {}}
    
    raw_content = item.get("content") or item.get("data") or item.get("payload")
    
                                              
    if isinstance(raw_content, str):
        try:
            clean_val = raw_content.strip()
            if clean_val.startswith("{") or clean_val.startswith("["):
                parsed = json.loads(clean_val)
                if isinstance(parsed, dict):
                    item.update(parsed)
                raw_content = None
        except json.JSONDecodeError:
            pass

                                                          
                                                          
    if isinstance(raw_content, str) and "|" in raw_content:
        parts = [p.strip() for p in raw_content.split("|")]
        for p in parts:
                                                                                  
            if p.isalpha() and len(p) > 2:
                if p.isupper() and not info["nom"]:
                    info["nom"] = p
                elif not info["prenom"]:
                    info["prenom"] = p.capitalize()
            
                               
            if "-" in p and len(p) >= 10 and "Date de naissance" not in info["details"]:
                info["details"]["Date de naissance"] = p[:10]
        
        info["details"]["Ligne brute"] = raw_content

                                      
    def _search_dict(d, current_prefix=""):
        if not isinstance(d, dict): return
        for k, v in d.items():
            k_low = k.lower()
            if isinstance(v, str):
                                                         
                if "allocataire" in k_low or "beneficiaire" in k_low:
                    if "nom" in k_low and not info["nom"]: info["nom"] = v
                    elif ("prenom" in k_low or "prénom" in k_low) and not info["prenom"]: info["prenom"] = v
                    elif "nom" not in k_low and "prenom" not in k_low and "prenom" not in k_low:
                        info["allocataire"] = v
                                   
                elif k_low in ("nom", "lastname", "nom_famille") and not info["nom"]:
                    info["nom"] = v
                elif k_low in ("prenom", "firstname", "prénom", "given_name") and not info["prenom"]:
                    info["prenom"] = v
                elif k_low in ("name", "fullname", "full_name", "nom_complet", "nom complet") and not info["full"]:
                    info["full"] = v
            
            elif isinstance(v, dict):
                _search_dict(v, f"{current_prefix}{k}.")
            elif isinstance(v, list):
                for i in v:
                    if isinstance(i, dict): _search_dict(i, f"{current_prefix}{k}.")

    _search_dict(item)
    
                                               
    def _flatten_details(d, prefix=""):
        if not isinstance(d, dict): return
        for k, v in d.items():
            k_clean = k.replace("_", " ").capitalize()
            if k.lower() in ("id", "_id", "index", "score", "psp", "content", "data", "payload"): continue
            if isinstance(v, (str, int, float)) and str(v).strip() != "":
                info["details"][f"{prefix}{k_clean}"] = str(v)
            elif isinstance(v, dict):
                _flatten_details(v, f"{prefix}{k_clean} > ")

    _flatten_details(item)
    
    if "source" in item and "Source" not in info["details"]:
        info["details"]["Fichier source"] = str(item["source"])

    return info

                                                                        
       
                                                                        
class RechercheScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.SysFont("georgia", 26)
        self.font_modal_title = pygame.font.SysFont("georgia", 30)
        self.font_body  = pygame.font.SysFont("helvetica", 15)
        self.font_small = pygame.font.SysFont("helvetica", 13)
        self.font_tiny  = pygame.font.SysFont("helvetica", 11)

        self.client = ScraphubClient()

        self.query = ""
        self.exact = False
        self.cursor_t = 0.0
        self.last_tick = pygame.time.get_ticks()

        self.state = "idle"
        self.error_msg = ""
        self.results = []
        self.total = 0

        self.scroll_y = 0
        self.max_scroll = 0
        self.search_rect = pygame.Rect(0, 0, 0, 0)
        self.exact_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)
        self.search_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.export_rect = pygame.Rect(0, 0, 0, 0)

        self.card_rects = []
        
        self.modal_open = False
        self.modal_item = None
        self.modal_close_rect = pygame.Rect(0, 0, 0, 0)
        self.modal_scroll_y = 0
        self.modal_export_rect = pygame.Rect(0, 0, 0, 0)
        self.save_message = ""
        self.save_msg_time = 0

        self._worker = None

    def _run_search(self, query, exact):
        try:
            data = self.client.search(query, exact=exact, limit=100)
            items = data.get("results") or data.get("data") or data.get("items") or []
            if isinstance(items, dict):
                items = items.get("results", [])
            
            self.results = items
            self.total = data.get("total") or len(items)
            self.state = "done"
        except Exception as e:
            self.error_msg = str(e)
            self.state = "error"

    def launch_search(self):
        q = self.query.strip()
        if not q or self.state == "loading": return
        self.state = "loading"
        self.error_msg = ""
        self.results = []
        self.total = 0
        self.scroll_y = 0
        self._worker = threading.Thread(target=self._run_search, args=(q, self.exact), daemon=True)
        self._worker.start()

    def _text(self, txt, x, y, color=WHITE, font=None, anchor="topleft"):
        font = font or self.font_body
        surf = font.render(str(txt), True, color)
        rect = surf.get_rect()
        setattr(rect, anchor, (x, y))
        self.screen.blit(surf, rect)

    def _truncate(self, txt, font, max_w):
        txt = str(txt)
        if font.size(txt)[0] <= max_w: return txt
        ell = "…"
        while txt and font.size(txt + ell)[0] > max_w:
            txt = txt[:-1]
        return txt + ell

    def _export_data(self, data, title):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        
        filetypes = [("Fichier JSON", "*.json"), ("Fichier Texte", "*.txt")]
        filepath = filedialog.asksaveasfilename(
            title=title,
            defaultextension=".json",
            filetypes=filetypes,
            initialfile="export"
        )
        root.destroy()

        if filepath:
            try:
                ext = os.path.splitext(filepath)[1].lower()
                with open(filepath, "w", encoding="utf-8") as f:
                    if ext == ".json":
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    else:
                        if isinstance(data, dict):
                            for k, v in data.items():
                                f.write(f"{k.upper()} : {v}\n")
                        elif isinstance(data, list):
                            f.write("\n---\n".join([json.dumps(i, ensure_ascii=False) for i in data]))
                self.save_message = f"Sauvegardé : {os.path.basename(filepath)}"
                self.save_msg_time = pygame.time.get_ticks()
            except Exception as e:
                self.save_message = f"Erreur : {e}"
                self.save_msg_time = pygame.time.get_ticks()

    def draw(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_tick) / 1000.0
        self.last_tick = now
        self.cursor_t += dt

        if self.save_message and now - self.save_msg_time > 3000:
            self.save_message = ""

        w, h = self.screen.get_size()
        self.screen.fill(BG)

        panel = pygame.Rect(40, 30, w - 80, h - 60)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, panel, 1, border_radius=10)

        self._text("RECHERCHE", panel.x + 28, panel.y + 26, MUTED, self.font_tiny)
        self._text("By Lupin", panel.x + 28, panel.y + 44, WHITE, self.font_title)

        mx, my = pygame.mouse.get_pos()

        if self.state == "done" and self.results:
            self.export_rect = pygame.Rect(panel.right - 220, panel.y + 24, 100, 30)
            hov = self.export_rect.collidepoint(mx, my)
            pygame.draw.rect(self.screen, CARD_HOV if hov else CARD, self.export_rect, border_radius=4)
            pygame.draw.rect(self.screen, BORDER, self.export_rect, 1, border_radius=4)
            self._text("EXPORTER", self.export_rect.centerx, self.export_rect.centery, GREY, self.font_tiny, anchor="center")

        self.back_rect = pygame.Rect(panel.right - 100, panel.y + 24, 72, 30)
        hov = self.back_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, CARD_HOV if hov else CARD, self.back_rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER, self.back_rect, 1, border_radius=4)
        self._text("RETOUR", self.back_rect.centerx, self.back_rect.centery, GREY, self.font_tiny, anchor="center")

        y = panel.y + 100
        self._text("RECHERCHER", panel.x + 28, y, MUTED, self.font_tiny)
        y += 18

        self.search_rect = pygame.Rect(panel.x + 28, y, panel.width - 220, 44)
        pygame.draw.rect(self.screen, CARD, self.search_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER_HI, self.search_rect, 1, border_radius=6)

        placeholder = "Nom, prénom ou téléphone…"
        display = self.query if self.query else placeholder
        color = WHITE if self.query else DIM
        cursor = "|" if (self.cursor_t % 1.0) < 0.5 and self.state != "loading" else ""
        if self.query: display = display + cursor
        self._text(display, self.search_rect.x + 14, self.search_rect.centery, color, self.font_body, anchor="midleft")

        self.exact_rect = pygame.Rect(panel.x + 28, y + 56, 18, 18)
        pygame.draw.rect(self.screen, CARD, self.exact_rect, border_radius=3)
        pygame.draw.rect(self.screen, BORDER_HI, self.exact_rect, 1, border_radius=3)
        if self.exact: pygame.draw.rect(self.screen, WHITE, self.exact_rect.inflate(-8, -8), border_radius=1)
        self._text("Phrase exacte", self.exact_rect.right + 10, self.exact_rect.centery, GREY, self.font_small, anchor="midleft")

        self.search_btn_rect = pygame.Rect(self.search_rect.right + 10, self.search_rect.y, 150, 44)
        can = bool(self.query.strip()) and self.state != "loading"
        hov_btn = self.search_btn_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, CARD_HOV if (can and hov_btn) else CARD, self.search_btn_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER_HI if can else BORDER, self.search_btn_rect, 1, border_radius=6)
        label = "RECHERCHER" if self.state != "loading" else "RECHERCHE…"
        self._text(label, self.search_btn_rect.centerx, self.search_btn_rect.centery, WHITE if can else DIM, self.font_tiny, anchor="center")

        status_y = y + 92
        if self.state == "loading":
            self._text("Interrogation de l'index…", panel.x + 28, status_y, GREY, self.font_small)
        elif self.state == "error":
            self._text(self._truncate("Erreur : " + self.error_msg, self.font_small, panel.width - 56), panel.x + 28, status_y, (200, 120, 120), self.font_small)
        elif self.state == "done":
            self._text(f"{self.total} résultat(s)", panel.x + 28, status_y, MUTED, self.font_small)

        if self.save_message:
            self._text(self.save_message, panel.right - 250, status_y, GREEN, self.font_small)

        list_rect = pygame.Rect(panel.x + 28, status_y + 26, panel.width - 56, panel.bottom - status_y - 56)
        pygame.draw.rect(self.screen, BG, list_rect, border_radius=6)
        pygame.draw.rect(self.screen, BORDER, list_rect, 1, border_radius=6)

        if self.state == "idle":
            self._text("Saisissez une requête puis appuyez sur Entrée.", list_rect.centerx, list_rect.centery, MUTED, self.font_small, anchor="center")
        elif self.state == "done" and not self.results:
            self._text("Aucun résultat.", list_rect.centerx, list_rect.centery, MUTED, self.font_small, anchor="center")
        else:
            self._draw_results(list_rect, mx, my)

        if self.max_scroll > 0 and not self.modal_open:
            bar = pygame.Rect(list_rect.right - 6, list_rect.y + 8, 3, int((list_rect.height - 16) * (list_rect.height / (list_rect.height + self.max_scroll))))
            ratio = self.scroll_y / self.max_scroll if self.max_scroll else 0
            bar.y = list_rect.y + 8 + int((list_rect.height - 16 - bar.height) * ratio)
            pygame.draw.rect(self.screen, BORDER_HI, bar, border_radius=2)

        if self.modal_open and self.modal_item:
            self._draw_modal(w, h, mx, my)

    def _draw_results(self, list_rect, mx, my):
        inner = list_rect.inflate(-20, -16)
        row_h = 90
        gap = 8
        content_h = len(self.results) * (row_h + gap)
        self.max_scroll = max(0, content_h - inner.height)
        self.card_rects.clear()

        clip = self.screen.get_clip()
        self.screen.set_clip(inner)

        start_y = inner.y - self.scroll_y
        for i, item in enumerate(self.results):
            cy = start_y + i * (row_h + gap)
            if cy + row_h < inner.y - 20: continue
            if cy > inner.bottom + 20: break

            card = pygame.Rect(inner.x, cy, inner.width, row_h)
            self.card_rects.append((card, item))
            hov = card.collidepoint(mx, my) and inner.collidepoint(mx, my) and not self.modal_open
            
            pygame.draw.rect(self.screen, CARD_HOV if hov else CARD, card, border_radius=6)
            pygame.draw.rect(self.screen, BORDER, card, 1, border_radius=6)
            pygame.draw.rect(self.screen, BORDER_HI, pygame.Rect(card.x, card.y + 12, 2, card.height - 24))

            ext = extract_person_info(item)
            
            nom = ext["nom"].upper()
            prenom = ext["prenom"].capitalize()
            display_name = f"{nom} {prenom}".strip()
            
                                                                     
            if not display_name and ext["allocataire"]:
                display_name = f"Allocataire : {ext['allocataire']}"
            if not display_name:
                display_name = ext["full"] or "Inconnu (données masquées)"
            
            self._text(self._truncate(display_name, self.font_body, card.width - 2 * 14 - 80), card.x + 14, card.y + 16, WHITE, self.font_body)
            
            badge = pygame.Rect(card.right - 14 - 54, card.y + 14, 54, 18)
            pygame.draw.rect(self.screen, BG, badge, border_radius=3)
            pygame.draw.rect(self.screen, BORDER, badge, 1, border_radius=3)
            self._text("DÉTAILS", badge.centerx, badge.centery, MUTED, self.font_tiny, anchor="center")

            info_parts = []
            if "Date de naissance" in ext["details"]: info_parts.append(f"Né(e) le {ext['details']['Date de naissance']}")
            if "Id psp" in ext["details"]: info_parts.append(f"Matricule : {ext['details']['Id psp']}")
                
            info = "   ·   ".join([str(x) for x in info_parts if x])
            if info:
                self._text(self._truncate(info, self.font_small, card.width - 2 * 14), card.x + 14, card.y + 44, GREY, self.font_small)

            source = item.get("source") or item.get("file") or item.get("filename") or item.get("_source") or "Fichier local"
            self._text(self._truncate(source, self.font_tiny, card.width - 2 * 14), card.x + 14, card.y + card.height - 22, MUTED, self.font_tiny)

        self.screen.set_clip(clip)

    def _draw_modal(self, w, h, mx, my):
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        modal_w, modal_h = 700, 500
        modal = pygame.Rect((w - modal_w) // 2, (h - modal_h) // 2, modal_w, modal_h)
        
        pygame.draw.rect(self.screen, PANEL, modal, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_HI, modal, 1, border_radius=10)

        ext = extract_person_info(self.modal_item)
        
        nom = ext["nom"].upper()
        prenom = ext["prenom"].capitalize()
        display_name = f"{nom} {prenom}".strip() or ext["allocataire"] or ext["full"] or "Détails"
        
        self._text(display_name, modal.x + 30, modal.y + 30, WHITE, self.font_modal_title)
        self._text("DONNÉES BRUTES TROUVÉES", modal.x + 30, modal.y + 70, MUTED, self.font_tiny)

        self.modal_export_rect = pygame.Rect(modal.right - 140, modal.y + 24, 80, 24)
        hov = self.modal_export_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, CARD_HOV if hov else CARD, self.modal_export_rect, border_radius=3)
        pygame.draw.rect(self.screen, BORDER_HI, self.modal_export_rect, 1, border_radius=3)
        self._text("EXPORTER", self.modal_export_rect.centerx, self.modal_export_rect.centery, GREY, self.font_tiny, anchor="center")

        self.modal_close_rect = pygame.Rect(modal.right - 40, modal.y + 24, 20, 20)
        pygame.draw.line(self.screen, GREY, (self.modal_close_rect.x, self.modal_close_rect.y), (self.modal_close_rect.right, self.modal_close_rect.bottom), 2)
        pygame.draw.line(self.screen, GREY, (self.modal_close_rect.x, self.modal_close_rect.bottom), (self.modal_close_rect.right, self.modal_close_rect.y), 2)

        content_rect = pygame.Rect(modal.x + 30, modal.y + 110, modal.width - 60, modal.height - 140)
        
        items = list(ext["details"].items())
        row_h = 30
        total_h = len(items) * row_h
        max_scroll = max(0, total_h - content_rect.height)
        
        if self.modal_scroll_y > max_scroll: self.modal_scroll_y = max_scroll
        if self.modal_scroll_y < 0: self.modal_scroll_y = 0

        clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)
        
        y = content_rect.y - self.modal_scroll_y
        for k, v in items:
            if y + row_h > content_rect.y and y < content_rect.bottom:
                self._text(f"{k}", content_rect.x, y, GREY, self.font_small)
                self._text(self._truncate(v, self.font_small, content_rect.width - 200), content_rect.x + 180, y, WHITE, self.font_small)
            y += row_h
            
        self.screen.set_clip(clip)

    def handle_event(self, event):
        if event.type == pygame.QUIT: return "quit"
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.modal_open:
                self.modal_open = False
                return None
            return "back"

        if self.modal_open:
            if event.type == pygame.MOUSEWHEEL:
                self.modal_scroll_y -= event.y * 30
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.modal_close_rect.collidepoint(event.pos):
                    self.modal_open = False
                elif self.modal_export_rect.collidepoint(event.pos):
                    self._export_data(self.modal_item, "Exporter le profil")
            return None

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN: self.launch_search()
            elif event.key == pygame.K_BACKSPACE: self.query = self.query[:-1]
            elif event.key == pygame.K_TAB: self.exact = not self.exact
            elif event.unicode and event.unicode.isprintable(): self.query += event.unicode

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, min(self.max_scroll, self.scroll_y - event.y * 40))

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if self.back_rect.collidepoint(pos): return "back"
            if self.search_btn_rect.collidepoint(pos): self.launch_search()
            if self.exact_rect.collidepoint(pos): self.exact = not self.exact
            if self.export_rect.collidepoint(pos): 
                self._export_data(self.results, "Exporter toute la recherche")

            for rect, item in self.card_rects:
                if rect.collidepoint(pos):
                    self.modal_open = True
                    self.modal_item = item
                    self.modal_scroll_y = 0
                    break

        return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("Recherche")
    
    clock = pygame.time.Clock()
    app = RechercheScreen(screen)
    running = True

    while running:
        for event in pygame.event.get():
            r = app.handle_event(event)
            if r in ("quit", "back"):
                running = False
        app.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

# Dont Use This File On Your Project, This File Contain API Logs.