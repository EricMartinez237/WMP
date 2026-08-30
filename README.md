# Mini Music Visualizer

Visualizer de música minimalista, inspirat en les figures del Windows
Media Player de tota la vida. captura l'àudio que sona al sistema (loopback)
i dibuixa formes que reacciones a les freqüències en temps real.



Desenvolupat amb Claude com a copilot d'aprenentatge per accelerar la implementació de DSP; el disseny, les decisions darquitectura i les iteracions són meves.

## Requisits

- Windows 10/11
- Python 3.9+

## Instalació

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ús

1. Posa música sonant al teu equip (Spotify, WMP, YouTube...).
2. Executa:

```bash
python main.py
```

Hauria d'obrir-se una finestra amb un cercle que pulsa amb els greus i tres
barres d'espectre (greus / mitjans / aguts).

## Com funciona

1. **Captura d'àudio**: s'obre un stream de loopback sobre el dispositiu
   de sortida por defecte, és a dir, "escolta" el mateix que surt pels teus
   altaveus, sense necessitat de micròfon.
2. **FFT**: cada bloc d'àudio (`CHUNK = 1024`) es transforma amb
   `numpy.fft.rfft` per obtenir l'energía a cada freqüència.
3. **Bandes**: s'agrupen les freqüències en greus (20–250 Hz), mitjans
   (250–2000 Hz) i aguts (2000–8000 Hz).
4. **Suavizat**: els valors es suavitzen amb una mitja
   (`SMOOTHING`) per tal que les figures no parpallegin bruscament.
5. **Render**: `pygame` dibuixa el cercle i les barres a cada frame (60 fps).


## Nota sobre el bug de Windows Media Player

Aquest projecte és independent de WMP: no en depèn ni intenta
arreglar-ho, així que el bug del visualizer que es queda "congelat" al
canviar de cançó no t'afectarà aquí.
