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
RED       = (200, 120, 120)

                                                                        
                    
                                                                        
SCRIPT_DIR = Path(__file__).resolve().parent
ENV_PATH = SCRIPT_DIR / ".env"
_DEFAULT_API_URL = "https://api.scraphub.org/api"
_LEGACY_API_URL = "https://scraphub-web-backend.fly.dev/api"

def load_env(path: Path):
    if not path.is_file(): return
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line: continue
            key, value = line.split("=", 1)
            key, value = key.strip(), value.strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    value = value[1:-1]
            elif len(value) >= 2 and value[0] == value[-1] == "'":
                value = value[1:-1]
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception as e:
        print(f"[.env] Erreur de lecture : {e}", file=sys.stderr)

load_env(ENV_PATH)

                                                                        
                     
                                                                        
def _request_json(opener, url, payload=None, method="POST"):
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url, data=body, headers=headers, method=method,
    )
    try:
        with opener.open(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        try:
            d = json.loads(raw)
            if e.code == 403 and d.get("error_code") == 1010:
                request_id = d.get("instance")
                message = (
                    "ScrapHub/Cloudflare bloque l'accès de cette application "
                    "(Error 1010). Seul ScrapHub peut autoriser cette requête."
                )
                if request_id:
                    message += f" Identifiant à transmettre au support : {request_id}"
                raise RuntimeError(message) from e
            msg = d.get("error") or d.get("message") or raw
        except json.JSONDecodeError:
            msg = raw or str(e.reason)
        raise RuntimeError(f"HTTP {e.code}: {msg}") from e
    except (urllib.error.URLError, TimeoutError) as e:
        raise RuntimeError(f"API injoignable: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError("Réponse JSON invalide de l'API ScrapHub.") from e


def save_credentials(email, password):
    values = {
        "SCRAPHUB_EMAIL": email,
        "SCRAPHUB_PASSWORD": password,
    }
    lines = ENV_PATH.read_text(encoding="utf-8").splitlines() if ENV_PATH.is_file() else []
    updated = set()
    output = []
    for line in lines:
        key = line.split("=", 1)[0].strip() if "=" in line else ""
        if key in values:
            output.append(f"{key}={json.dumps(values[key], ensure_ascii=False)}")
            updated.add(key)
        else:
            output.append(line)
    for key, value in values.items():
        if key not in updated:
            output.append(f"{key}={json.dumps(value, ensure_ascii=False)}")
    temporary_path = ENV_PATH.with_name(ENV_PATH.name + ".tmp")
    temporary_path.write_text("\n".join(output) + "\n", encoding="utf-8")
    temporary_path.replace(ENV_PATH)
    os.environ.update(values)

class ScraphubClient:
    def __init__(self):
        api_url = os.getenv("SCRAPHUB_API_URL") or _DEFAULT_API_URL
        if api_url.rstrip("/") == _LEGACY_API_URL:
            api_url = _DEFAULT_API_URL
        self.api_url = api_url.rstrip("/")
        self.email = os.getenv("SCRAPHUB_EMAIL")
        self.password = os.getenv("SCRAPHUB_PASSWORD")
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self._logged = False

    def _check_api_url(self):
        if not self.api_url.startswith("https://"):
            raise RuntimeError("SCRAPHUB_API_URL doit utiliser HTTPS.")

    def register(self, email, password):
        self._check_api_url()
        return _request_json(self.opener, f"{self.api_url}/auth/register", {
            "name": email.split("@", 1)[0],
            "email": email,
            "password": password,
            "confirmPassword": password,
        })

    def verify_email(self, email, code):
        self._check_api_url()
        return _request_json(self.opener, f"{self.api_url}/auth/verify-email", {
            "email": email,
            "code": code,
        })

    def login(self, email=None, password=None):
        self._check_api_url()
        self.email = email or self.email
        self.password = password or self.password
        if not self.email or not self.password:
            raise RuntimeError("Saisis ton adresse e-mail et ton mot de passe ScrapHub.")
        _request_json(self.opener, f"{self.api_url}/auth/login", {
            "email": self.email,
            "password": self.password,
        })
        session = _request_json(
            self.opener, f"{self.api_url}/auth/verify", method="GET"
        )
        if isinstance(session, dict) and session.get("authenticated") is False:
            raise RuntimeError("La session ScrapHub n'a pas pu être vérifiée.")
        self._logged = True

    def logout(self):
        if self._logged:
            _request_json(self.opener, f"{self.api_url}/auth/logout", {})
        self._logged = False

    def search(self, query, exact=False, limit=100):
        if not self._logged:
            self.login()
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
        self.auth_screen = not (self.client.email and self.client.password)
        self.auth_mode = "login"
        self.auth_email = self.client.email or ""
        self.auth_password = ""
        self.auth_confirm = ""
        self.auth_code = ""
        self.auth_focus = 0
        self.auth_error = ""
        self.auth_message = ""
        self.auth_loading = False
        self.auth_fields = []
        self.auth_submit_rect = pygame.Rect(0, 0, 0, 0)
        self.auth_toggle_rect = pygame.Rect(0, 0, 0, 0)
        self.account_rect = pygame.Rect(0, 0, 0, 0)

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

    def _submit_auth(self):
        if self.auth_loading:
            return
        email = self.auth_email.strip()
        if self.auth_mode == "verify":
            if not email or not self.auth_code.strip():
                self.auth_error = "Saisis ton e-mail et le code reçu."
                return
            action = "verify"
            args = (email, self.auth_password, self.auth_code.strip())
        else:
            if not email or "@" not in email:
                self.auth_error = "Saisis une adresse e-mail valide."
                return
            if not self.auth_password:
                self.auth_error = "Saisis ton mot de passe."
                return
            if self.auth_mode == "register":
                if self.auth_password != self.auth_confirm:
                    self.auth_error = "Les deux mots de passe ne correspondent pas."
                    return
                action = "register"
            else:
                action = "login"
            args = (email, self.auth_password)

        self.auth_error = ""
        self.auth_message = "Connexion en cours…" if action == "login" else (
            "Vérification en cours…" if action == "verify" else "Création du compte…"
        )
        self.auth_loading = True
        self._worker = threading.Thread(
            target=self._run_auth, args=(action, *args), daemon=True
        )
        self._worker.start()

    def _run_auth(self, action, email, password, code=None):
        try:
            if action == "register":
                self.client.register(email, password)
                self.auth_mode = "verify"
                self.auth_email = email
                self.auth_password = password
                self.auth_code = ""
                self.auth_focus = 0
                self.auth_message = "Code envoyé par e-mail. Saisis-le ci-dessous."
            elif action == "logout":
                if self.client.email and self.client.password and not self.client._logged:
                    self.client.login()
                self.client.logout()
                save_credentials("", "")
                self.client.email = ""
                self.client.password = ""
                self.auth_email = ""
                self.auth_password = ""
                self.auth_confirm = ""
                self.auth_code = ""
                self.auth_mode = "login"
                self.auth_focus = 0
                self.auth_screen = True
                self.auth_message = ""
            else:
                if action == "verify":
                    self.client.verify_email(email, code)
                self.client.login(email, password)
                save_credentials(email, password)
                self.auth_screen = False
                self.auth_message = ""
                self.auth_error = ""
        except Exception as error:
            self.auth_error = str(error)
        finally:
            self.auth_loading = False

    def _draw_auth(self, width, height, mouse_pos):
        overlay = pygame.Surface((width, height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        self.screen.blit(overlay, (0, 0))

        card_width = min(540, width - 48)
        card_height = 460 if self.auth_mode == "register" else 400
        if self.auth_mode == "verify":
            card_height = 360
        card = pygame.Rect(
            (width - card_width) // 2, (height - card_height) // 2,
            card_width, card_height,
        )
        pygame.draw.rect(self.screen, PANEL, card, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_HI, card, 1, border_radius=10)
        title = {
            "login": "Connexion ScrapHub",
            "register": "Créer un compte ScrapHub",
            "verify": "Vérifier ton adresse e-mail",
        }[self.auth_mode]
        self._text(title, card.centerx, card.y + 30, WHITE, self.font_title, anchor="midtop")
        self._text(
            "Tes identifiants seront conservés localement dans settings/options/.env.",
            card.centerx, card.y + 70, MUTED, self.font_small, anchor="midtop",
        )

        fields = [("E-mail", "email")]
        if self.auth_mode != "verify":
            fields.append(("Mot de passe", "password"))
        if self.auth_mode == "register":
            fields.append(("Confirmer le mot de passe", "confirm"))
        if self.auth_mode == "verify":
            fields.append(("Code reçu par e-mail", "code"))

        field_values = {
            "email": self.auth_email,
            "password": self.auth_password,
            "confirm": self.auth_confirm,
            "code": self.auth_code,
        }
        self.auth_fields = []
        field_y = card.y + 112
        field_h = 44
        for index, (label, key) in enumerate(fields):
            self._text(label, card.x + 36, field_y, GREY, self.font_small)
            rect = pygame.Rect(card.x + 36, field_y + 20, card.width - 72, field_h)
            focused = self.auth_focus == index
            pygame.draw.rect(self.screen, CARD, rect, border_radius=5)
            pygame.draw.rect(
                self.screen, BORDER_HI if focused else BORDER, rect, 1, border_radius=5
            )
            value = field_values[key]
            if key in ("password", "confirm"):
                value = "*" * len(value)
            if focused and not self.auth_loading and (self.cursor_t % 1.0) < 0.5:
                value += "|"
            self._text(value or " ", rect.x + 12, rect.centery, WHITE, self.font_body, anchor="midleft")
            self.auth_fields.append((rect, key))
            field_y += 78

        message_y = card.bottom - 118
        if self.auth_error:
            self._text(
                self._truncate(self.auth_error, self.font_small, card.width - 72),
                card.centerx, message_y, RED, self.font_small, anchor="midtop",
            )
        elif self.auth_message:
            self._text(
                self._truncate(self.auth_message, self.font_small, card.width - 72),
                card.centerx, message_y, GREY, self.font_small, anchor="midtop",
            )

        self.auth_submit_rect = pygame.Rect(card.x + 36, card.bottom - 82, card.width - 72, 38)
        hover = self.auth_submit_rect.collidepoint(mouse_pos)
        pygame.draw.rect(
            self.screen, CARD_HOV if hover else CARD, self.auth_submit_rect, border_radius=5
        )
        pygame.draw.rect(self.screen, BORDER_HI, self.auth_submit_rect, 1, border_radius=5)
        submit_label = {
            "login": "SE CONNECTER",
            "register": "CRÉER LE COMPTE ET ENVOYER LE CODE",
            "verify": "VÉRIFIER LE CODE ET SE CONNECTER",
        }[self.auth_mode]
        if self.auth_loading:
            submit_label = "VEUILLE PATIENTER…"
        self._text(
            submit_label, self.auth_submit_rect.centerx, self.auth_submit_rect.centery,
            WHITE, self.font_tiny, anchor="center",
        )

        self.auth_toggle_rect = pygame.Rect(card.x + 36, card.bottom - 36, card.width - 72, 24)
        if self.auth_mode == "verify":
            toggle_label = "Retour à la connexion"
        elif self.auth_mode == "register":
            toggle_label = "J'ai déjà un compte — Se connecter"
        else:
            toggle_label = "Pas encore de compte — Créer un compte"
        self._text(
            toggle_label, self.auth_toggle_rect.centerx, self.auth_toggle_rect.centery,
            MUTED, self.font_small, anchor="center",
        )

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
        if self.auth_screen:
            self._draw_auth(w, h, (mx, my))
            return

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

        self.account_rect = pygame.Rect(panel.right - 310, panel.y + 24, 80, 30)
        account_hover = self.account_rect.collidepoint(mx, my)
        pygame.draw.rect(self.screen, CARD_HOV if account_hover else CARD, self.account_rect, border_radius=4)
        pygame.draw.rect(self.screen, BORDER, self.account_rect, 1, border_radius=4)
        self._text("COMPTE", self.account_rect.centerx, self.account_rect.centery, GREY, self.font_tiny, anchor="center")

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

        if self.auth_screen:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "back"
                if event.key == pygame.K_TAB:
                    self.auth_focus = (self.auth_focus + 1) % max(1, len(self.auth_fields))
                elif event.key == pygame.K_RETURN:
                    self._submit_auth()
                elif event.key == pygame.K_BACKSPACE and not self.auth_loading:
                    if self.auth_fields:
                        key = self.auth_fields[self.auth_focus][1]
                        attr = {
                            "email": "auth_email",
                            "password": "auth_password",
                            "confirm": "auth_confirm",
                            "code": "auth_code",
                        }[key]
                        setattr(self, attr, getattr(self, attr)[:-1])
                elif event.unicode and event.unicode.isprintable() and not self.auth_loading:
                    if self.auth_fields:
                        key = self.auth_fields[self.auth_focus][1]
                        attr = {
                            "email": "auth_email",
                            "password": "auth_password",
                            "confirm": "auth_confirm",
                            "code": "auth_code",
                        }[key]
                        setattr(self, attr, getattr(self, attr) + event.unicode)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for index, (rect, _) in enumerate(self.auth_fields):
                    if rect.collidepoint(event.pos):
                        self.auth_focus = index
                        break
                else:
                    if self.auth_submit_rect.collidepoint(event.pos):
                        self._submit_auth()
                    elif self.auth_toggle_rect.collidepoint(event.pos) and not self.auth_loading:
                        if self.auth_mode == "verify":
                            self.auth_mode = "login"
                            self.auth_code = ""
                        else:
                            self.auth_mode = "login" if self.auth_mode == "register" else "register"
                        self.auth_focus = 0
                        self.auth_error = ""
                        self.auth_message = ""
            return None

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
            if self.account_rect.collidepoint(pos) and not self.auth_loading:
                self.auth_loading = True
                self.auth_error = ""
                self.auth_message = "Déconnexion en cours…"
                self._worker = threading.Thread(
                    target=self._run_auth, args=("logout", "", ""), daemon=True
                )
                self._worker.start()
                return None
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