import math
import random
import pygame

class Bubble:
    def __init__(self, x, y, radius, speed=0.5, wobble_amplitude=12, wobble_frequency=0.04):
        self.x = x
        self.base_x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.wobble_amplitude = wobble_amplitude
        self.wobble_frequency = wobble_frequency
        self.age = 0

        # Desfasament aleatori perquè no oscil·lin en sincronia
        self.phase_offset = random.uniform(0, math.pi * 2)

        # Pre-renderitzat de la superfície translúcida de la bombolla
        self.surface = self._create_bubble_surface()

    def update(self):
        """Actualitza la posició i l'edat de la bombolla."""
        self.age += 1
        self.y -= self.speed
        # Effecte bombolla: oscil·lació basada en l'edat
        wobble = math.sin(self.wobble_frequency * self.age + self.phase_offset)
        self.x = self.base_x + self.wobble_amplitude * wobble

    def is_alive(self):
        """Comprova si la bombolla encara és visible a la pantalla."""
        return self.y > self.radius*2

    def _create_bubble_surface(self) -> pygame.Surface:
        """Genera el gràfic translúcid de la bombolla, coherent amb la paleta de l'onada."""
        diameter = int(self.radius * 2) + 4
        surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        center = (diameter // 2, diameter // 2)
        r = int(self.radius)

        # Contorn de la bombolla amb un degradat suau
        pygame.draw.circle(surf, (100, 200, 255, 60), center, r, width=1)

        # Brillantor per a simular la reflexió de la llum
        hl_size = max(1, int(r * 0.25))
        hl_x = int(center[0] - r * 0.35)
        hl_y = int(center[1] - r * 0.35)
        pygame.draw.circle(surf, (200, 230, 255, 90), (hl_x, hl_y), hl_size)
       
        return surf
    
    

    def draw(self, canvas: pygame.Surface):
        """Dibuixa la superfície pre-renderitzada centrant-la en les coordenades actuals."""
        top_left_x = int(self.x - self.surface.get_width() // 2)
        top_left_y = int(self.y - self.surface.get_height() // 2)
        canvas.blit(self.surface, (top_left_x, top_left_y))        