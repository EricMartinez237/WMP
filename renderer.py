import pygame
import colorsys
import math
import random
from halo import Halo

class VisualizerRenderer:
    """Maneja la finestra de Pygame i el dibuix d'elements a la pantalla."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self.width = width
        self.height = height
        pygame.init()
        self.canvas = pygame.Surface((self.width, self.height))
        self.screen = pygame.display.set_mode((self.width, self.height), vsync=1)
        pygame.display.set_caption("Mini Visualizer - OOP Architecture")
        self.clock = pygame.time.Clock()
        self.pulse = 0.0

        self.trail_surface = pygame.Surface((self.width, self.height))
        self.trail_surface.set_alpha(40)  # Transparència per a l'efecte de rastre
        self.bg_color = (10, 10, 20)
        self.trail_surface.fill(self.bg_color)  # Color base de fons, es dibuixa una sola vegada; la transparència ve del set_alpha()
        self.halos = []
        self.max_age = 60.0
        self.rotation_angle = 0.0
        self.hue_shift = 0.0

    def process_events(self) -> bool:
        """Processa la cua d'esdeveniments de Pygame. Retorna False si l'usuari tanca la finestra."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _band_to_color(self, hue: float, value: float, saturation: float = 1.0) -> tuple[int, int, int]:
        """Converteix un to (hue), saturació i lluminositat (value) en un color RGB per a pygame."""
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        return int(r * 255), int(g * 255), int(b * 255)

    def render(self, bass: float, mid: float, treble: float, beat: bool) -> None:
        """Dibuixa un fotograma complet: cercle, barres radials, halos i un pols de color sincronitzat amb els beats."""
        self.canvas.blit(self.trail_surface, (0, 0))    # Dibuixa el rastre del fotograma anterior

        # 1. Cercle central reactiu als greus i mitjans
        center_x, center_y = self.width // 2, self.height // 2
        radius = 50 + bass * 100  # Amplifica l'efecte visual dels greus
        value = min(1.0, 0.4 + mid * 0.6)
        base_color = self._band_to_color(treble, value)
        r_int, g_int, b_int = self._apply_pulse(base_color, self.pulse)
        pygame.draw.circle(
            self.canvas, (r_int, g_int, b_int), (center_x, center_y), int(radius)
        )

        # 2. Barres espectrals (Graves, Mitjans, Aguts)
        N = 9  # Nombre de copies simètriques
        values = [bass, mid, treble]
        bar_w = 15
        self.rotation_angle = (self.rotation_angle + 0.2) % 360 # Incrementa l'angle de rotació per a l'animació
        self.hue_shift = (self.hue_shift + 0.001) % 1.0  # Incrementa el desplaçament de to per a l'animació

        for i in range(N):
            band_index = i % 3 # cicle entre greus/mitjans/aguts
            val = values[band_index]
            hue = (band_index / 3.0 + self.hue_shift) % 1.0  # Desplaçament de to per a l'animació 

            base_color = self._band_to_color(hue, min(1.0, 0.4 + val * 0.6))
            color = self._apply_pulse(base_color, self.pulse)

            angle = math.radians(i * (360.0 / N)+ self.rotation_angle)
            self._draw_radial_bar(angle_rad=angle, length=val * 200, color=color, inner_radius=20, thickness=5)
            h = int(val*100)  # Altura proporcional a la magnitud
            x = int((i + 0.4) * (self.width / N)) # Càlcul width disponible entre barres
            pygame.draw.rect(
                self.canvas, color, (x, self.height - h, bar_w, h)
            )

        # 3. Halos visuals que apareixen amb els beats
        for halo in self.halos:
            halo.update()
            color = halo.get_color(self.bg_color)
            pygame.draw.circle(self.canvas, color, (center_x, center_y), int(halo.radius), width=2)

        self.halos = [h for h in self.halos if h.is_alive()]

        if beat:
            self.pulse = min(1.0, self.pulse + 0.5)
            hue = random.random()  # qualsevol valor entre 0.0 i 1.0 → qualsevol color del cercle cromàtic
            color = self._band_to_color(hue, 1.0)  # value=1.0 perquè neixi ben lluminós
            self.halos.append(Halo(radius=radius, base_color=color, max_age=self.max_age))  # afegim un nou halo amb el color del beat
        else:
            self.pulse *= 0.95

        self.screen.blit(self.canvas, (0, 0))
        pygame.display.flip()
        self.clock.tick(60)
        #print(f"FPS: {self.clock.get_fps():.1f}") #debug


    def _draw_radial_bar(self, angle_rad: float, length: float, color: tuple[int, int, int], inner_radius: int = 30, thickness: int = 20) -> None:
        """Dibuixa una línia des del centre cap enfora, en un angle donat (coordenades polars)."""
        if length < 1:
            return
        center_x, center_y = self.width // 2, self.height // 2
        start_point = (center_x + inner_radius * math.cos(angle_rad), center_y + inner_radius * math.sin(angle_rad))
        end_point = (center_x + (inner_radius + length) * math.cos(angle_rad), center_y + (inner_radius + length) * math.sin(angle_rad))
        pygame.draw.line(self.canvas, color, start_point, end_point, thickness)


    def _apply_pulse(self, color: tuple[int, int, int], pulse: float) -> tuple[int, int, int]:
        """Fon un color cap al fons quan el pols és baix; el mostra viu quan el pols és alt."""
        blend = min(1.0, 0.3 + pulse * 0.95)  # 0.3 = siempre algo visible, 1.0 = color completo
        bg_r, bg_g, bg_b = self.bg_color
        r, g, b = color
        return (
            int(r * blend + bg_r * (1 - blend)),
            int(g * blend + bg_g * (1 - blend)),
            int(b * blend + bg_b * (1 - blend)),
        )



    def close(self) -> None:
        """Tanca l'entorn gràfic de Pygame."""
        pygame.quit()
