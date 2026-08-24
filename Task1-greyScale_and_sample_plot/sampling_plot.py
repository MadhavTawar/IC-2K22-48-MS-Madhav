import numpy as np
import matplotlib.pyplot as plt
f = 5       # signal frequency in Hz
duration = 1        # seconds

# "continuous" reference signal (1000 points looks smooth to the eye)
t = np.linspace(0, duration, 1000)
signal = np.sin(2 * np.pi * f * t)
for fs in [100, 20, 10, 5]:
    ts = np.arange(0, duration, 1 / fs)     # sample instants    
    samples = np.sin(2 * np.pi * f * ts)    # sampled values
    plt.figure(figsize=(8, 3))
    plt.plot(t, signal, color='lightgray', label='original 5 Hz signal')
    plt.stem(ts, samples, linefmt='C0-', markerfmt='C0o', basefmt=' ')
    plt.plot(ts, samples, 'r--', label=f'reconstructed from fs={fs} Hz')
    plt.title(f'fs = {fs} Hz(Nyquist requires fs > 10 Hz)')
    plt.xlabel('Time (s)'); plt.ylabel('Amplitude')
    plt.legend(); plt.tight_layout(); plt.show()