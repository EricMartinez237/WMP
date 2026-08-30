"""
Mini Music Visualizer (Modular POO)
-----------------------------------
Estructura orientada a objectes per separar el pipeline del processament d'àudio (DSP)
de la capa de presentació/renderitzat amb Pygame.
"""

import numpy as np
import pyaudiowpatch as pyaudio
import pygame


class AudioAnalyzer:
    """Maneja la captura d'àudio loopback (WASAPI) i el processament FFT"""

    def __init__(
        self, chunk_size: int = 1024, smoothing: float = 0.3
    ) -> None:
        self.chunk_size = chunk_size
        self.smoothing = smoothing

        # Estat del filtre de suavitzat (Exponential Moving Average)
        self.bass_s = 0.0
        self.mid_s = 0.0
        self.treble_s = 0.0

        # Inicialització de PyAudio i cerca de dispositiu Loopback
        self.p = pyaudio.PyAudio()
        self.stream, device = self._get_loopback_stream()

        self.rate = int(device["defaultSampleRate"])
        self.channels = device["maxInputChannels"]
        self.freqs = np.fft.rfftfreq(self.chunk_size, 1.0 / self.rate)

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
        """Calcula la energía media en un rango espectral de frecuencias."""
        mask = (self.freqs >= low_hz) & (self.freqs <= high_hz)
        if not np.any(mask):
            return 0.0
        return float(np.mean(fft_magnitudes[mask]))

    def update(self) -> tuple[float, float, float]:
        """Llegeix el buffer del micròfon/loopback i actualitza les energies filtrades.

        Returns:
            tuple[float, float, float]: Energies filtrades de (Graves, Mitjans, Aguts).
        """
        data = self.stream.read(self.chunk_size, exception_on_overflow=False)
        audio = np.frombuffer(data, dtype=np.float32)

        # Si l'àudio és estèreo/multicanal, amitjanem a Monoaural
        if self.channels > 1:
            audio = audio.reshape(-1, self.channels).mean(axis=1)

        # Transformada Ràpida de Fourier (Temps -> Freqüència)
        fft_mag = np.abs(np.fft.rfft(audio))

        # Extracció de bandes
        bass = self._band_energy(fft_mag, 20, 250)
        mid = self._band_energy(fft_mag, 250, 2000)
        treble = self._band_energy(fft_mag, 2000, 8000)

        # Suavitzat suau
        self.bass_s = self.bass_s * (1 - self.smoothing) + bass * self.smoothing
        self.mid_s = self.mid_s * (1 - self.smoothing) + mid * self.smoothing
        self.treble_s = (
            self.treble_s * (1 - self.smoothing) + treble * self.smoothing
        )

        return self.bass_s, self.mid_s, self.treble_s

    def close(self) -> None:
        """Allibera els recursos del sistema d'àudio."""
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

    def process_events(self) -> bool:
        """Processa la cua d'esdeveniments de Pygame. Retorna False si l'usuari tanca la finestra."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
        return True

    def render(self, bass: float, mid: float, treble: float) -> None:
        """Dibuixa un fotograma complet a partir de les magnituds de freqüència."""
        self.screen.fill((10, 10, 20))

        # 1. Cercle central reactiu als greus
        center_x, center_y = self.width // 2, self.height // 2
        radius = 50 + min(bass * 2, 200)
        pygame.draw.circle(
            self.screen, (255, 80, 120), (center_x, center_y), int(radius)
        )

        # 2. Barres espectrals (Graves, Mitjans, Aguts)
        bar_w = 40
        values = [bass, mid, treble]
        colors = [(255, 100, 100), (100, 255, 100), (100, 150, 255)]

        for i, (val, color) in enumerate(zip(values, colors)):
            h = min(int(val * 3), 400)
            x = 150 + i * 200
            pygame.draw.rect(
                self.screen, color, (x, self.height - h, bar_w, h)
            )

        pygame.display.flip()
        self.clock.tick(60)

    def close(self) -> None:
        """Tanca l'entorn gràfic de Pygame."""
        pygame.quit()


def main():
    # Instancies els dos components principals
    analyzer = AudioAnalyzer(chunk_size=1024, smoothing=0.3)
    renderer = VisualizerRenderer(width=800, height=600)

    running = True
    try:
        while running:
            # 1. Entrada d'usuari
            running = renderer.process_events()

            # 2. Captura i Processament DSP
            bass, mid, treble = analyzer.update()

            # 3. Presentació / Renderitzat
            renderer.render(bass, mid, treble)
    finally:
        # Garantim l'alliberament net de recursos
        analyzer.close()
        renderer.close()


if __name__ == "__main__":
    main()