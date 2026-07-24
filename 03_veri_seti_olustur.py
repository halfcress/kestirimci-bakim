import numpy as np

def ozellik_cikar(sinyal):
    "Bir titreşim sinyalinde 5 temel istatistiksel özellik çıkart."
    sinyal = sinyal.flatten()
    rms = np.sqrt(np.mean(sinyal**2))
    std = np.std(sinyal)
    tepe = np.max(np.abs(sinyal))
    basiklik = _kurtosis(sinyal)
    crest_factor = tepe / rms
    return {

        "RMS": rms,
        "Std": std,
        "Tepe Değer": tepe,
        "Kurtosis (Basıklık)": basiklik,
        "Crest factor": crest_factor

    }

def _kurtosis(sinyal):
    ortalama = np.mean(sinyal)
    sapma = sinyal - ortalama
    return np.mean(sapma**4) / (np.mean(sapma**2)**2)

dosyalar = {
    "Sağlıklı": "CWRU_Bearing_NumPy/Data/1797 RPM/1797_Normal.npz",
    "İç bilezik arızası": "CWRU_Bearing_NumPy/Data/1797 RPM/1797_IR_14_DE12.npz",
    "Dış bilezik arızası": "CWRU_Bearing_NumPy/Data/1797 RPM/1797_OR@6_14_DE12.npz",
    "Bilya arızası": "CWRU_Bearing_NumPy/Data/1797 RPM/1797_B_14_DE12.npz",
}

for isim, yol in dosyalar.items():
    veri = np.load(yol)
    de_sinyali = veri["DE"][:120000]  
    ozellikler = ozellik_cikar(de_sinyali)
    print(f"\n{isim}:")
    for k, v in ozellikler.items():
        print(f"  {k}: {v:.4f}")
