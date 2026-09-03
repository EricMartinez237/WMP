"""
Mini Music Visualizer (Modular POO)
-----------------------------------
Estructura orientada a objectes per separar el pipeline del processament d'àudio (DSP)
de la capa de presentació/renderitzat amb Pygame.
"""

import numpy as np
import pyaudiowpatch as pyaudio
import pygame
import threading
import colorsys
import math
import random
from collections import deque


class AudioAnalyzer:
    """Maneja la captura d'àudio loopback (WASAPI) i el processament FFT"""

    def __init__(
        self, chunk_size: int = 2048, smoothing: float = 0.1
    ) -> None:
        self.chunk_size = chunk_size
        self.smoothing = smoothing
        self.lock = threading.Lock()
        self.running = True
        self.beat_flag = False
        self.beat_cooldown = 0

        # Estat del filtre de suavitzat (Exponential Moving Average)
        self.bass_s = 0.0
        self.mid_s = 0.0
        self.treble_s = 0.0

        self.bass_floor = self.bass_ceil = None
        self.mid_floor = self.mid_ceil = None
        self.treble_floor = self.treble_ceil = None

        # Inicialització de PyAudio i cerca de dispositiu Loopback
        self.p = pyaudio.PyAudio()
        self.stream, device = self._get_loopback_stream()

        self.rate = int(device["defaultSampleRate"])
        self.channels = device["maxInputChannels"]
        self.freqs = np.fft.rfftfreq(self.chunk_size, 1.0 / self.rate)
        self.bass_history = deque(maxlen=int(self.rate/self.chunk_size))

    def _get_loopback_stream(self):
        """Cercador intern de dispositius de sortida activa (Loopback)."""
        wasapi_info = self.p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = self.p.get_device_info_by_index(
            wasapi_info["defaultOutputDevice"]
        )

        if not default_speakers.get("isLoopbackDevice", False):
            for loopback in self.p.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                raise RuntimeError(
                    "No s'ha trobat cap dispositiu de loopback per a la vostra sortida d'àudio."
                )

        stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=default_speakers["maxInputChannels"],
            rate=int(default_speakers["defaultSampleRate"]),
            frames_per_buffer=self.chunk_size,
            input=True,
            input_device_index=default_speakers["index"],
        )
        return stream, default_speakers

    def _band_energy(
        self, fft_magnitudes: np.ndarray, low_hz: float, high_hz: float
    ) -> float:
        """Calcula la energia mitjaen un rang espectral de freqüències."""
        mask = (self.freqs >= low_hz) & (self.freqs <= high_hz)
        if not np.any(mask):
            return 0.0
        return float(np.mean(fft_magnitudes[mask]))

    def _normalize(self, value: float, floor: float, ceil: float, attack: float = 0.1, release: float = 0.01, min_span: float = 1.0
    ) -> tuple[float, float, float]:
        """Actualitza floor/ceil amb attack/release i retorna (valor normalitzat 0-1, floor, ceil)."""
        if value > ceil:
            ceil = ceil * (1 - attack) + value * attack
        else:
            ceil = ceil * (1 - release) + value * release

        if value < floor:
            floor = floor * (1 - attack) + value * attack
        else:
            floor = floor * (1 - release) + value * release

        span = max(ceil - floor, min_span)  # nunca normalitzar contra rang practicament nul
        norm = (value - floor) / span if span > 1e-9 else 0.0
        norm = max(0.0, min(1.0, norm))
        return norm, floor, ceil

    
    def _process_frame(self) -> None:
        """Llegeix un bloc d'àudio, el processa, i actualitza l'estat compartit (bass_s, mid_s, treble_s)."""
        
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.float32)

        # Si l'àudio és estèreo/multicanal, amitjanem a Monoaural
        if self.channels > 1:
            audio = audio.reshape(-1, self.channels).mean(axis=1)

        # Transformada Ràpida de Fourier (Temps -> Freqüència)
        fft_mag = np.abs(np.fft.rfft(audio))

        # Extracció de bandes
        bass = self._band_energy(fft_mag, 20, 250)
        if len(self.bass_history) > 0 and bass > np.mean(self.bass_history) * 1.3 and self.beat_cooldown <= 0:
            with self.lock:
                self.beat_flag = True
                self.beat_cooldown = 2.5
        else:
            if self.beat_cooldown > 0:
                self.beat_cooldown = self.beat_cooldown -1
        self.bass_history.append(bass)

        mid = self._band_energy(fft_mag, 250, 2000)
        treble = self._band_energy(fft_mag, 2000, 8000)

        # Primera lectura real
        if self.bass_floor is None:
            self.bass_floor = self.bass_ceil = bass
            self.mid_floor = self.mid_ceil = mid
            self.treble_floor = self.treble_ceil = treble

        bass_norm, self.bass_floor, self.bass_ceil = self._normalize(bass, self.bass_floor, self.bass_ceil)
        mid_norm, self.mid_floor, self.mid_ceil = self._normalize(mid, self.mid_floor, self.mid_ceil)
        treble_norm, self.treble_floor, self.treble_ceil = self._normalize(treble, self.treble_floor, self.treble_ceil)

        # Suavitzat sobre el valor ja normalitzat (0-1)
        with self.lock:
            self.bass_s = self.bass_s * (1 - self.smoothing) + bass_norm * self.smoothing
            self.mid_s = self.mid_s * (1 - self.smoothing) + mid_norm * self.smoothing
            self.treble_s = self.treble_s * (1 - self.smoothing) + treble_norm * self.smoothing

    def get_beat(self)-> bool:
        with self.lock:
            beat = self.beat_flag
            self.beat_flag = False
        return beat

    def _audio_loop(self):
        """Bucle intern per a la captura d'àudio en un fil separat (Thread)."""
        while self.running:
            self._process_frame()

    def start(self) -> None:
        """Inicia el fil de captura d'àudio."""
        self.thread = threading.Thread(target=self._audio_loop, daemon=True)
        self.thread.start()

    def get_values(self) -> tuple[float, float, float]:
        """Retorna les energies filtrades actuals (Graves, Mitjans, Aguts)."""
        with self.lock:
            return self.bass_s, self.mid_s, self.treble_s
        
    def close(self) -> None:
        """Allibera els recursos del sistema d'àudio."""
        self.running = False # el thread ho veurà a la seva pròxima volta del while i sortirà sol
        self.thread.join() # esperem que el fil acabi ABANS de tocar el stream per no tancar l'àudio mentre encara l'està llegint
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()


