# Mini Music Visualizer

A lightweight, object-oriented desktop music visualizer inspired by classic media players. 
It captures system audio in real-time (WASAPI loopback) and renders responsive visual effects 
synchronized with frequency bands and audio beats.

Developed with Claude as a learning copilot to accelerate the DSP implementation; design, architectural decisions and code iterations remain my own work.


## Requirements

- Windows 10/11
- Python 3.9+


## Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```


## Usage

1. Play music on your device (Spotify, WMP, Youtube...).
2. Execute:

```bash
python main.py
```

A window should open with a wave and some bubbles reacting to the frequencies of the music.
If you press the spacebar you will change the render to a pulsating circle and spectrum bars.


## How does it work?

1. **Audio Capture**: Opens a WASAPI loopback stream on the default output device to "listen" directly to system audio without requiring a microphone.

2. **Fast Fourier Transform (FFT)**: Each audio block (`CHUNK = 2048`) is processed using `numpy.fft.rfft` to extract frequency domain energy.

3. **Frequency Bands**: Frequencies are grouped into Bass (20–250 Hz), Mids (250–2000 Hz), and Treble (2000–8000 Hz).

4. **Smoothing**: Values are smoothed using an Exponential Moving Average (`SMOOTHING`) to prevent jarring visual flickering.

5. **Rendering**: `pygame` draws the customized shapes, effects, and frame trails at a stable 60 FPS.


## A Note on the Classic WMP Bug

This project is entirely independent of the original Windows Media Player (WMP). It does not rely on or attempt to fix WMP, meaning you won't encounter the classic legacy visualizer freezing bug when changing tracks here!
