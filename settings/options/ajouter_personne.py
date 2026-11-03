
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import shutil
import uuid
from PIL import Image

                                
               
                                

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "personnes.json")
PHOTO_DIR = os.path.join(BASE_DIR, "photos_personnes")

os.makedirs(PHOTO_DIR, exist_ok=True)

BG = "#000000"
CARD = "#101010"
CARD_HOVER = "#191919"
BORDER = "#292929"
WHITE = "#FFFFFF"
GREY = "#888888"


                                
         
                                

def load_people():
    if not os.path.exists(DATA_FILE):
        return []

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def save_people():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(people, f, indent=4, ensure_ascii=False)


people = load_people()


                                
             
                                

class PeopleApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("Mes personnes")
        self.geometry("1200x800")
        self.configure(fg_color=BG)

        self.attributes("-fullscreen", True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.bind("<F11>", self.toggle_fullscreen)

        self.current_photo = None
        self.current_fields = []

        self.show_home()

    def toggle_fullscreen(self, event=None):
        self.attributes(
            "-fullscreen",
            not self.attributes("-fullscreen")
        )

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def make_button(self, parent, text, command, width=180):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=45,
            corner_radius=12,
            fg_color="#171717",
            hover_color="#292929",
            text_color=WHITE,
            border_width=1,
            border_color=BORDER,
            font=("Arial", 14)
        )

                                
                     
                                

    def show_home(self):
        self.clear()

        main = ctk.CTkFrame(
            self,
            fg_color=BG
        )
        main.pack(fill="both", expand=True, padx=50, pady=35)

        title = ctk.CTkLabel(
            main,
            text="AJOUTER UNE PERSONNE",
            font=("Arial", 30, "bold"),
            text_color=WHITE
        )
        title.pack(pady=(45, 10))

        subtitle = ctk.CTkLabel(
            main,
            text="Gérez vos dossiers et vos fiches personnalisées",
            font=("Arial", 14),
            text_color=GREY
        )
        subtitle.pack(pady=(0, 55))

        folder = ctk.CTkButton(
            main,
            text="📁",
            font=("Arial", 90),
            width=240,
            height=220,
            corner_radius=25,
            fg_color=CARD,
            hover_color=CARD_HOVER,
            border_width=1,
            border_color=BORDER,
            command=self.show_folders
        )
        folder.pack()

        label = ctk.CTkLabel(
            main,
            text="MES DOSSIERS",
            font=("Arial", 17, "bold"),
            text_color=WHITE
        )
        label.pack(pady=20)

        self.make_button(
            main,
            "OUVRIR MES DOSSIERS",
            self.show_folders,
            260
        ).pack(pady=15)

        bottom = ctk.CTkLabel(
            main,
            text=f"{len(people)} personne(s) enregistrée(s)",
            text_color=GREY,
            font=("Arial", 12)
        )
        bottom.pack(side="bottom", pady=15)

                                
              
                                

    def show_folders(self):
        self.clear()

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=45, pady=30)

        self.make_button(
            header,
            "← RETOUR",
            self.show_home,
            130
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="MES DOSSIERS",
            font=("Arial", 28, "bold"),
            text_color=WHITE
        ).pack(side="left", padx=35)

        ctk.CTkLabel(
            header,
            text=f"{len(people)} fiche(s)",
            text_color=GREY
        ).pack(side="right")

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            scrollbar_button_color="#333333"
        )
        scroll.pack(fill="both", expand=True, padx=45, pady=10)

        columns = 4

        for col in range(columns):
            scroll.grid_columnconfigure(col, weight=1)

        for index, person in enumerate(people):
            self.create_person_card(
                scroll,
                person,
                index,
                index // columns,
                index % columns
            )

        add_index = len(people)

        add_card = ctk.CTkButton(
            scroll,
            text="+\n\nCRÉER UNE NOUVELLE FICHE",
            font=("Arial", 22, "bold"),
            text_color=WHITE,
            fg_color="#080808",
            hover_color="#202020",
            border_width=2,
            border_color=BORDER,
            corner_radius=18,
            height=230,
            command=self.show_create
        )
        add_card.grid(
            row=add_index // columns,
            column=add_index % columns,
            padx=12,
            pady=12,
            sticky="nsew"
        )

                                
                    
                                

    def create_person_card(
        self, parent, person, index, row, column
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color=CARD,
            border_width=1,
            border_color=BORDER,
            corner_radius=18,
            height=230
        )
        card.grid(
            row=row,
            column=column,
            padx=12,
            pady=12,
            sticky="nsew"
        )
        card.grid_propagate(False)

        photo_path = person.get("photo")

        if photo_path and os.path.exists(photo_path):
            try:
                image = Image.open(photo_path)
                image.thumbnail((90, 90))

                photo = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(90, 90)
                )

                img_label = ctk.CTkLabel(
                    card,
                    text="",
                    image=photo
                )
                img_label.image = photo
                img_label.pack(pady=(15, 5))

            except Exception:
                ctk.CTkLabel(
                    card,
                    text="👤",
                    font=("Arial", 55)
                ).pack(pady=12)
        else:
            ctk.CTkLabel(
                card,
                text="👤",
                font=("Arial", 55),
                text_color=WHITE
            ).pack(pady=12)

        name = (
            f"{person.get('prenom', '')} "
            f"{person.get('nom', '')}"
        ).strip()

        if not name:
            name = person.get("titre", "Sans nom")

        ctk.CTkLabel(
            card,
            text=name,
            font=("Arial", 16, "bold"),
            text_color=WHITE
        ).pack(pady=5)

        ctk.CTkLabel(
            card,
            text=person.get("titre", ""),
            text_color=GREY,
            font=("Arial", 11)
        ).pack()

        self.make_button(
            card,
            "OUVRIR LA FICHE",
            lambda i=index: self.show_detail(i),
            180
        ).pack(pady=10)

                                
                    
                                

    def show_create(self):
        self.clear()

        self.current_photo = None
        self.current_fields = []

        header = ctk.CTkFrame(self, fg_color=BG)
        header.pack(fill="x", padx=45, pady=25)

        self.make_button(
            header,
            "← RETOUR",
            self.show_folders,
            130
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="NOUVELLE FICHE",
            font=("Arial", 26, "bold"),
            text_color=WHITE
        ).pack(side="left", padx=30)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG
        )
        scroll.pack(fill="both", expand=True, padx=100, pady=10)

        self.title_entry = self.create_input(
            scroll,
            "Nom de la carte",
            "Exemple : Dossier personnel"
        )

        self.first_entry = self.create_input(
            scroll,
            "Prénom (facultatif)",
            "Prénom"
        )

        self.last_entry = self.create_input(
            scroll,
            "Nom (facultatif)",
            "Nom"
        )

               

        ctk.CTkLabel(
            scroll,
            text="PHOTO",
            font=("Arial", 18, "bold"),
            text_color=WHITE
        ).pack(anchor="w", pady=(30, 10))

        self.photo_label = ctk.CTkLabel(
            scroll,
            text="Aucune photo sélectionnée",
            text_color=GREY
        )
        self.photo_label.pack(anchor="w", pady=8)

        self.make_button(
            scroll,
            "＋ IMPORTER UNE PHOTO",
            self.import_photo,
            240
        ).pack(anchor="w", pady=5)

                              

        ctk.CTkLabel(
            scroll,
            text="INFORMATIONS PERSONNALISÉES",
            font=("Arial", 19, "bold"),
            text_color=WHITE
        ).pack(anchor="w", pady=(35, 15))

        self.fields_container = ctk.CTkFrame(
            scroll,
            fg_color=BG
        )
        self.fields_container.pack(fill="x")

        self.field_name_entry = self.create_input(
            scroll,
            "Nom de la catégorie",
            "Exemple : Adresse"
        )

        self.field_value_entry = self.create_input(
            scroll,
            "Information",
            "Exemple : 12 Grande Rue"
        )

        self.make_button(
            scroll,
            "+ AJOUTER CETTE INFORMATION",
            self.add_field,
            280
        ).pack(anchor="w", pady=15)

        self.fields_display = ctk.CTkFrame(
            scroll,
            fg_color=BG
        )
        self.fields_display.pack(fill="x")

        ctk.CTkFrame(
            scroll,
            fg_color=BG,
            height=20
        ).pack()

        ctk.CTkButton(
            scroll,
            text="ENREGISTRER LA FICHE",
            height=55,
            corner_radius=14,
            fg_color="#FFFFFF",
            hover_color="#CCCCCC",
            text_color="#000000",
            font=("Arial", 16, "bold"),
            command=self.save_person
        ).pack(fill="x", pady=25)

    def create_input(self, parent, label, placeholder):
        ctk.CTkLabel(
            parent,
            text=label,
            text_color=WHITE,
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=(17, 7))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=45,
            fg_color=CARD,
            border_color=BORDER,
            text_color=WHITE,
            corner_radius=10
        )
        entry.pack(fill="x")

        return entry

                                
                  
                                

    def import_photo(self):
        path = filedialog.askopenfilename(
            title="Choisir une photo",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.webp")
            ]
        )

        if not path:
            return

        extension = os.path.splitext(path)[1].lower()

        filename = f"{uuid.uuid4().hex}{extension}"
        destination = os.path.join(
            PHOTO_DIR,
            filename
        )

        shutil.copy2(path, destination)

        self.current_photo = destination

        self.photo_label.configure(
            text="Photo sélectionnée : " + os.path.basename(path),
            text_color=WHITE
        )

                                
                  
                                

    def add_field(self):
        name = self.field_name_entry.get().strip()
        value = self.field_value_entry.get().strip()

        if not name or not value:
            messagebox.showwarning(
                "Information manquante",
                "Remplis le nom de la catégorie et son contenu."
            )
            return

        self.current_fields.append({
            "categorie": name,
            "valeur": value
        })

        self.field_name_entry.delete(0, "end")
        self.field_value_entry.delete(0, "end")

        self.refresh_fields()

    def refresh_fields(self):
        for widget in self.fields_display.winfo_children():
            widget.destroy()

        for index, field in enumerate(self.current_fields):

            line = ctk.CTkFrame(
                self.fields_display,
                fg_color=CARD,
                corner_radius=10
            )
            line.pack(fill="x", pady=5)

            ctk.CTkLabel(
                line,
                text=f"{field['categorie']} : {field['valeur']}",
                text_color=WHITE,
                font=("Arial", 13),
                wraplength=650
            ).pack(side="left", padx=15, pady=12)

            ctk.CTkButton(
                line,
                text="✕",
                width=35,
                fg_color="#292929",
                hover_color="#444444",
                command=lambda i=index: self.remove_field(i)
            ).pack(side="right", padx=10)

    def remove_field(self, index):
        self.current_fields.pop(index)
        self.refresh_fields()

                                
                    
                                

    def save_person(self):
        titre = self.title_entry.get().strip()

        if not titre:
            messagebox.showwarning(
                "Nom manquant",
                "Donne un nom à ta carte."
            )
            return

        person = {
            "id": str(uuid.uuid4()),
            "titre": titre,
            "prenom": self.first_entry.get().strip(),
            "nom": self.last_entry.get().strip(),
            "photo": self.current_photo,
            "champs": self.current_fields.copy()
        }

        people.append(person)
        save_people()

        messagebox.showinfo(
            "Enregistré",
            "La fiche a été créée."
        )

        self.show_folders()

                                
             
                                

    def show_detail(self, index):
        self.clear()

        person = people[index]

        header = ctk.CTkFrame(
            self,
            fg_color=BG
        )
        header.pack(fill="x", padx=45, pady=25)

        self.make_button(
            header,
            "← DOSSIERS",
            self.show_folders,
            150
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="DÉTAILS DE LA FICHE",
            font=("Arial", 25, "bold"),
            text_color=WHITE
        ).pack(side="left", padx=30)

        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG
        )
        scroll.pack(fill="both", expand=True, padx=100, pady=15)

        photo_path = person.get("photo")

        if photo_path and os.path.exists(photo_path):
            try:
                image = Image.open(photo_path)
                image.thumbnail((180, 180))

                photo = ctk.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(180, 180)
                )

                image_label = ctk.CTkLabel(
                    scroll,
                    text="",
                    image=photo
                )
                image_label.image = photo
                image_label.pack(pady=20)

            except Exception:
                pass

        else:
            ctk.CTkLabel(
                scroll,
                text="👤",
                font=("Arial", 80),
                text_color=WHITE
            ).pack(pady=20)

        name = (
            f"{person.get('prenom', '')} "
            f"{person.get('nom', '')}"
        ).strip()

        if not name:
            name = person.get("titre", "")

        ctk.CTkLabel(
            scroll,
            text=name,
            font=("Arial", 30, "bold"),
            text_color=WHITE
        ).pack(pady=10)

        ctk.CTkLabel(
            scroll,
            text=person.get("titre", ""),
            font=("Arial", 14),
            text_color=GREY
        ).pack(pady=(0, 30))

        for field in person.get("champs", []):
            box = ctk.CTkFrame(
                scroll,
                fg_color=CARD,
                corner_radius=12,
                border_width=1,
                border_color=BORDER
            )
            box.pack(fill="x", pady=8)

            ctk.CTkLabel(
                box,
                text=field["categorie"],
                font=("Arial", 14, "bold"),
                text_color=GREY
            ).pack(anchor="w", padx=20, pady=(15, 5))

            ctk.CTkLabel(
                box,
                text=field["valeur"],
                font=("Arial", 17),
                text_color=WHITE,
                wraplength=750,
                justify="left"
            ).pack(anchor="w", padx=20, pady=(0, 15))

                     

        ctk.CTkButton(
            scroll,
            text="SUPPRIMER CETTE FICHE",
            fg_color="#242424",
            hover_color="#444444",
            text_color="#FFFFFF",
            height=45,
            command=lambda: self.delete_person(index)
        ).pack(pady=35)


                                
                 
                                

    def delete_person(self, index):
        confirm = messagebox.askyesno(
            "Confirmation",
            "Supprimer définitivement cette fiche ?"
        )

        if not confirm:
            return

        person = people[index]

        photo = person.get("photo")

        if photo and os.path.exists(photo):
            try:
                os.remove(photo)
            except OSError:
                pass

        people.pop(index)
        save_people()

        self.show_folders()

if __name__ == "__main__":
    app = PeopleApp()
    app.mainloop()
