import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv("ozellik_veriseti.csv")

etiket_karsiligi = {
    "Normal": "saglikli",
    "IR": "ic_bilezik",
    "OR": "dis_bilezik",
    "B": "bilya"
}
df["durum"] = df["Etiket"].map(etiket_karsiligi)

ozellik_sutunlari = ["RMS", "Std", "Tepe", "Kurtosis", "CrestFactor"]

saglikli_veri = df[df["durum"] == "saglikli"][ozellik_sutunlari]
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(saglikli_veri)

tum_ozellikler = df[ozellik_sutunlari]
df["uzaklik_skoru"] = -model.decision_function(tum_ozellikler)

# ÖNEMLİ: bu gerçek tarih değil, SİMÜLE EDİLMİŞ bir sıralama.
saglikli_kisim = df[df["durum"] == "saglikli"].sample(frac=1, random_state=1)
arizali_kisim = df[df["durum"] != "saglikli"].sample(frac=1, random_state=1)

sirali_df = pd.concat([saglikli_kisim, arizali_kisim]).reset_index(drop=True)

# 2024/1'den 2026/12'ye kadar 36 ay oluştur
aylar = []
for yil in [2024, 2025, 2026]:
    for ay in range(1, 13):
        aylar.append(f"{yil}/{ay}")

# Elimizdeki tüm pencereleri bu 36 aya eşit şekilde dağıt
n_pencere = len(sirali_df)
sirali_df["ay_index"] = (sirali_df.index * 36) // n_pencere
sirali_df["ay_etiketi"] = sirali_df["ay_index"].apply(lambda i: aylar[i])

# Her ay için, 4 durumdan kaçar pencere olduğunu say
aylik_kompozisyon = sirali_df.groupby(["ay_etiketi", "durum"]).size().unstack(fill_value=0)
aylik_kompozisyon = aylik_kompozisyon.reindex(aylar, fill_value=0)

renkler = {"saglikli": "#4CAF50", "bilya": "#FFA726", "dis_bilezik": "#FB8C00", "ic_bilezik": "#E53935"}
sira = ["saglikli", "bilya", "dis_bilezik", "ic_bilezik"]

plt.figure(figsize=(14, 6))
alt_toplam = np.zeros(36)
for durum in sira:
    if durum in aylik_kompozisyon.columns:
        degerler = aylik_kompozisyon[durum].values
        plt.bar(range(36), degerler, bottom=alt_toplam, color=renkler[durum], label=durum)
        alt_toplam += degerler

plt.xticks(range(36), aylar, rotation=90, fontsize=8)
plt.xlabel("Ay (SİMÜLE EDİLMİŞ senaryo - gerçek tarih değil)")
plt.ylabel("Pencere sayısı")
plt.title("Ay bazında sağlık durumu kompozisyonu - simüle edilmiş senaryo")
plt.legend()
plt.tight_layout()
plt.savefig("zaman_grafigi.png", dpi=120)
print("zaman_grafigi.png kaydedildi")