import numpy as np
from pathlib import Path
import csv

def ozellik_cikar(sinyal):
    rms = np.sqrt(np.mean(sinyal**2))
    std = np.std(sinyal)
    tepe = np.max(np.abs(sinyal))
    basiklik = _kurtosis(sinyal)
    crest_factor = tepe / rms
    return [rms, std, tepe, basiklik, crest_factor]

def _kurtosis(sinyal):
    ortalama = np.mean(sinyal)
    sapma = sinyal - ortalama
    return np.mean(sapma**4) / (np.mean(sapma**2)**2)

PENCERE_BOYU = 2000
data_klasoru = Path("CWRU_Bearing_NumPy/Data/1797 RPM")  # tek makine, tek yük koşulu

satirlar = []

for npz_dosya in data_klasoru.rglob("*.npz"):
    isim = npz_dosya.stem  # örnek: "1797_IR_14_DE12"
    parcalar = isim.split("_")

    if parcalar[1] == "Normal":
        etiket = "Normal"
        hasar_capi = 0
    else:
        if not isim.endswith("DE12"):
            continue
        etiket = parcalar[1].split("@")[0]  # "OR@6" -> "OR"
        hasar_capi = int(parcalar[2])  # 7, 14, 21 ya da 28

    veri = np.load(npz_dosya)
    if "DE" not in veri:
        continue
    sinyal_tam = veri["DE"].flatten()

    n_pencere = len(sinyal_tam) // PENCERE_BOYU
    for i in range(n_pencere):
        parca = sinyal_tam[i*PENCERE_BOYU : (i+1)*PENCERE_BOYU]
        ozellikler = ozellik_cikar(parca)
        satirlar.append(ozellikler + [etiket, hasar_capi])

print(f"Toplam {len(satirlar)} pencere oluşturuldu")

with open("ozellik_veriseti.csv", "w", newline="") as f:
    yazici = csv.writer(f)
    yazici.writerow(["RMS", "Std", "Tepe", "Kurtosis", "CrestFactor", "Etiket", "HasarCapi"])
    yazici.writerows(satirlar)

print("ozellik_veriseti.csv olarak kaydedildi")