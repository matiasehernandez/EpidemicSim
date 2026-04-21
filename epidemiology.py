import pygame
import random
import math
import sys
from enum import Enum
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

#--------------------------------------------
#  ENUM
#--------------------------------------------

class Estado(Enum):
    SUSCEPTIBLE = 1
    INFECTADO = 2
    RECUPERADO = 3

PANEL_W = 340 # Ancho del panel derecho 
CHART_H = 120 # Altura de cada gráfico de ciudad en línea
SIM_COLS = 2 # Son las dos columnas de la ciudad
HUD_H = 28 # Barra superior del HUD

# Columnas de simulación: cada ciudad recibe la mitad del área izquierda
LEFT_W = 760 # Ancho total del área izquierda
CITY_W = LEFT_W // 2 # 380 píxeles por columna de ciudad
CITY_H = 400 # Altura del área de simulación por ciudad
ROAD_W = 60 # Franja de carretera entre las dos columnas de simulación (ciudades)

WIDTH = LEFT_W + PANEL_W
HEIGHT = HUD_H + CITY_H + CHART_H 

#--------------------------------------------
#  Paleta de colores
#--------------------------------------------

PAL = {
    "bg": (10, 10, 18),
    "panel_bg": (18, 20, 35),
    "panel_border": (60, 65, 100),
    "city_border": (80, 80, 130),
    "city_fill": (20, 22, 40),
    "road_fill": (30, 30, 50),
    "susceptible": (80, 200, 80),
    "infected": (230, 60, 60),
    "recovered": (60, 130, 230),
    "aura": (255,220, 50),
    "white": (220, 220, 240),
    "gray": (120, 120, 160),
    "accent": (255,200, 50),
    "btn_normal": (50, 60, 100),
    "btn_hover": (80, 95, 160),
    "btn_press": (120, 150, 220),
    "slider_bg": (40,  45, 70),
    "slider_fill": (80, 130, 220),
    "slider_knob": (200, 210, 255),
    "chart_bg": (12, 14, 26),
    "grid": (28, 32, 52),
    "sep": (45, 50, 80),
}

##--------------------------------------------
#  Funciones auxiliares
#--------------------------------------------

def px_rect(surf, color, rect, bw=0):
    pygame.draw.rect(surf, color, rect, bw)

def px_text(surf, font, txt, color, pos, align="left"):
    s = font.render(txt, False, color)
    r = s.get_rect()
    if   align == "center": r.midtop = pos
    elif align == "right": r.topright = pos
    else: r.topleft  = pos
    surf.blit(s, r)
    return r

