"""
Mini Music Visualizer (Modular POO)
-----------------------------------
Estructura orientada a objectes per separar el pipeline del processament d'àudio (DSP)
de la capa de presentació/renderitzat amb Pygame.
"""

from audio_analyzer import AudioAnalyzer
from renderer import VisualizerRenderer



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