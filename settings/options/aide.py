import customtkinter as ctk
import tkinter as tk
import os
import subprocess
import sys

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

                                                   
BG      = "#0A0A0A"
PANEL   = "#0D0D0D"
CARD    = "#101010"
HOVER   = "#161616"
BORDER  = "#1C1C1C"
WHITE   = "#EDEDED"
GREY    = "#8A8A8A"
MUTED   = "#4A4A4A"

SERIF   = "Georgia"
SANS    = "Helvetica"

MODULES = [
    {
        "name": "Version orale",
        "file": "version_orale.py",
        "icon": "mic",
        "description": "Fonctionnalités vocales.",
        "details": [
            "Accéder à l'interface orale.",
            "Découvrir les commandes disponibles.",
            "Consulter les fonctions vocales."
        ]
    },
    {
        "name": "Scan identité",
        "file": "scan.py",
        "icon": "scan",
        "description": "Module identité.",
        "details": [
            "Accéder au module de scan.",
            "Consulter les informations disponibles.",
            "Retrouver les résultats enregistrés."
        ]
    },
    {
        "name": "Tableau",
        "file": "tableau.py",
        "icon": "dashboard",
        "description": "Tableau de bord.",
        "details": [
            "Consulter le tableau de bord.",
            "Visualiser les données disponibles.",
            "Accéder aux informations principales."
        ]
    },
    {
        "name": "Ajouter personne",
        "file": "ajouter_personne.py",
        "icon": "user",
        "description": "Fiches personnalisées.",
        "details": [
            "Créer une nouvelle fiche.",
            "Ajouter des photos.",
            "Créer des catégories personnalisées.",
            "Consulter les informations enregistrées."
        ]
    },
    {
        "name": "Scan réseau",
        "file": "scan_reseau.py",
        "icon": "network",
        "description": "Informations réseau.",
        "details": [
            "Interroger les DNS.",
            "Consulter les certificats TLS.",
            "Examiner les réponses HTTP.",
            "Consulter les résultats des audits autorisés."
        ]
    },
    {
        "name": "Recherche",
        "file": "recherche.py",
        "icon": "search",
        "description": "Recherche rapide.",
        "details": [
            "Effectuer une recherche.",
            "Consulter les résultats.",
            "Retrouver les informations utiles."
        ]
    },
    {
        "name": "Aide",
        "file": "aide.py",
        "icon": "help",
        "description": "Centre d'aide.",
        "details": [
            "Découvrir les différents modules.",
            "Comprendre les fonctionnalités.",
            "Consulter les conseils d'utilisation."
        ]
    },
    {
        "name": "Dev Space",
        "file": "dev_space.py",
        "icon": "code",
        "description": "Environnement développeur.",
        "details": [
            "Découvrir les outils développeur.",
            "Consulter les fonctions techniques.",
            "Accéder à votre espace de développement."
        ]
    }
]


