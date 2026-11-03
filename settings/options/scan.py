import json
import os
import re
import sys
import threading
import urllib.parse
import urllib.request
import tkinter as tk
from tkinter import filedialog
import webbrowser

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
LINK_BLUE = (130, 170, 255)

                                                                        
       
                                                                        
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^(?:\+33|0)[1-9](?:[ .-]?\d{2}){4}$")

                                                                        
              
                                                                        
class OsintEngine:
    def __init__(self, on_finish):
        self.on_finish = on_finish
        self.results = []
        self.is_running = False
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Accept": "application/vnd.github+json"
        }

    def _add_result(self, category, platform, data, description, url=None):
        self.results.append({
            "category": category,
            "platform": platform,
            "data": data,
            "description": description,
            "url": url
        })

    def _search_github_emails(self, pseudo):
        """Cherche les emails dans les commits GitHub via l'API publique."""
        if not pseudo: return
        
                                                                      
        events_url = f"https://api.github.com/users/{pseudo}/events/public"
        emails_found = set()
        
        try:
            req = urllib.request.Request(events_url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                events = json.loads(resp.read().decode("utf-8"))
                for event in events:
                    if event.get("type") == "PushEvent":
                        commits = event.get("payload", {}).get("commits", [])
                        for commit in commits:
                            author_email = commit.get("author", {}).get("email")
                            if author_email and not author_email.endswith("users.noreply.github.com"):
                                emails_found.add(author_email)
        except Exception:
            pass

                                                                                        
        if not emails_found:
            search_url = f"https://api.github.com/search/commits?q=author:{pseudo}"
            try:
                req = urllib.request.Request(search_url, headers=self.headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    for item in data.get("items", [])[:10]:                             
                        email = item.get("commit", {}).get("author", {}).get("email")
                        if email and not email.endswith("users.noreply.github.com"):
                            emails_found.add(email)
            except Exception:
                pass

        if emails_found:
            for email in emails_found:
                self._add_result("GitHub", "Email trouvé", email, f"Email utilisé dans les commits de {pseudo}")
        else:
            self._add_result("GitHub", "Recherche email", "Aucun email public", f"Aucun email visible dans les commits de {pseudo}")

    def start(self, data):
        self.is_running = True
        self.results = []
        
        pseudo = data.get("pseudo", "").strip()
        nom = data.get("nom", "").strip()
        prenom = data.get("prenom", "").strip()
        full_name = f"{prenom} {nom}".strip()
        
                                               
        if pseudo:
            self._search_github_emails(pseudo)
                                          
            self._add_result("GitHub", "Profil", pseudo, "Ouvrir le profil GitHub", f"https://github.com/{pseudo}")

                                                      
        if full_name:
            query_jss = f'site:jss.fr "{full_name}"'
            url_jss = f"https://www.google.com/search?q={urllib.parse.quote_plus(query_jss)}"
            self._add_result("Journaux Officiels", "JSS.fr", "Recherche Google", f"Chercher {full_name} sur JSS.fr", url_jss)

                                                                    
        if full_name:
            self._add_result("Moteurs de recherche", "Google", "Recherche d'identité", f"Rechercher {full_name} sur Google", f"https://www.google.com/search?q={urllib.parse.quote_plus(full_name)}")
            self._add_result("Moteurs de recherche", "Bing", "Recherche d'identité", f"Rechercher {full_name} sur Bing", f"https://www.bing.com/search?q={urllib.parse.quote_plus(full_name)}")
            self._add_result("Moteurs de recherche", "LinkedIn", "Recherche professionnelle", f"Chercher {full_name} sur LinkedIn", f"https://www.linkedin.com/search/results/all/?keywords={urllib.parse.quote_plus(full_name)}")

                                  
        tel = data.get("tel", "").strip()
        if tel:
            clean_tel = re.sub(r"\s+", "", tel)
            self._add_result("Annuaire Téléphonique", "Pages Blanches", "Annuaire officiel", f"Chercher le {clean_tel} sur Pages Blanches", f"https://www.pagesjaunes.fr/pagesblanches/recherche?quoiqui={clean_tel}")
            self._add_result("Annuaire Téléphonique", "Truecaller", "Identification", f"Chercher le {clean_tel} sur Truecaller", f"https://www.truecaller.com/search/fr/{clean_tel}")

                                      
        email = data.get("mail", "").strip()
        if email:
            self._add_result("Fuites de données", "Have I Been Pwned", "Vérification email", f"Vérifier les fuites pour {email}", f"https://haveibeenpwned.com/account/{email}")
            self._add_result("Fuites de données", "Epieos", "Email", f"Analyse pour {email}", f"https://epieos.com/?q={email}")
            
        self.is_running = False
        self.on_finish()

                                                                        
                                         
                                                                        
class ScanIdentiteScreen:
    def __init__(self, screen):
        self.screen = screen
        self.font_title = pygame.font.SysFont("georgia", 26)
        self.font_modal_title = pygame.font.SysFont("georgia", 24)
        self.font_body  = pygame.font.SysFont("helvetica", 14)
        self.font_small = pygame.font.SysFont("helvetica", 12)
        self.font_tiny  = pygame.font.SysFont("helvetica", 10)

        self.engine = OsintEngine(self._on_scan_finish)
        
        self.inputs = {"pseudo": "", "nom": "", "prenom": "", "mail": "", "tel": ""}
        self.fields = ["pseudo", "nom", "prenom", "mail", "tel"]
        self.active_field = 0
        self.cursor_t = 0.0
        self.last_tick = pygame.time.get_ticks()

        self.state = "idle"
        self.error_msg = ""
        
        self.input_rects = []
        self.start_btn_rect = pygame.Rect(0, 0, 0, 0)
        self.back_rect = pygame.Rect(0, 0, 0, 0)
        self.export_rect = pygame.Rect(0, 0, 0, 0)
        
        self.scroll_y = 0
        self.modal_open = False
        self.modal_close_rect = pygame.Rect(0, 0, 0, 0)
        self.link_rects = []
        self.save_message = ""
        self.save_msg_time = 0

        self.load_angle = 0

    def _on_scan_finish(self):
        self.state = "done"
        self.modal_open = True

    def _text(self, txt, x, y, color=WHITE, font=None, anchor="topleft"):
        font = font or self.font_body
        surf = font.render(str(txt), True, color)
        rect = surf.get_rect()
        setattr(rect, anchor, (x, y))
        self.screen.blit(surf, rect)
        return rect

    def _render_multiline(self, text, x, y, max_w, color=MUTED, font=None):
        font = font or self.font_tiny
        words = text.split()
        lines = []
        current = ""
        for w in words:
            test = current + " " + w if current else w
            if font.size(test)[0] <= max_w:
                current = test
            else:
                if current: lines.append(current)
                current = w
        if current: lines.append(current)

        for line in lines:
            self._text(line, x, y, color, font)
            y += font.get_height() + 2
        return y

    def _is_valid_email(self, email):
        return bool(EMAIL_REGEX.match(email))

    def _is_valid_phone(self, phone):
        return bool(PHONE_REGEX.match(phone.replace(" ", "")))

    def launch_scan(self):
        self.error_msg = ""
        
        if not self.inputs["pseudo"].strip():
            self.error_msg = "Le pseudo est obligatoire."
            return

        email = self.inputs["mail"].strip()
        if email and not self._is_valid_email(email):
            self.error_msg = "Format d'email invalide."
            return

        phone = self.inputs["tel"].strip()
        if phone and not self._is_valid_phone(phone):
            self.error_msg = "Format de téléphone invalide."
            return

        self.state = "running"
        self.scroll_y = 0
        threading.Thread(target=self.engine.start, args=(self.inputs.copy(),), daemon=True).start()

    def _export_data(self):
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        filetypes = [("Fichier JSON", "*.json"), ("Fichier Texte", "*.txt")]
        filepath = filedialog.asksaveasfilename(
            title="Exporter le rapport",
            defaultextension=".json",
            filetypes=filetypes,
            initialfile="rapport"
        )
        root.destroy()

        if filepath:
            try:
                ext = os.path.splitext(filepath)[1].lower()
                with open(filepath, "w", encoding="utf-8") as f:
                    if ext == ".json":
                        json.dump(self.engine.results, f, indent=2, ensure_ascii=False)
                    else:
                        for r in self.engine.results:
                            f.write(f"[{r['category']}] {r['platform']}\n")
                            f.write(f"STATUT: {r['data']}\n")
                            f.write(f"DETAILS: {r['description']}\n")
                            if r['url']: f.write(f"URL: {r['url']}\n")
                            f.write("\n")
                self.save_message = f"Rapport exporté."
                self.save_msg_time = pygame.time.get_ticks()
            except Exception as e:
                self.save_message = f"Erreur d'export."
                self.save_msg_time = pygame.time.get_ticks()

    def draw(self):
        now = pygame.time.get_ticks()
        dt = (now - self.last_tick) / 1000.0
        self.last_tick = now
        self.cursor_t += dt
        self.load_angle += dt * 5

        if self.save_message and now - self.save_msg_time > 3000:
            self.save_message = ""

        w, h = self.screen.get_size()
        self.screen.fill(BG)

        panel = pygame.Rect(40, 30, w - 80, h - 60)
        pygame.draw.rect(self.screen, PANEL, panel, border_radius=10)
        pygame.draw.rect(self.screen, BORDER, panel, 1, border_radius=10)

        self._text("SCAN IDENTITÉ", panel.x + 28, panel.y + 26, MUTED, self.font_tiny)
        self._text("Moteur", panel.x + 28, panel.y + 44, WHITE, self.font_title)

        mx, my = pygame.mouse.get_pos()

        if self.state == "done" and self.engine.results:
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

        form_w = 400
        form_x = panel.x + 100
        pygame.draw.line(self.screen, BORDER, (form_x + form_w + 50, panel.y + 100), (form_x + form_w + 50, panel.bottom - 20), 1)

        y = panel.y + 120
        self._text("PARAMÈTRES DU SCAN", form_x, y, MUTED, self.font_tiny)
        y += 30

        self.input_rects.clear()
        for field in self.fields:
            label = field.capitalize() + (" *" if field == "pseudo" else "")
            self._text(label, form_x, y, GREY, self.font_small)
            
            rect = pygame.Rect(form_x, y + 20, form_w, 38)
            active = (self.fields[self.active_field] == field) and self.state == "idle"
            
            pygame.draw.rect(self.screen, CARD, rect, border_radius=6)
            border_color = BORDER_HI if active else BORDER
            if field == "mail" and self.inputs["mail"] and not self._is_valid_email(self.inputs["mail"]): border_color = RED
            if field == "tel" and self.inputs["tel"] and not self._is_valid_phone(self.inputs["tel"]): border_color = RED
            
            pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=6)
            
            val = self.inputs[field]
            cursor = "|" if active and (self.cursor_t % 1.0) < 0.5 else ""
            self._text(val + cursor if val else "", rect.x + 10, rect.centery, WHITE, self.font_body, anchor="midleft")
            
            self.input_rects.append((rect, field))
            y += 70

        self.start_btn_rect = pygame.Rect(form_x, y + 20, form_w, 44)
        can_start = bool(self.inputs["pseudo"].strip()) and self.state in ("idle", "done")
        hov = self.start_btn_rect.collidepoint(mx, my)
        
        if self.state == "running":
            pygame.draw.rect(self.screen, CARD, self.start_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, BORDER_HI, self.start_btn_rect, 1, border_radius=6)
            self._text("ANALYSE EN COURS...", self.start_btn_rect.centerx, self.start_btn_rect.centery - 8, GREY, self.font_tiny, anchor="center")
            
            import math
            cx, cy = self.start_btn_rect.centerx, self.start_btn_rect.bottom - 12
            for i in range(8):
                angle = self.load_angle + (i * math.pi / 4)
                alpha = int(255 * (i / 8.0))
                px = cx + int(12 * math.cos(angle))
                py = cy + int(12 * math.sin(angle))
                pygame.draw.circle(self.screen, (alpha, alpha, alpha), (px, py), 2)
        else:
            pygame.draw.rect(self.screen, CARD_HOV if (can_start and hov) else CARD, self.start_btn_rect, border_radius=6)
            pygame.draw.rect(self.screen, BORDER_HI if can_start else BORDER, self.start_btn_rect, 1, border_radius=6)
            self._text("LANCER LE SCAN", self.start_btn_rect.centerx, self.start_btn_rect.centery, WHITE if can_start else DIM, self.font_tiny, anchor="center")

        if self.error_msg:
            self._text(self.error_msg, form_x, self.start_btn_rect.bottom + 10, RED, self.font_small)

        if self.save_message:
            self._text(self.save_message, form_x, self.start_btn_rect.bottom + 30, GREEN, self.font_small)

        info_x = form_x + form_w + 100
        info_y = panel.y + 120
        self._text("RÉSULTATS TROUVÉS", info_x, info_y, MUTED, self.font_tiny)
        
        if self.state == "idle":
            self._text("Le scan n'a pas encore été lancé.", info_x, info_y + 30, DIM, self.font_body)
        elif self.state == "running":
            self._text("Interrogation des moteurs...", info_x, info_y + 30, GREY, self.font_body)
        elif self.state == "done":
            count = len(self.engine.results)
            self._text(f"{count} élément(s) trouvé(s).", info_x, info_y + 30, WHITE, self.font_body)
            self._text("Cliquez sur 'LANCER LE SCAN' pour voir le rapport.", info_x, info_y + 55, MUTED, self.font_small)

        if self.modal_open:
            self._draw_modal(w, h, mx, my)

    def _draw_modal(self, w, h, mx, my):
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 210))
        self.screen.blit(overlay, (0, 0))

        modal_w, modal_h = 850, 600
        modal = pygame.Rect((w - modal_w) // 2, (h - modal_h) // 2, modal_w, modal_h)
        
        pygame.draw.rect(self.screen, PANEL, modal, border_radius=10)
        pygame.draw.rect(self.screen, BORDER_HI, modal, 1, border_radius=10)

        self._text("RAPPORT", modal.x + 30, modal.y + 30, WHITE, self.font_modal_title)
        self._text("CLIQUEZ SUR UN LIEN POUR L'OUVRIR", modal.x + 30, modal.y + 65, MUTED, self.font_tiny)

        self.modal_close_rect = pygame.Rect(modal.right - 40, modal.y + 30, 20, 20)
        pygame.draw.line(self.screen, GREY, (self.modal_close_rect.x, self.modal_close_rect.y), (self.modal_close_rect.right, self.modal_close_rect.bottom), 2)
        pygame.draw.line(self.screen, GREY, (self.modal_close_rect.x, self.modal_close_rect.bottom), (self.modal_close_rect.right, self.modal_close_rect.y), 2)

        content_rect = pygame.Rect(modal.x + 30, modal.y + 100, modal.width - 60, modal.height - 130)
        
        clip = self.screen.get_clip()
        self.screen.set_clip(content_rect)
        
        self.link_rects.clear()
        current_cat = None
        y = content_rect.y - self.scroll_y
        
        for r in self.engine.results:
            if r["category"] != current_cat:
                current_cat = r["category"]
                if y + 30 > content_rect.y and y < content_rect.bottom:
                    self._text(current_cat.upper(), content_rect.x, y + 10, MUTED, self.font_tiny)
                y += 30

            row_height = 65
            if r["description"]:
                row_height += 15

            if y + row_height > content_rect.y and y < content_rect.bottom:
                link_hitbox = pygame.Rect(content_rect.x, y, content_rect.width, row_height)
                if r["url"]:
                    hov = link_hitbox.collidepoint(mx, my) and content_rect.collidepoint(mx, my)
                    if hov:
                        pygame.draw.rect(self.screen, CARD_HOV, link_hitbox, border_radius=4)
                    self.link_rects.append((link_hitbox, r["url"]))

                self._text(r["platform"], content_rect.x + 10, y + 12, LINK_BLUE if r["url"] else GREY, self.font_small)
                self._text(r["data"], content_rect.x + 150, y + 12, WHITE, self.font_small)
                
                if r["description"]:
                    self._text(r["description"], content_rect.x + 150, y + 32, MUTED, self.font_tiny)
                    
                                        
                btn_open = pygame.Rect(content_rect.right - 70, y + 18, 60, 24)
                hov_btn = btn_open.collidepoint(mx, my) and content_rect.collidepoint(mx, my)
                pygame.draw.rect(self.screen, CARD if not hov_btn else BORDER_HI, btn_open, border_radius=4)
                pygame.draw.rect(self.screen, BORDER, btn_open, 1, border_radius=4)
                self._text("OUVRIR", btn_open.centerx, btn_open.centery, GREY, self.font_tiny, anchor="center")
            
            y += row_height
            
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
                self.scroll_y = max(0, self.scroll_y - event.y * 40)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.modal_close_rect.collidepoint(event.pos):
                    self.modal_open = False
                for rect, url in self.link_rects:
                    if rect.collidepoint(event.pos):
                        webbrowser.open(url)
                        break
            return None

        if self.state == "idle":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.active_field = (self.active_field + 1) % len(self.fields)
                elif event.key == pygame.K_RETURN:
                    self.launch_scan()
                elif event.key == pygame.K_BACKSPACE:
                    field = self.fields[self.active_field]
                    self.inputs[field] = self.inputs[field][:-1]
                elif event.unicode and event.unicode.isprintable():
                    field = self.fields[self.active_field]
                    self.inputs[field] += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                for rect, field in self.input_rects:
                    if rect.collidepoint(pos):
                        self.active_field = self.fields.index(field)
                if self.start_btn_rect.collidepoint(pos):
                    self.launch_scan()
                if self.back_rect.collidepoint(pos):
                    return "back"

        elif self.state == "done":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos
                if self.back_rect.collidepoint(pos): return "back"
                if self.export_rect.collidepoint(pos): self._export_data()
                if self.start_btn_rect.collidepoint(pos):
                    self.modal_open = True

        return None

def main():
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN | pygame.NOFRAME)
    pygame.display.set_caption("By Lupin")
    clock = pygame.time.Clock()
    app = ScanIdentiteScreen(screen)
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