def draw_sep(surf, y, x0, x1, label=None, font=None):
    pygame.draw.line(surf, PAL["sep"], (x0, y), (x1, y))
    if label and font:
        px_text(surf, font, label, PAL["gray"], ((x0+x1)//2, y+2), align="center")

#--------------------------------------------
#  Ciudad e individuos
#--------------------------------------------

class Ciudad:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.individuos = []

class Individuo:
    def __init__(self, x, y, ciudad):
        self.x = float(x)
        self.y = float(y)
        self.estado = Estado.SUSCEPTIBLE
        self.dx = random.uniform(-1, 1)
        self.dy = random.uniform(-1, 1)
        self.tiempo_infeccion = 0
        self.tiempo_recuperacion = 0
        self.ciudad_actual = ciudad
        self.t_ultimo_cambio = 0

    def mover(self, ciudades, camino, t, speed, c_radius, dist_lvl):
        if dist_lvl > 0 and self.estado == Estado.SUSCEPTIBLE:
            threshold = c_radius * 2.0 * dist_lvl
            for ciudad in ciudades:
                for otro in ciudad.individuos:
                    if otro is self:
                        continue
                    ddx = otro.x - self.x
                    ddy = otro.y - self.y
                    dist = math.hypot(ddx, ddy)
                    if 0 < dist < threshold:
                        self.dx -= ddx * dist_lvl * 0.15
                        self.dy -= ddy * dist_lvl * 0.15

        mag = math.hypot(self.dx, self.dy)
        if mag > 0:
            self.dx = (self.dx / mag) * speed
            self.dy = (self.dy / mag) * speed

        nx, ny = self.x + self.dx, self.y + self.dy

        MIN_CHANGE = 2000
        PROB_CHANGE = 0.0001
        if (t - self.t_ultimo_cambio > MIN_CHANGE and random.random() < PROB_CHANGE):
            if camino.collidepoint(self.x, self.y):
                for ciudad in ciudades:
                    if abs(self.x - ciudad.rect.centerx) < 100:
                        nx, ny = float(ciudad.rect.centerx), float(ciudad.rect.centery)
                        self.ciudad_actual = ciudad
                        self.t_ultimo_cambio = t
                        break
            elif random.random() < PROB_CHANGE:
                nx = float(self.ciudad_actual.rect.centerx)
                ny = float(camino.centery)
                self.t_ultimo_cambio = t

        if self.ciudad_actual.rect.collidepoint(nx, ny) or camino.collidepoint(nx, ny):
            self.x, self.y = nx, ny
        else:
            self.dx *= -1
            self.dy *= -1

#--------------------------------------------
#  SLIDER: se puede reposicionar después de su creación mediante reposition()
#--------------------------------------------

class Slider:
    LABEL_H = 16 # height of the label row
    TRACK_H = 16 # height of the track row
    TOTAL_H = LABEL_H + TRACK_H # = 32 px por slider

    def __init__(self, x, y, w, mn, mx, val, label, fmt, color=None):
        self._x = x
        self._w = w
        self.label_y = y
        self.rect = pygame.Rect(x, y + self.LABEL_H, w, self.TRACK_H)
        self.min, self.max = float(mn), float(mx)
        self.value = float(val)
        self.label = label
        self.fmt = fmt
        self.color = color or PAL["slider_fill"]
        self.dragging = False

    def reposition(self, y):
        """Mueva el control deslizante a una nueva coordenada y (utilizada para el espaciado uniforme)"""
        self.label_y = y
        self.rect.top = y + self.LABEL_H

    @property
    def bottom(self):
        return self.rect.bottom

    def _kx(self):
        frac = (self.value - self.min) / (self.max - self.min)
        return int(self.rect.x + frac * self.rect.w)

    def draw(self, surf, font):
        px_text(surf, font, self.label, PAL["white"], (self.rect.x, self.label_y))
        px_text(surf, font, self.fmt.format(self.value), PAL["accent"],
                (self.rect.right, self.label_y), align="right")
        track = pygame.Rect(self.rect.x, self.rect.centery - 2, self.rect.w, 5)
        px_rect(surf, PAL["slider_bg"], track)
        kx = self._kx()
        px_rect(surf, self.color,
                pygame.Rect(self.rect.x, self.rect.centery - 2, kx - self.rect.x, 5))
        ky = self.rect.centery
        px_rect(surf, PAL["slider_knob"],  pygame.Rect(kx-4, ky-7, 8, 14))
        px_rect(surf, PAL["panel_border"], pygame.Rect(kx-4, ky-7, 8, 14), 1)

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if abs(event.pos[0]-self._kx()) < 10 and abs(event.pos[1]-self.rect.centery) < 12:
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            frac = (event.pos[0] - self.rect.x) / self.rect.w
            self.value = self.min + max(0.0, min(1.0, frac)) * (self.max - self.min)

#-------------------------------------------
# Botón
#-------------------------------------------

class Button:
    def __init__(self, x, y, w, h, label):
        self.rect = pygame.Rect(x, y, w, h)
        self.label = label
        self.pressed = False

    @property
    def bottom(self):
        return self.rect.bottom

    def draw(self, surf, font):
        hover = self.rect.collidepoint(pygame.mouse.get_pos())
        col = PAL["btn_press"] if self.pressed else (PAL["btn_hover"] if hover else PAL["btn_normal"])
        px_rect(surf, col, self.rect)
        px_rect(surf, PAL["panel_border"], self.rect, 2)
        px_text(surf, font, self.label,  PAL["white"], self.rect.center, align="center")

    def handle(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos): self.pressed = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            fired = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            return fired
        return False

#-------------------------------------------
#  Gráfico en tiempo real de las dinámicas (abajo de las ciudades)
#-------------------------------------------

class MiniChart:
    def __init__(self, rect, title):
        self.rect = pygame.Rect(rect)
        self.title = title
        self.surf = pygame.Surface((self.rect.w, self.rect.h))

    def draw(self, dst, font, t_list, s_list, i_list, r_list):
        s = self.surf
        s.fill(PAL["chart_bg"])
        pygame.draw.rect(s, PAL["panel_border"], s.get_rect(), 1)
        px_text(s, font, self.title, PAL["accent"], (4, 3))
        n = len(t_list)
        if n >= 2:
            cw = self.rect.w - 8
            ch = self.rect.h - 22
            cx, cy = 4, 18
            total = max(s_list[0] + i_list[0] + r_list[0], 1)
            for row in (1, 2, 3):
                gy = cy + ch * row // 4
                pygame.draw.line(s, PAL["grid"], (cx, gy), (cx+cw, gy))
            def series(data, color):
                pts = [(cx + int(cw*k/(n-1)), cy + ch - int(ch*data[k]/total))
                       for k in range(n)]
                if len(pts) >= 2:
                    pygame.draw.lines(s, color, False, pts, 2)
            series(s_list, PAL["susceptible"])
            series(i_list, PAL["infected"])
            series(r_list, PAL["recovered"])
        dst.blit(s, self.rect.topleft)

#-------------------------------------------
#  Guardar figuras en PNG
#-------------------------------------------

def guardar_graficas(t_list, sA, iA, rA, sB, iB, rB):
    ts = np.array(t_list) / 1000.0
    plt.rcParams.update({
        "figure.facecolor":"#0A0A12","axes.facecolor":"#0E1028",
        "axes.edgecolor":"#3C4164","axes.labelcolor":"#DCDCF0",
        "text.color":"#DCDCF0","xtick.color":"#787890","ytick.color":"#787890",
        "grid.color":"#1E2337","grid.linestyle":"--",
    })
    for title, s_d, i_d, r_d, fname in [
        ("Ciudad A – Curvas SIRS", sA, iA, rA, "ciudad_A_sirs.png"),
        ("Ciudad B – Curvas SIRS", sB, iB, rB, "ciudad_B_sirs.png"),
    ]:
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(ts, s_d, color="#50C850", lw=2, label="Susceptibles")
        ax.plot(ts, i_d, color="#E63C3C", lw=2, label="Infectados")
        ax.plot(ts, r_d, color="#3C82E6", lw=2, label="Recuperados")
        ax.set_title(title, fontsize=14, pad=10)
        ax.set_xlabel("Tiempo (s)")
        ax.set_ylabel("Individuos")
        ax.grid(True)
        ax.legend()
        fig.tight_layout()
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"Gráfica guardada: {fname}")

#-------------------------------------------
#  MAIN
#-------------------------------------------

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Modelo Epidemiológico SIRS  •  Pixel Edition")

    try:
        fn_lg = pygame.font.SysFont("couriernew", 15, bold=True)
        fn_md = pygame.font.SysFont("couriernew", 13, bold=True)
        fn_sm = pygame.font.SysFont("couriernew", 11)
        fn_xs = pygame.font.SysFont("couriernew",  9)
    except Exception:
        fn_lg = pygame.font.SysFont(None, 15)
        fn_md = pygame.font.SysFont(None, 13)
        fn_sm = pygame.font.SysFont(None, 11)
        fn_xs = pygame.font.SysFont(None,  9)

    COL_A_X = 0
    COL_B_X = CITY_W
    SIM_Y = HUD_H
    SIM_H = CITY_H   # alias

    # Rectángulos de la ciudad: deje un pequeño margen para que el borde sea visible
    M = 4   # margin
    ciudad_a = Ciudad(COL_A_X + M, SIM_Y + M,
                      CITY_W  - M - 30, SIM_H - M*2)
    ciudad_b = Ciudad(COL_B_X + 30, SIM_Y + M,
                      CITY_W  - M - 30, SIM_H - M*2)
    ciudades = [ciudad_a, ciudad_b]

    # Carretera: una franja horizontal que conecta las dos ciudades 
    road_x = ciudad_a.rect.right
    road_w = ciudad_b.rect.left - road_x
    road_y = SIM_Y + SIM_H // 2 - 30
    camino = pygame.Rect(road_x, road_y, road_w, 60)

    # Gráficos: uno debajo de cada columna de ciudad, a ancho completo de la columna
    CHART_PAD = 2
    chart_rect_a = pygame.Rect(COL_A_X + CHART_PAD,
                               HUD_H + SIM_H + CHART_PAD,
                               CITY_W - CHART_PAD*2,
                               CHART_H - CHART_PAD*2)
    chart_rect_b = pygame.Rect(COL_B_X + CHART_PAD,
                               HUD_H + SIM_H + CHART_PAD,
                               CITY_W - CHART_PAD*2,
                               CHART_H - CHART_PAD*2)
    chart_a = MiniChart(chart_rect_a, "Ciudad A")
    chart_b = MiniChart(chart_rect_b, "Ciudad B")

    PX = LEFT_W + 10 # Panel derecho
    PW = PANEL_W - 20 # Ancho del contenido del panel

    PANEL_TOP      = 36
    BTN_ZONE_H = 58 + 20   # dos botones + gap + hint
    SLIDERS_AVAIL = HEIGHT - PANEL_TOP - BTN_ZONE_H

    N_SLIDERS = 10
    pitch = SLIDERS_AVAIL / N_SLIDERS

    def make_sl(idx, mn, mx, val, label, fmt, color=None):
        y = int(PANEL_TOP + idx * pitch)
        return Slider(PX, y, PW, mn, mx, val, label, fmt, color)

    sl_dist = make_sl(0, 0.0, 1.0, 0.0, "Distanciamiento", "{:.0%}")
    sl_vacc = make_sl(1, 0.0, 1.0, 0.5, "% Vacunacion", "{:.0%}",  color=(80, 200, 130))
    sl_n = make_sl(2, 5, 100, 50, "Indiv./ciudad", "{:.0f}",  color=(160, 160, 220))
    sl_speed = make_sl(3, 0.5, 5.0, 2.0, "Velocidad", "{:.1f}",  color=(160, 200, 220))
    sl_prad = make_sl(4, 2, 10, 4, "Radio individuo", "{:.0f}",  color=(160, 200, 220))
    sl_crad = make_sl(5, 5, 50, 18, "Radio contagio", "{:.0f}",  color=(230, 160, 80))
    sl_prob = make_sl(6, 0.0, 1.0, 0.3,  "Prob. contagio", "{:.0%}",  color=(230, 100, 100))
    sl_recov = make_sl(7, 1000, 15000, 5000, "T.recuperac.(ms)", "{:.0f}",  color=(100, 200, 160))
    sl_reinf = make_sl(8, 500, 10000, 3000, "T.reinfec.(ms)", "{:.0f}",  color=(100, 160, 200))
    sl_dur = make_sl(9, 10000, 180000, 60000, "Duracion sim.(ms)", "{:.0f}", color=(180, 180, 100))

    all_sliders = [sl_dist, sl_vacc, sl_n, sl_speed, sl_prad,
                   sl_crad, sl_prob, sl_recov, sl_reinf, sl_dur]

    # Los botones debajo de los controles deslizantes
    btn_y = HEIGHT - BTN_ZONE_H + 4
    btn_vacc = Button(PX, btn_y, PW, 24, "VACUNAR AHORA")
    btn_restart = Button(PX, btn_y + 30, PW, 24, "REINICIAR")

    #----- Posiciones de los separadores (para divisores etiquetados) ----------
    sep_model_y = int(PANEL_TOP + 2 * pitch) - 6
    sep_btn_y   = btn_y - 8

    #----- Funciones auxiliares para generar entidades ----------
    def spawn(n):
        for ciudad in ciudades:
            ciudad.individuos.clear()
            for _ in range(n):
                x = random.randint(ciudad.rect.left+6, ciudad.rect.right -6)
                y = random.randint(ciudad.rect.top +6, ciudad.rect.bottom-6)
                ciudad.individuos.append(Individuo(x, y, ciudad))
        for _ in range(5):
            ind = random.choice(ciudad_a.individuos)
            ind.estado = Estado.INFECTADO

    spawn(int(round(sl_n.value)))

    #----- Datos ----------------------
    t_list = []
    sA, iA, rA = [], [], []
    sB, iB, rB = [], [], []

    #----- Tiempo ----------------
    paused = False
    t_inicio = pygame.time.get_ticks()
    t_paused_acc = 0
    t_pause_start = 0
    t_frozen = 0

    def snapshot(t_el):
        def cnt(c):
            s = sum(1 for p in c.individuos if p.estado == Estado.SUSCEPTIBLE)
            i = sum(1 for p in c.individuos if p.estado == Estado.INFECTADO)
            r = sum(1 for p in c.individuos if p.estado == Estado.RECUPERADO)
            return s, i, r
        sa, ia, ra = cnt(ciudad_a)
        sb, ib, rb = cnt(ciudad_b)
        t_list.append(t_el)
        sA.append(sa); iA.append(ia); rA.append(ra)
        sB.append(sb); iB.append(ib); rB.append(rb)

    def restart():
        nonlocal t_inicio, t_paused_acc, t_frozen, paused
        spawn(int(round(sl_n.value)))
        t_list.clear()
        for lst in (sA, iA, rA, sB, iB, rB): lst.clear()
        t_inicio = pygame.time.get_ticks()
        t_paused_acc = 0
        t_frozen = 0
        paused = False

    clock = pygame.time.Clock()
    running = True

    #---------------------------------------------------
    #  Bucle principal
    #---------------------------------------------------
    while running:
        t_now = pygame.time.get_ticks()

        if paused:
            t_elapsed = t_frozen
        else:
            t_elapsed = (t_now - t_inicio) - t_paused_acc
            t_frozen = t_elapsed

        sim_dur = int(sl_dur.value)
        t_remain = max(0, sim_dur - t_elapsed)

        #------ Eventos ------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if   event.key == pygame.K_ESCAPE: running = False
                elif event.key == pygame.K_p:
                    paused = not paused
                    if paused:
                        t_pause_start = t_now
                    else:
                        t_paused_acc += t_now - t_pause_start

            for sl in all_sliders:
                sl.handle(event)

            if btn_vacc.handle(event):
                pct = sl_vacc.value
                for ciudad in ciudades:
                    pool = [p for p in ciudad.individuos if p.estado == Estado.SUSCEPTIBLE]
                    k    = int(len(pool) * pct)
                    for p in random.sample(pool, min(k, len(pool))):
                        p.estado              = Estado.RECUPERADO
                        p.tiempo_recuperacion = t_elapsed

            if btn_restart.handle(event):
                restart()

        #------ Parámetros para modificar en tiempo real -------------
        speed    = sl_speed.value
        c_radius = max(1, int(round(sl_crad.value)))
        p_radius = max(1, int(round(sl_prad.value)))
        prob_c   = sl_prob.value
        t_recov  = int(sl_recov.value)
        t_reinf  = int(sl_reinf.value)
        dist_lvl = sl_dist.value

        #------- Etapas de la simulación ----------------
        if not paused and t_elapsed < sim_dur:
            for ciudad in ciudades:
                for ind in ciudad.individuos:
                    ind.mover(ciudades, camino, t_elapsed, speed, c_radius, dist_lvl)

                    if ind.estado == Estado.INFECTADO:
                        if t_elapsed - ind.tiempo_infeccion > t_recov:
                            ind.estado              = Estado.RECUPERADO
                            ind.tiempo_recuperacion = t_elapsed
                        else:
                            for otra in ciudades:
                                for otro in otra.individuos:
                                    if otro.estado == Estado.SUSCEPTIBLE:
                                        if math.hypot(otro.x-ind.x, otro.y-ind.y) < c_radius:
                                            if random.random() < prob_c:
                                                otro.estado           = Estado.INFECTADO
                                                otro.tiempo_infeccion = t_elapsed

                    elif ind.estado == Estado.RECUPERADO:
                        if t_elapsed - ind.tiempo_recuperacion > t_reinf:
                            ind.estado = Estado.SUSCEPTIBLE

            snapshot(t_elapsed)

        if not paused and t_elapsed >= sim_dur:
            running = False

        #-----------------------------------
        #  Dibujo de objetos
        #-----------------------------------
        screen.fill(PAL["bg"])

        #----- Ciudades ---------------------------
        for ciudad in ciudades:
            px_rect(screen, PAL["city_fill"], ciudad.rect.inflate(-4,-4))
            px_rect(screen, PAL["city_border"], ciudad.rect, 2)
            for gx in range(ciudad.rect.left+16, ciudad.rect.right, 16):
                pygame.draw.line(screen, PAL["grid"],
                                 (gx, ciudad.rect.top), (gx, ciudad.rect.bottom))
            for gy in range(ciudad.rect.top+16, ciudad.rect.bottom, 16):
                pygame.draw.line(screen, PAL["grid"],
                                 (ciudad.rect.left, gy), (ciudad.rect.right, gy))

        px_text(screen, fn_md, "CIUDAD A", PAL["accent"],
                (ciudad_a.rect.centerx, ciudad_a.rect.top+5), align="center")
        px_text(screen, fn_md, "CIUDAD B", PAL["accent"],
                (ciudad_b.rect.centerx, ciudad_b.rect.top+5), align="center")

        #------ Calle -------------------------------
        px_rect(screen, PAL["road_fill"], camino)
        for dx in range(camino.left+4, camino.right-4, 8):
            pygame.draw.rect(screen, PAL["gray"],
                             pygame.Rect(dx, camino.centery-1, 4, 2))

        #----- Individuos -------------------------
        for ciudad in ciudades:
            for ind in ciudad.individuos:
                ix, iy = int(ind.x), int(ind.y)
                if ind.estado == Estado.INFECTADO:
                    aura = pygame.Surface((c_radius*2, c_radius*2), pygame.SRCALPHA)
                    pygame.draw.circle(aura, (*PAL["aura"], 35),
                                       (c_radius, c_radius), c_radius)
                    screen.blit(aura, (ix-c_radius, iy-c_radius))
                    color = PAL["infected"]
                elif ind.estado == Estado.RECUPERADO:
                    color = PAL["recovered"]
                else:
                    color = PAL["susceptible"]
                pygame.draw.rect(screen, color,
                                 pygame.Rect(ix-p_radius, iy-p_radius,
                                             p_radius*2,  p_radius*2))
                pygame.draw.rect(screen, PAL["bg"],
                                 pygame.Rect(ix-p_radius, iy-p_radius,
                                             p_radius*2,  p_radius*2), 1)

        #---------- Gráficos abajo de cada ciudad ---------------
        # Línea separadora entre la simulación y el gráfico
        pygame.draw.line(screen, PAL["panel_border"],
                         (0, HUD_H + SIM_H), (LEFT_W, HUD_H + SIM_H))

        chart_a.draw(screen, fn_xs, t_list, sA, iA, rA)
        chart_b.draw(screen, fn_xs, t_list, sB, iB, rB)

        # Leyenda S/I/R: una vez, abajo a la izquierda
        lx, ly = CHART_PAD + 4, HUD_H + SIM_H + CHART_H - 14
        for col, lbl in [(PAL["susceptible"],"S"),(PAL["infected"],"I"),(PAL["recovered"],"R")]:
            pygame.draw.rect(screen, col, pygame.Rect(lx, ly, 7, 7))
            px_text(screen, fn_xs, lbl, PAL["white"], (lx+9, ly))
            lx += 26

        #-------- Barra superior del HUD (interfaz en pantalla) -------------------
        px_rect(screen, PAL["panel_bg"], pygame.Rect(0, 0, LEFT_W, HUD_H))
        pygame.draw.line(screen, PAL["panel_border"], (0, HUD_H), (LEFT_W, HUD_H))

        time_txt = "TIEMPO: {:.1f}s".format(t_remain / 1000)
        px_text(screen, fn_md, time_txt, PAL["accent"], (8, 7))

        if paused:
            px_text(screen, fn_lg, "[ PAUSADO ]", PAL["infected"],
                    (LEFT_W // 2, 7), align="center")

        tot_s = sum(1 for c in ciudades for p in c.individuos if p.estado==Estado.SUSCEPTIBLE)
        tot_i = sum(1 for c in ciudades for p in c.individuos if p.estado==Estado.INFECTADO)
        tot_r = sum(1 for c in ciudades for p in c.individuos if p.estado==Estado.RECUPERADO)
        px_text(screen, fn_sm, f"S:{tot_s}  I:{tot_i}  R:{tot_r}",
                PAL["white"], (LEFT_W-8, 8), align="right")

        #------ Panel derecho -------------------------------
        px_rect(screen, PAL["panel_bg"], pygame.Rect(LEFT_W, 0, PANEL_W, HEIGHT))
        pygame.draw.line(screen, PAL["panel_border"],
                         (LEFT_W, 0), (LEFT_W, HEIGHT), 2)

        px_text(screen, fn_lg, "CONTROLES", PAL["accent"],
                (LEFT_W + PANEL_W//2, 10), align="center")
        draw_sep(screen, 32, LEFT_W+6, LEFT_W+PANEL_W-6)

        for sl in all_sliders:
            sl.draw(screen, fn_sm)

        # Separadores de secciones etiquetados
        draw_sep(screen, sep_model_y, LEFT_W+6, LEFT_W+PANEL_W-6,
                 "-- PARAMETROS DEL MODELO --", fn_xs)
        draw_sep(screen, sep_btn_y,   LEFT_W+6, LEFT_W+PANEL_W-6,
                 "-- ACCIONES --", fn_xs)

        btn_vacc.draw(screen, fn_sm)
        btn_restart.draw(screen, fn_sm)

        px_text(screen, fn_xs, "[P] pausar  [ESC] salir",
                PAL["gray"], (LEFT_W + PANEL_W//2, HEIGHT-14), align="center")

        pygame.display.flip()
        clock.tick(60)

    #---- Fin del bloque principal---------------
    pygame.quit()
    if t_list:
        guardar_graficas(t_list, sA, iA, rA, sB, iB, rB)
    sys.exit()


if __name__ == "__main__":
    main()