class Icon(tk.Canvas):
    """Icônes dessinées à la main, trait fin, style minimal."""

    def __init__(self, parent, name, size=18, color=WHITE):
        bg = self._resolve_bg(parent)
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0)
        self.name = name
        self.size = size
        self.color = color
        self.draw()

    @staticmethod
    def _resolve_bg(widget, fallback=BG):
        current = widget
        while current is not None:
            try:
                if isinstance(current, ctk.CTkFrame):
                    fg = current.cget("fg_color")
                    if isinstance(fg, (tuple, list)):
                        fg = fg[1] if ctk.get_appearance_mode() == "Dark" else fg[0]
                    if fg and fg != "transparent":
                        return fg
                elif isinstance(current, tk.Widget):
                    bg = current.cget("bg")
                    if bg and bg != "transparent":
                        return bg
            except Exception:
                pass
            current = current.master
        return fallback

    def line(self, *points, width=1.0):
        self.create_line(*points, fill=self.color, width=width,
                         capstyle=tk.ROUND, joinstyle=tk.ROUND)

    def draw(self):
        s = self.size
        c = self.color

        if self.name == "search":
            self.create_oval(s*.12, s*.12, s*.68, s*.68, outline=c, width=1.0)
            self.line(s*.61, s*.61, s*.88, s*.88)

        elif self.name == "user":
            self.create_oval(s*.34, s*.12, s*.66, s*.44, outline=c, width=1.0)
            self.create_arc(s*.14, s*.39, s*.86, s*.98, start=0, extent=180,
                            style=tk.ARC, outline=c, width=1.0)

        elif self.name == "user-plus":
            self.draw_user()
            self.line(s*.78, s*.22, s*.78, s*.52)
            self.line(s*.63, s*.37, s*.93, s*.37)

        elif self.name == "scan":
            self.line(s*.12, s*.32, s*.12, s*.12, s*.32, s*.12)
            self.line(s*.68, s*.12, s*.88, s*.12, s*.88, s*.32)
            self.line(s*.12, s*.68, s*.12, s*.88, s*.32, s*.88)
            self.line(s*.68, s*.88, s*.88, s*.88, s*.88, s*.68)
            self.line(s*.2, s*.5, s*.8, s*.5)

        elif self.name == "dashboard":
            self.create_rectangle(s*.12, s*.12, s*.88, s*.88, outline=c, width=1.0)
            self.line(s*.5, s*.12, s*.5, s*.88)
            self.line(s*.12, s*.5, s*.88, s*.5)

        elif self.name == "network":
            points = [(s*.5, s*.16), (s*.2, s*.75), (s*.8, s*.75), (s*.5, s*.16)]
            self.line(*[v for p in points for v in p])
            for x, y in points[:3]:
                self.create_oval(x-s*.08, y-s*.08, x+s*.08, y+s*.08,
                                 fill=BG, outline=c, width=1.0)

        elif self.name == "mic":
            self.create_oval(s*.37, s*.12, s*.63, s*.62, outline=c, width=1.0)
            self.create_arc(s*.22, s*.3, s*.78, s*.78, start=180, extent=180,
                            style=tk.ARC, outline=c, width=1.0)
            self.line(s*.5, s*.78, s*.5, s*.92)
            self.line(s*.34, s*.92, s*.66, s*.92)

        elif self.name == "help":
            self.create_oval(s*.1, s*.1, s*.9, s*.9, outline=c, width=1.0)
            self.create_text(s*.5, s*.48, text="?",
                             fill=c, font=(SERIF, int(s*.55)))

        elif self.name == "code":
            self.line(s*.37, s*.25, s*.12, s*.5, s*.37, s*.75)
            self.line(s*.63, s*.25, s*.88, s*.5, s*.63, s*.75)
            self.line(s*.56, s*.16, s*.44, s*.84)

        elif self.name == "arrow":
            self.line(s*.18, s*.5, s*.82, s*.5)
            self.line(s*.58, s*.25, s*.82, s*.5, s*.58, s*.75)

    def draw_user(self):
        s = self.size
        self.create_oval(s*.34, s*.1, s*.66, s*.42, outline=self.color, width=1.0)
        self.create_arc(s*.12, s*.4, s*.88, s*.98, start=0, extent=180,
                        style=tk.ARC, outline=self.color, width=1.0)


class HelpApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Centre d'aide")
        self.geometry("1200x800")
        self.configure(fg_color=BG)
        self.attributes("-fullscreen", True)

        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.bind("<F11>", self.toggle_fullscreen)

        self.search_value = tk.StringVar()
        self.show_home()

    def toggle_fullscreen(self, event=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def button(self, parent, text, command, width=100):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=26,
            fg_color="transparent",
            hover_color=HOVER,
            text_color=GREY,
            border_width=1,
            border_color=BORDER,
            corner_radius=2,
            font=(SANS, 8)
        )

    def sidebar(self, active=None):
        side = ctk.CTkFrame(self, width=180, corner_radius=0,
                            fg_color=PANEL, border_width=0)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        ctk.CTkFrame(side, width=1, fg_color=BORDER).place(relx=1.0, rely=0,
                                                           relheight=1.0, anchor="ne")

        brand = ctk.CTkFrame(side, fg_color=PANEL)
        brand.pack(fill="x", padx=18, pady=(24, 22))

        ctk.CTkLabel(brand, text="", font=(SERIF, 13),
                     text_color=WHITE).pack(anchor="w")

        ctk.CTkLabel(brand, text="aide",
                     font=(SERIF, 8, "italic"), text_color=MUTED).pack(anchor="w", pady=(2, 0))

        self.nav_item(side, "home", "Accueil", self.show_home)
        self.nav_item(side, "help", "Centre d'aide", self.show_home)

        ctk.CTkLabel(side, text="MODULES", text_color=MUTED,
                     font=(SANS, 7)).pack(anchor="w", padx=20, pady=(18, 8))

        for module in MODULES:
            self.nav_item(
                side,
                module["icon"],
                module["name"],
                lambda m=module: self.show_module(m),
                module["name"] == active
            )

        ctk.CTkLabel(side, text="assistance", text_color=MUTED,
                     font=(SERIF, 8, "italic")).pack(side="bottom", pady=14)

    def nav_item(self, parent, icon_name, title, command, active=False):
        frame = ctk.CTkFrame(parent, fg_color="transparent", corner_radius=0)
        frame.pack(fill="x", padx=10, pady=0)

        if active:
            ctk.CTkFrame(frame, width=1, fg_color=WHITE).pack(side="left", fill="y")

        icon = Icon(frame, icon_name, 13, WHITE if active else MUTED)
        icon.pack(side="left", padx=(10, 8), pady=7)

        label = ctk.CTkLabel(
            frame,
            text=title,
            text_color=WHITE if active else GREY,
            font=(SANS, 9)
        )
        label.pack(side="left", pady=7)

        for widget in (frame, icon, label):
            widget.bind("<Button-1>", lambda e, c=command: c())
            widget.bind("<Enter>", lambda e, f=frame: f.configure(fg_color=HOVER))
            widget.bind("<Leave>", lambda e, f=frame: f.configure(fg_color="transparent"))

    def content(self):
        self.main = ctk.CTkFrame(self, fg_color=BG, corner_radius=0)
        self.main.pack(side="left", fill="both", expand=True)

    def show_home(self):
        self.clear()
        self.sidebar()
        self.content()

        scroll = ctk.CTkScrollableFrame(self.main, fg_color=BG,
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=MUTED)
        scroll.pack(fill="both", expand=True, padx=40, pady=30)

        ctk.CTkLabel(scroll, text="CENTRE D'AIDE",
                     text_color=MUTED, font=(SANS, 7)).pack(anchor="w")

        ctk.CTkLabel(scroll, text="Comment pouvons-nous vous aider ?",
                     text_color=WHITE, font=(SERIF, 18)).pack(anchor="w", pady=(8, 4))

        ctk.CTkLabel(scroll,
                     text="Informations et guides de chaque module.",
                     text_color=GREY, font=(SERIF, 10, "italic")).pack(anchor="w", pady=(0, 20))

        search = ctk.CTkEntry(
            scroll,
            textvariable=self.search_value,
            placeholder_text="Rechercher…",
            height=32,
            fg_color="transparent",
            border_color=BORDER,
            text_color=WHITE,
            placeholder_text_color=MUTED,
            corner_radius=2,
            font=(SERIF, 10)
        )
        search.pack(fill="x", pady=(0, 20))
        search.bind("<KeyRelease>", self.filter_modules)

        self.grid_frame = ctk.CTkFrame(scroll, fg_color=BG)
        self.grid_frame.pack(fill="x")

        for col in range(2):
            self.grid_frame.grid_columnconfigure(col, weight=1)

        self.module_cards = []

        for index, module in enumerate(MODULES):
            self.create_card(self.grid_frame, module, index // 2, index % 2)

        ctk.CTkFrame(scroll, fg_color=BG, height=20).pack()

        footer = ctk.CTkFrame(scroll, fg_color="transparent")
        footer.pack(fill="x", pady=(4, 0))
        ctk.CTkFrame(footer, height=1, fg_color=BORDER).pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(footer, text="MAISON",
                     text_color=GREY, font=(SERIF, 9)).pack(anchor="w")
        ctk.CTkLabel(footer,
                     text="Centre d'information et d'assistance.",
                     text_color=MUTED, font=(SERIF, 8, "italic")).pack(anchor="w", pady=(2, 0))

    def create_card(self, parent, module, row, col):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=2,
            height=108
        )
        card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        card.grid_propagate(False)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 8))

        icon = Icon(top, module["icon"], 14, GREY)
        icon.pack(side="left")

        ctk.CTkLabel(top, text="MODULE", text_color=MUTED,
                     font=(SANS, 6)).pack(side="right")

        ctk.CTkLabel(card, text=module["name"], text_color=WHITE,
                     font=(SERIF, 12)).pack(anchor="w", padx=14)

        ctk.CTkLabel(card, text=module["description"], text_color=GREY,
                     font=(SERIF, 9, "italic"), wraplength=360,
                     justify="left").pack(anchor="w", padx=14, pady=(4, 8))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(fill="x", padx=14, pady=(0, 10))

        ctk.CTkLabel(bottom, text="GUIDE", text_color=MUTED,
                     font=(SANS, 6)).pack(side="left")

        arrow = Icon(bottom, "arrow", 11, MUTED)
        arrow.pack(side="right")

        for widget in (card, top, icon, bottom, arrow):
            widget.bind("<Button-1>", lambda e, m=module: self.show_module(m))

        self.module_cards.append((card, module))

    def filter_modules(self, event=None):
        query = self.search_value.get().lower().strip()
        for card, module in self.module_cards:
            visible = (query in module["name"].lower()
                       or query in module["description"].lower())
            if visible:
                card.grid()
            else:
                card.grid_remove()

    def show_module(self, module):
        self.clear()
        self.sidebar(module["name"])
        self.content()

        scroll = ctk.CTkScrollableFrame(self.main, fg_color=BG,
                                        scrollbar_button_color=BORDER,
                                        scrollbar_button_hover_color=MUTED)
        scroll.pack(fill="both", expand=True, padx=44, pady=30)

        self.button(scroll, "RETOUR", self.show_home, 90).pack(
            anchor="w", pady=(0, 22))

        icon_box = ctk.CTkFrame(scroll, fg_color=CARD, border_width=1,
                                border_color=BORDER, corner_radius=2,
                                width=44, height=44)
        icon_box.pack(anchor="w", pady=(0, 14))
        icon_box.pack_propagate(False)
        Icon(icon_box, module["icon"], 20, GREY).place(relx=.5, rely=.5, anchor="center")

        ctk.CTkLabel(scroll, text=module["name"].upper(), text_color=WHITE,
                     font=(SERIF, 16)).pack(anchor="w")

        ctk.CTkLabel(scroll, text=module["description"], text_color=GREY,
                     font=(SERIF, 10, "italic")).pack(anchor="w", pady=(4, 22))

        ctk.CTkLabel(scroll, text="GUIDE",
                     text_color=MUTED, font=(SANS, 7)).pack(anchor="w", pady=(0, 10))

        for index, detail in enumerate(module["details"], 1):
            row = ctk.CTkFrame(scroll, fg_color="transparent")
            row.pack(fill="x", pady=0)

            ctk.CTkLabel(row, text=f"{index:02d}", text_color=MUTED,
                         font=(SERIF, 9)).pack(side="left", padx=(0, 14), pady=8)

            ctk.CTkFrame(row, width=1, fg_color=BORDER).pack(side="left", fill="y", pady=3)

            ctk.CTkLabel(row, text=detail, text_color=GREY,
                         font=(SERIF, 9), wraplength=640,
                         justify="left").pack(side="left", padx=14, pady=8)

            ctk.CTkFrame(scroll, height=1, fg_color=BORDER).pack(fill="x")

        ctk.CTkFrame(scroll, fg_color=BG, height=20).pack()

    def open_module(self, module):
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), module["file"])
        if not os.path.isfile(path):
            tk.messagebox.showerror("Fichier introuvable",
                                    f"Le fichier {module['file']} est introuvable.")
            return
        try:
            subprocess.Popen([sys.executable, path])
        except OSError as error:
            tk.messagebox.showerror("Erreur", str(error))


if __name__ == "__main__":
    app = HelpApp()
    app.mainloop()