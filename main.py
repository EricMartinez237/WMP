"""
Mini Music Visualizer (Modular POO)
-----------------------------------
Estructura orientada a objectes per separar el pipeline del processament d'àudio (DSP)
de la capa de presentació/renderitzat amb Pygame.
"""

from audio.audio_analyzer import AudioAnalyzer
from renderers.circle.circle_renderer import VisualizerRenderer
from renderers.wave.wave_renderer import WaveRenderer


def main():
    # Instancies els dos components principals
    analyzer = AudioAnalyzer(chunk_size=2048, smoothing=0.1)
    #renderer = WaveRenderer(width=800, height=600) # wave
    renderer = VisualizerRenderer(width=800, height=600) # cercle

    running = True
    analyzer.start()
    try:
        while running:
            # 1. Entrada d'usuari
            running = renderer.process_events()
 
            # 2. Captura i Processament DSP
            bass, mid, treble = analyzer.get_values()
            beat = analyzer.get_beat()

            # 3. Presentació / Renderitzat
            renderer.render(bass, mid, treble, beat)
    finally:
        # Garantim l'alliberament net de recursos
        analyzer.close()
        renderer.close()


if __name__ == "__main__":
    main()