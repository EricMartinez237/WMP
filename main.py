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

    # Llista de modes disponibles per anar alternant
    renderer_classes = [WaveRenderer, VisualizerRenderer]
    current_index = 0
    renderer = renderer_classes[current_index](width=800, height=600)

    running = True
    analyzer.start()
    try:
        while running:
            # 1. Entrada d'usuari (gestió d'esdeveniments i canvi de mode)
            action = renderer.process_events()
            if action is False:
                running = False
                break
            elif action == "switch":
                renderer.close() # Tanca el renderer actual
                current_index = (current_index + 1) % len(renderer_classes)
                renderer = renderer_classes[current_index](width=800, height=600) # Obrim el nou mode
 
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