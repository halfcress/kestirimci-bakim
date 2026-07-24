import pandas as pd
import numpy as np
from pathlib import Path
import re
import csv

def ozellik_cikar(sinyal):
    sinyal = sinyal.values.astype(float)
    rms = np.sqrt(np.mean(sinyal**2))
    std = np.std(sinyal)
    tepe = np.max(np.abs(sinyal))
    basiklik = _kurtosis(sinyal)
    crest_factor = tepe / rms if rms > 0 else 0
    return [rms, std, tepe, basiklik, crest_factor]

def _kurtosis(sinyal):
    ortalama = np.mean(sinyal)
    sapma = sinyal - ortalama
    payda = np.mean(sapma**2)**2
    return np.mean(sapma**4) / payda if payda > 0 else 0

PENCERE_BOYU = 500
data_klasoru = Path("mcsa_data/Datasets")

satirlar = []
for csv_dosya in data_klasoru.rglob("*.csv"):
    isim = csv_dosya.stem

    if isim == "healthy":
        etiket, hasar_capi, yuk = "Saglikli", 0.0, None
    elif isim.startswith("BRB"):
        m = re.match(r"BRB-[\d-]+-(\d+)watt", isim)
        yuk = int(m.group(1)) if m else None
        etiket, hasar_capi = "BRB", None
    else:
        m = re.match(r"([\d.]+)(inner|outer)-(\d+)watt", isim)
        if not m:
            continue
        hasar_capi, konum, yuk = float(m.group(1)), m.group(2), int(m.group(3))
        etiket = "IR" if konum == "inner" else "OR"

    veri = pd.read_csv(csv_dosya)
    veri.columns = [c.strip() for c in veri.columns]
    sinyal_tam = veri["Current-A"]

    n_pencere = len(sinyal_tam) // PENCERE_BOYU
    for i in range(n_pencere):
        parca = sinyal_tam[i*PENCERE_BOYU : (i+1)*PENCERE_BOYU]
        ozellikler = ozellik_cikar(parca)
        satirlar.append(ozellikler + [etiket, hasar_capi, yuk])

print(f"Toplam {len(satirlar)} pencere oluşturuldu")

with open("ozellik_veriseti_akim.csv", "w", newline="") as f:
    yazici = csv.writer(f)
    yazici.writerow(["RMS", "Std", "Tepe", "Kurtosis", "CrestFactor", "Etiket", "HasarCapi", "Yuk"])
    yazici.writerows(satirlar)

print("ozellik_veriseti_akim.csv olarak kaydedildi")