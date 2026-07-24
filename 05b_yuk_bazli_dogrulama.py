"""Sizinti testi: rastgele pencere bolmesi ile yuk-bazli bolmenin karsilastirilmasi.

CWRU'da yaygin hata: uzun bir kayit pencerelere bolunur, pencereler rastgele
egitim/test olarak ayrilir. Ayni kaydin komsu pencereleri iki tarafa da duser;
model kaydi "ezberleyebilir". Bu betik iki protokolu yan yana kosar:

  A) Rastgele pencere bolmesi  -> iyimser (sizinti riskli) sonuc
  B) Yuk-bazli bolme           -> model, HIC gormedigi calisma kosulunda sinanir
     (1797 / 1772 / 1750 RPM ile egit, 1730 RPM'de test)

03_veri_seti_olustur.py ile ayni ozellikler ve pencere boyu kullanilir;
tek fark, verinin dort yuk kosulunun tamamindan toplanmasidir.
"""
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report


def ozellik_cikar(sinyal):
    rms = np.sqrt(np.mean(sinyal**2))
    std = np.std(sinyal)
    tepe = np.max(np.abs(sinyal))
    basiklik = _kurtosis(sinyal)          # kurtosis = basiklik (basiklik degil!)
    crest_factor = tepe / rms
    return [rms, std, tepe, basiklik, crest_factor]


def _kurtosis(sinyal):
    ortalama = np.mean(sinyal)
    sapma = sinyal - ortalama
    return np.mean(sapma**4) / (np.mean(sapma**2)**2)


PENCERE_BOYU = 2000
OZELLIKLER = ["RMS", "Std", "Tepe", "Kurtosis", "CrestFactor"]
data_koku = Path("CWRU_Bearing_NumPy/Data")   # dort RPM klasorunun tamami

satirlar = []
for npz_dosya in data_koku.rglob("*.npz"):
    isim = npz_dosya.stem                      # ornek: "1772_IR_14_DE12"
    parcalar = isim.split("_")
    rpm = int(parcalar[0])

    if parcalar[1] == "Normal":
        etiket, hasar_capi = "Normal", 0
    else:
        if not isim.endswith("DE12"):          # sadece 12 kHz Drive-End kayitlari
            continue
        etiket = parcalar[1].split("@")[0]     # "OR@6" -> "OR"
        hasar_capi = int(parcalar[2])

    veri = np.load(npz_dosya)
    if "DE" not in veri:
        continue
    sinyal_tam = veri["DE"].flatten()

    for i in range(len(sinyal_tam) // PENCERE_BOYU):
        parca = sinyal_tam[i * PENCERE_BOYU:(i + 1) * PENCERE_BOYU]
        satirlar.append(ozellik_cikar(parca) + [etiket, hasar_capi, rpm])

df = pd.DataFrame(satirlar, columns=OZELLIKLER + ["Etiket", "HasarCapi", "RPM"])
print(f"Toplam pencere: {len(df)}  |  Kayit kosullari (RPM): {sorted(df['RPM'].unique())}")
print(df["Etiket"].value_counts(), "\n")

X, y = df[OZELLIKLER], df["Etiket"]

# ---------- A) RASTGELE PENCERE BOLMESI (sizinti riskli) ----------
X_egt, X_test, y_egt, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)
model_a = RandomForestClassifier(n_estimators=100, random_state=42)
model_a.fit(X_egt, y_egt)
dogruluk_a = accuracy_score(y_test, model_a.predict(X_test))
print(f"[A] Rastgele pencere bolmesi : dogruluk = %{dogruluk_a*100:.1f}  (iyimser)")

# ---------- B) YUK-BAZLI BOLME (durust protokol) ----------
egitim = df[df["RPM"] != 1730]
test   = df[df["RPM"] == 1730]                 # hic gorulmemis yuk kosulu
model_b = RandomForestClassifier(n_estimators=100, random_state=42)
model_b.fit(egitim[OZELLIKLER], egitim["Etiket"])
tahmin = model_b.predict(test[OZELLIKLER])
dogruluk_b = accuracy_score(test["Etiket"], tahmin)
f1_b = f1_score(test["Etiket"], tahmin, average="macro")
print(f"[B] Yuk-bazli bolme (1730 RPM test): dogruluk = %{dogruluk_b*100:.1f}  |  makro F1 = %{f1_b*100:.1f}\n")

siniflar = ["Normal", "B", "IR", "OR"]
print("Karisiklik matrisi (satir = gercek, sutun = tahmin):")
print(pd.DataFrame(confusion_matrix(test["Etiket"], tahmin, labels=siniflar),
                   index=siniflar, columns=siniflar))
print()
print(classification_report(test["Etiket"], tahmin, labels=siniflar, digits=3))

# ---------- C) CAPRAZ KONTROL: her yuk sirayla test ----------
print("Capraz kontrol — her yuk kosulu sirayla test edilirse:")
sonuclar = []
for test_rpm in sorted(df["RPM"].unique()):
    egt = df[df["RPM"] != test_rpm]
    tst = df[df["RPM"] == test_rpm]
    m = RandomForestClassifier(n_estimators=100, random_state=42)
    m.fit(egt[OZELLIKLER], egt["Etiket"])
    a = accuracy_score(tst["Etiket"], m.predict(tst[OZELLIKLER]))
    sonuclar.append(a)
    print(f"  test = {test_rpm} RPM  ->  %{a*100:.1f}")
print(f"  Ortalama: %{np.mean(sonuclar)*100:.1f}")
