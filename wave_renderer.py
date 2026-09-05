from collections import deque
import pygame
import math

class WaveRenderer:
    """Maneja la finestra de Pygame i el dibuix d'elements a la pantalla."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        """Inicialitza la finestra, el canvas i l'estat de l'onada."""
        self.width = width
        self.height = height
        pygame.init()
        self.canvas = pygame.Surface((self.width, self.height))
        self.screen = pygame.display.set_mode((self.width, self.height), vsync=1)
        pygame.display.set_caption("Mini Visualizer - OOP Architecture")
        self.clock = pygame.time.Clock()

        self.bg_color = (10, 10, 20)
        self.trail_surface = pygame.Surface((self.width, self.height))
        self.trail_surface.set_alpha(60)  # Transparència per a l'efecte de rastre
        self.trail_surface.fill(self.bg_color)  # Color base de fons, es dibuixa una sola vegada

        self.lags = [5, 10, 15] # frames de retras per cada eco
        self.phase = 0.0
        self.phase_history = deque(maxlen=300)

    def render(self, bass: float, mid: float, treble: float, beat: bool) -> None:
        """Dibuixa un fotograma complet: onada principal, ecos retardats i rastre del fotograma anterior."""
        self.canvas.blit(self.trail_surface, (0, 0))

        # Onada principal
        amplitude = 20 + mid * 80
        self.phase += 0.1 + bass * 0.3
        self.phase_history.append((self.phase, amplitude))
        color = (100, 200, 255)
        points = self.compute_wave_points(self.phase, amplitude)
        pygame.draw.lines(self.canvas, color, False, points, width=3)

        
        # Dibuixem els ecos, cada un més apagat com més gran és el retard
        for idx, lag in enumerate(self.lags):
            if len(self.phase_history) > lag:
                past_phase, past_amplitude = self.phase_history[-1 - lag]
                echo_points = self.compute_wave_points(past_phase, past_amplitude)

                # Com més gran el retard, més apagat el color (barrejat cap al fons)
                fade = 1.0 - (idx + 1) / (len(self.lags) + 1)
                echo_color = tuple(int(c * fade + bg * (1 - fade))for c, bg in zip(color, self.bg_color))

                pygame.draw.lines(self.canvas, echo_color, False, echo_points, width=2)

        self.screen.blit(self.canvas, (0, 0))
        pygame.display.flip()
        self.clock.tick(60)

    def compute_wave_points(self, phase: float, amplitude: float, step: int = 8) -> list[tuple[int, int]]:
        """Calcula els punts de l'onada de so per a la visualització."""
        points = []
        for x in range(0, self.width, step):
            y = (self.height / 2 + amplitude * math.sin(0.02 * x + phase))
            points.append((x, int(y)))
        return points
    
    def process_events(self) -> bool:
        """Processa la cua d'esdeveniments de Pygame. Retorna False si l'usuari tanca la finestra."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def close(self) -> None:
         """Tanca l'entorn gràfic de Pygame."""
         pygame.quit()

        