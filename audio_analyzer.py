
import threading
import numpy as np
import pyaudiowpatch as pyaudio
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