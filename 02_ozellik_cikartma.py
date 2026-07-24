import numpy as np

normal = np.load('CWRU_Bearing_NumPy/Data/1797 RPM/1797_Normal.npz')

print("Kanallar", list(normal.keys()))

for kanal in normal.keys():
    veri = normal[kanal]
    print(f"{kanal} kanalı boyutu: {veri.shape}, veri tipi: {veri.dtype}")