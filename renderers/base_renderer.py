from abc import ABC, abstractmethod
import pygame

class BaseRenderer(ABC):
    """Clase base abstracta per als renders."""

    def __init__(self, width: int, height: int, trail_alpha: int) -> None:
        self.width = width
        self.height = height
        
        pygame.init()
        self.canvas = pygame.Surface((self.width, self.height))
        self.screen = pygame.display.set_mode((self.width, self.height), vsync=1)
        pygame.display.set_caption("Mini Visualizer - OOP Architecture")
        self.clock = pygame.time.Clock()

        self.bg_color = (10, 10, 20)
        self.trail_surface = pygame.Surface((self.width, self.height))
        self.trail_surface.set_alpha(trail_alpha)
        self.trail_surface.fill(self.bg_color)

    def process_events(self) -> bool | str:
        """Processa la cua d'esdeveniments. Retorna False si surt, 'switch' si es vol canviar de mode, o True."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "switch"
        return True

    @abstractmethod
    def render(self, bass: float, mid: float, treble: float, beat: bool) -> None:
        """Mètode abstracte"""
        pass

    def close(self) -> None:
        """Tanca l'entorn gràfic"""
        pygame.quit()