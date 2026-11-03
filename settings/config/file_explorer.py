import os
from pathlib import Path
import pygame

from ui import (
    UI, WHITE, GREY, PANEL, PANEL_LIGHT, BORDER, BLACK,
    ACCENT, BLUE, DARKGREY, smooth, ease_out,
)


class FileExplorer:
    def __init__(self, ui, start_dir=None, mode="save", default_name="rapport.txt"):
        self.ui = ui
        self.mode = mode
        candidate_dir = Path(start_dir or Path.home())
        self.cwd = candidate_dir if candidate_dir.is_dir() else Path.home()
        self.entries = []
        self.scroll = 0
        self.selected = None
        self.filename = default_name
        self.active_field = "file"
        self.error_message = ""
        self.refresh()
        self.anim_t = 0.0

    def _valid_filename(self):
        invalid_chars = '<>:"/\\|?*'
        return (
            bool(self.filename.strip())
            and self.filename not in {".", ".."}
            and Path(self.filename).name == self.filename
            and not any(char in invalid_chars or ord(char) < 32 for char in self.filename)
        )

    def _confirm(self):
        if not self._valid_filename():
            self.error_message = "Nom de fichier invalide."
            return None
        self.error_message = ""
        return "confirm"

    def refresh(self):
        try:
            items = []
            for entry in sorted(self.cwd.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                if entry.name.startswith("."):
                    continue
                items.append(entry)
            self.entries = items
        except (PermissionError, OSError):
            self.entries = []
        self.scroll = 0
        self.selected = None

    def update(self, dt):
        self.anim_t += dt

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self.scroll - event.y * 3, max(0, len(self.entries) - 8)))
            return None

        if event.type == pygame.KEYDOWN:
            if self.active_field == "file":
                if event.key == pygame.K_BACKSPACE:
                    self.filename = self.filename[:-1]
                    self.error_message = ""
                elif event.key == pygame.K_RETURN:
                    return self._confirm()
                elif event.key == pygame.K_ESCAPE:
                    return "cancel"
                elif event.unicode and event.unicode.isprintable() and not any(
                    char in '<>:"/\\|?*' for char in event.unicode
                ):
                    self.filename += event.unicode
                    self.error_message = ""
                return None
            if event.key == pygame.K_ESCAPE:
                return "cancel"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            if hasattr(self, "up_rect") and self.up_rect.collidepoint(pos):
                if self.cwd.parent != self.cwd:
                    self.cwd = self.cwd.parent
                    self.refresh()
                return None
            if hasattr(self, "file_rect") and self.file_rect.collidepoint(pos):
                self.active_field = "file"
                return None
            if hasattr(self, "confirm_rect") and self.confirm_rect.collidepoint(pos):
                return self._confirm()
            if hasattr(self, "cancel_rect") and self.cancel_rect.collidepoint(pos):
                return "cancel"
            for rect, entry in getattr(self, "entry_rects", []):
                if rect.collidepoint(pos):
                    self.selected = entry
                    return None
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if self.selected is not None and self.selected.is_dir():
                self.cwd = self.selected
                self.refresh()
        return None

    def draw(self, surf):
        w, h = surf.get_size()
        surf.fill(BLACK)

        panel = pygame.Rect(60, 40, w - 120, h - 80)
        self.ui.panel(surf, panel)

        self.ui.text(surf, "SAUVEGARDER LE RAPPORT", panel.x + 25, panel.y + 18, WHITE, self.ui.subtitle)
        self.ui.text(surf, str(self.cwd), panel.x + 25, panel.y + 48, GREY, self.ui.mono_small)

        up_rect = pygame.Rect(panel.right - 240, panel.y + 16, 100, 32)
        self.up_rect = up_rect
        self.ui.button(surf, up_rect, "↑ DOSSIER", pygame.mouse.get_pos(), self.ui.small)

        list_rect = pygame.Rect(panel.x + 25, panel.y + 80, panel.width - 50, panel.height - 190)
        pygame.draw.rect(surf, PANEL_LIGHT, list_rect, border_radius=8)
        pygame.draw.rect(surf, BORDER, list_rect, 1, border_radius=8)

        self.entry_rects = []
        row_h = 30
        max_rows = list_rect.height // row_h
        visible = self.entries[self.scroll: self.scroll + max_rows]

        for i, entry in enumerate(visible):
            row = pygame.Rect(list_rect.x + 6, list_rect.y + 6 + i * row_h, list_rect.width - 12, row_h - 4)
            hover = row.collidepoint(pygame.mouse.get_pos())
            selected = self.selected == entry
            if selected:
                pygame.draw.rect(surf, (55, 55, 55), row, border_radius=6)
            elif hover:
                pygame.draw.rect(surf, (38, 38, 38), row, border_radius=6)
            icon = "▸" if entry.is_dir() else "·"
            color = BLUE if entry.is_dir() else WHITE
            self.ui.text(surf, icon, row.x + 8, row.y + 6, color, self.ui.body)
            self.ui.text(surf, entry.name, row.x + 30, row.y + 6, WHITE, self.ui.small)
            self.entry_rects.append((row, entry))

        if self.entries and self.selected is None:
            self.ui.text(
                surf, "clic = sélectionner · clic droit dossier = entrer",
                list_rect.x + 8, list_rect.bottom + 6, GREY, self.ui.tiny,
            )

        file_rect = pygame.Rect(panel.x + 25, panel.bottom - 90, panel.width - 50, 34)
        self.file_rect = file_rect
        if self.error_message:
            self.ui.text(surf, self.error_message, file_rect.x, file_rect.y - 18, (210, 100, 95), self.ui.tiny)
        pygame.draw.rect(surf, PANEL_LIGHT, file_rect, border_radius=8)
        pygame.draw.rect(surf, BORDER, file_rect, 1, border_radius=8)
        self.ui.text(surf, self.filename + ("|" if self.active_field == "file" else ""),
                     file_rect.x + 10, file_rect.y + 8, WHITE, self.ui.mono_small)

        confirm_rect = pygame.Rect(panel.right - 200, panel.bottom - 45, 160, 36)
        cancel_rect = pygame.Rect(panel.right - 380, panel.bottom - 45, 160, 36)
        self.confirm_rect = confirm_rect
        self.cancel_rect = cancel_rect
        self.ui.button(surf, confirm_rect, "ENREGISTRER", pygame.mouse.get_pos())
        self.ui.button(surf, cancel_rect, "ANNULER", pygame.mouse.get_pos(), danger=True)

    def result_path(self):
        if not self._valid_filename():
            raise ValueError("Nom de fichier invalide")
        target = self.selected if (self.selected and self.selected.is_dir()) else self.cwd
        return target / self.filename.strip()