class VisualizerRenderer:
    """Maneja la finestra de Pygame i el dibuix d'elements a la pantalla."""

    def __init__(self, width: int = 800, height: int = 600) -> None:
        self.width = width
        self.height = height
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Mini Visualizer - OOP Architecture")
        self.clock = pygame.time.Clock()

        self.trail_surface = pygame.Surface((self.width, self.height))
        self.trail_surface.set_alpha(40)  # Transparència per a l'efecte de rastre
        self.trail_surface.fill((10, 10, 20))  # Color base de fons, es dibuixa una sola vegada; la transparència ve del set_alpha()
        self.halos = []
        self.max_age = 60.0

    def process_events(self) -> bool:
        """Processa la cua d'esdeveniments de Pygame. Retorna False si l'usuari tanca la finestra."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def _band_to_color(self, hue: float, value: float) -> tuple[int, int, int]:
        """Converteix un to (hue) i una lluminositat (value) en un color RGB per a pygame."""
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, value)
        return int(r * 255), int(g * 255), int(b * 255)

    def render(self, bass: float, mid: float, treble: float, beat: bool) -> None:
        """Dibuixa un fotograma complet: cercle, barres radials i halos que neixen amb cada beat."""
        self.screen.blit(self.trail_surface, (0, 0))  # Dibuixa el rastre del fotograma anterior

        # 1. Cercle central reactiu als greus i mitjans
        center_x, center_y = self.width // 2, self.height // 2
        radius = 50 + bass * 100  # Amplifica l'efecte visual dels greus
        value = 0.4 + mid * 0.6
        r_int, g_int, b_int = self._band_to_color(treble, value)
        pygame.draw.circle(
            self.screen, (r_int, g_int, b_int), (center_x, center_y), int(radius)
        )

        # 2. Barres espectrals (Graves, Mitjans, Aguts)
        N = 9  # Nombre de copies simètriques
        values = [bass, mid, treble]
        bar_w = 15

        for i in range(N):
            band_index = i % 3 # cicle entre greus/mitjans/aguts
            val = values[band_index]
            hue = band_index / 3.0
            color = self._band_to_color(hue, 0.4 + val * 0.6)
            angle = math.radians(i * (360.0 / N))
            self._draw_radial_bar(angle_rad=angle, length=val * 200, color=color, inner_radius=20, thickness=5)
            h = int(val*100)  # Altura proporcional a la magnitud
            x = int((i + 0.4) * (self.width / N)) # Càlcul width disponible entre barres
            pygame.draw.rect(
                self.screen, color, (x, self.height - h, bar_w, h)
            )

        for halo in self.halos:
            halo["radius"] += 3
            halo["age"] += 1
            life_fraction = halo["age"] / self.max_age

            br, bg, bb = halo["base_color"]
            r = br * (1 - life_fraction) + 10 * life_fraction
            g = bg * (1 - life_fraction) + 10 * life_fraction
            b = bb * (1 - life_fraction) + 20 * life_fraction
            fade_color = (int(r), int(g), int(b))

            pygame.draw.circle(self.screen, fade_color, (center_x, center_y), int(halo["radius"]), width=2)

        self.halos = [h for h in self.halos if h["age"] / self.max_age < 1.0]

        

        if beat:
            hue = random.random()  # cualquier valor entre 0.0 y 1.0 → cualquier color del círculo cromático
            color = self._band_to_color(hue, 1.0)  # value=1.0 para que nazca bien brillante
            self.halos.append({"radius": radius, "age": 0, "base_color": color})
    
        pygame.display.flip()
        self.clock.tick(60)

    def _draw_radial_bar(self, angle_rad: float, length: float, color: tuple[int, int, int], inner_radius: int = 30, thickness: int = 20) -> None:
        """Dibuixa una línia des del centre cap enfora, en un angle donat (coordenades polars)."""

        center_x, center_y = self.width // 2, self.height // 2
        start_point = (center_x + inner_radius * math.cos(angle_rad), center_y + inner_radius * math.sin(angle_rad))
        end_point = (center_x + (inner_radius + length) * math.cos(angle_rad), center_y + (inner_radius + length) * math.sin(angle_rad))
        pygame.draw.line(self.screen, color, start_point, end_point, thickness)



    def close(self) -> None:
        """Tanca l'entorn gràfic de Pygame."""
        pygame.quit()


def main():
    # Instancies els dos components principals
    analyzer = AudioAnalyzer(chunk_size=2048, smoothing=0.1)
    renderer = VisualizerRenderer(width=800, height=600)

    running = True
    analyzer.start()
    try:
        while running:
            # 1. Entrada d'usuari
            running = renderer.process_events()
 
            # 2. Captura i Processament DSP
            bass, mid, treble = analyzer.get_values()
            beat = analyzer.get_beat()
            #print(f"Bass: {bass:.2f}, Mid: {mid:.2f}, Treble: {treble:.2f}") #debug

            # 3. Presentació / Renderitzat
            renderer.render(bass, mid, treble, beat)
    finally:
        # Garantim l'alliberament net de recursos
        analyzer.close()
        renderer.close()


if __name__ == "__main__":
    main()