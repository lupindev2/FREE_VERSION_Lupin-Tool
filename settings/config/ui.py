import pygame

WHITE = (235, 235, 235)
GREY = (135, 135, 135)
DARKGREY = (70, 70, 70)
BLACK = (5, 5, 5)
PANEL = (18, 18, 18)
PANEL_LIGHT = (28, 28, 28)
BORDER = (45, 45, 45)
ACCENT = (180, 180, 180)
GREEN = (110, 200, 140)
RED = (210, 100, 95)
YELLOW = (220, 190, 100)
BLUE = (100, 160, 230)

FONT_TITLE = "Georgia"
FONT_BODY = "Georgia"
FONT_MONO = "Consolas"


def _font(name, size, bold=False):
    return pygame.font.SysFont(name, size, bold=bold)


class UI:
    def __init__(self):
        self.title = _font(FONT_TITLE, 32)
        self.subtitle = _font(FONT_TITLE, 16)
        self.body = _font(FONT_BODY, 17)
        self.small = _font(FONT_BODY, 14)
        self.tiny = _font(FONT_BODY, 12)
        self.mono = _font(FONT_MONO, 13)
        self.mono_small = _font(FONT_MONO, 11)

    def text(self, surf, value, x, y, color=WHITE, font=None):
        f = font or self.body
        r = f.render(str(value), True, color)
        surf.blit(r, (x, y))
        return r.get_rect(topleft=(x, y))

    def rounded_rect(self, surf, rect, color, radius=10, border=None, bw=1):
        pygame.draw.rect(surf, color, rect, border_radius=radius)
        if border:
            pygame.draw.rect(surf, border, rect, bw, border_radius=radius)

    def button(self, surf, rect, label, mouse, font=None, selected=False, danger=False):
        hover = rect.collidepoint(mouse)
        if danger:
            base = (60, 25, 25)
            hov = (90, 35, 35)
        else:
            base = PANEL_LIGHT
            hov = (48, 48, 48)
        color = hov if hover else base
        if selected:
            color = (55, 55, 55)
        self.rounded_rect(surf, rect, color, radius=10, border=BORDER)
        f = font or self.body
        r = f.render(label, True, WHITE)
        surf.blit(r, r.get_rect(center=rect.center))
        return rect

    def panel(self, surf, rect):
        self.rounded_rect(surf, rect, PANEL, radius=14, border=BORDER)

    def progress(self, surf, rect, value, color=ACCENT):
        self.rounded_rect(surf, rect, PANEL_LIGHT, radius=rect.height // 2)
        w = max(0, min(1, value)) * rect.width
        if w > 1:
            self.rounded_rect(
                surf,
                pygame.Rect(rect.x, rect.y, int(w), rect.height),
                color,
                radius=rect.height // 2,
            )


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t