import math
import pygame
from ui import lerp, smooth, ease_out

INK = (190, 190, 190)


def _bezier(p0, p1, p2, p3, t):
    u = 1 - t
    return (
        u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
        u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1],
    )


def _make_pen():
    pen = pygame.Surface((150, 34), pygame.SRCALPHA)
    pygame.draw.ellipse(pen, (0, 0, 0, 60), (12, 24, 120, 7))
    pygame.draw.rect(pen, (22, 22, 22), (16, 11, 108, 12), border_radius=6)
    pygame.draw.line(pen, (110, 110, 110), (26, 12), (112, 12), 1)
    pygame.draw.line(pen, (0, 0, 0), (26, 21), (116, 21), 1)
    for x in (26, 116, 122):
        pygame.draw.rect(pen, (170, 170, 170), (x, 10, 2, 14), border_radius=1)
    pygame.draw.polygon(pen, (150, 150, 150), [(126, 11), (146, 17), (126, 23)])
    pygame.draw.polygon(pen, (230, 230, 230), [(127, 12), (141, 17), (127, 16)])
    pygame.draw.line(pen, (70, 70, 70), (146, 17), (126, 23), 1)
    return pen


_PEN = None


def _get_pen():
    global _PEN
    if _PEN is None:
        _PEN = _make_pen()
    return _PEN


def _signature_points(rect):
    x, y, w, h = rect
    curves = [
        ((0.00, .62), (.10, .08), (.16, .08), (.22, .58)),
        ((.22, .58), (.30, .95), (.34, .12), (.42, .48)),
        ((.42, .48), (.50, .78), (.54, .14), (.62, .50)),
        ((.62, .50), (.70, .86), (.74, .18), (.80, .48)),
        ((.80, .48), (.88, .72), (.92, .12), (.98, .42)),
    ]
    pts = []
    for curve in curves:
        conv = [(x + p[0] * w, y + p[1] * h) for p in curve]
        for i in range(16):
            pts.append(_bezier(*conv, i / 16))
    pts.append((x + w, y + h * .42))
    return pts


class PenAnimation:
    """Petit stylo qui écrit une signature dans un rect donné."""

    DURATION = 2.2

    def __init__(self, rect):
        self.rect = pygame.Rect(rect)
        self.points = _signature_points(self.rect)
        self.t = 0.0
        self.active = False
        self.visible_points = []

    def set_rect(self, rect):
        rect = pygame.Rect(rect)
        if rect == self.rect:
            return
        self.rect = rect
        self.points = _signature_points(rect)
        self.t = 0.0
        self.visible_points = []

    def start(self):
        self.t = 0.0
        self.active = True
        self.visible_points = []

    def update(self, dt):
        if not self.active:
            return
        self.t += dt
        if self.t >= self.DURATION:
            self.active = False
        progress = smooth(self.t / self.DURATION)
        amount = progress * (len(self.points) - 1)
        count = int(amount)
        frac = amount - count
        vis = self.points[: count + 1]
        if count + 1 < len(self.points):
            a, b = self.points[count], self.points[count + 1]
            vis.append((lerp(a[0], b[0], frac), lerp(a[1], b[1], frac)))
        self.visible_points = vis

    def draw(self, surf):
        if not self.visible_points and not self.active:
            return
        vis = self.visible_points
        if len(vis) >= 2:
            pygame.draw.lines(surf, (90, 90, 90), False, vis, 2)
            pygame.draw.lines(surf, INK, False, vis, 1)
        if self.active and vis:
            tip = vis[-1]
            pen = _get_pen()
            angle = -30
            offset = pygame.Vector2(146 - 75, 17 - 17).rotate(angle)
            center = (tip[0] - offset.x, tip[1] - offset.y)
            surf.blit(pen, pen.get_rect(center=center))