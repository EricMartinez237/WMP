class Halo:
    """Representa un halo visual que es dibuixa a la pantalla."""
    
    def __init__(self, radius: float, base_color: tuple, max_age: float = 60.0, growth_speed: float = 3.0) -> None:
        self.radius = radius
        self.base_color = base_color
        self.max_age = max_age
        self.growth_speed = growth_speed
        self.age = 0.0

    def update(self) -> None:
        """Actualitza l'estat del halo (creixement i envelliment)."""
        self.radius += self.growth_speed
        self.age += 1.0

    def is_alive(self) -> bool:
        """Retorna True si el halo encara és visible (no ha arribat a la seva edat màxima)."""
        return self.age < self.max_age

    def get_color(self, bg_color: tuple[int, int, int]) -> tuple[int, int, int]:
        """Calcula el color actual del halo basat en la seva edat, fonent-se cap al fons donat."""
        life_fraction = self.age / self.max_age
        br, bg, bb = self.base_color
        r = br * (1 - life_fraction) + bg_color[0] * life_fraction
        g = bg * (1 - life_fraction) + bg_color[1] * life_fraction
        b = bb * (1 - life_fraction) + bg_color[2] * life_fraction
        return (int(r), int(g), int(b))