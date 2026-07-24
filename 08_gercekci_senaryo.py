import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv("ozellik_veriseti.csv")

kategori_karsiligi = {0: "saglikli", 7: "hafif", 14: "orta", 21: "agir", 28: "cok_agir"}
df["siddet"] = df["HasarCapi"].map(kategori_karsiligi)

# --- SENARYO TASARIMI (gerçek zaman serisi değil, kurgulanmış demo) ---
senaryo = {}
for ay in range(1, 7):
    senaryo[ay] = {"saglikli": 1.0}
senaryo[7]  = {"saglikli": 0.92, "hafif": 0.08}
senaryo[8]  = {"saglikli": 0.85, "hafif": 0.15}
senaryo[9]  = {"saglikli": 0.78, "hafif": 0.22}
senaryo[10] = {"saglikli": 0.70, "hafif": 0.30}
senaryo[11] = {"saglikli": 0.82, "hafif": 0.18}   # 1. müdahale -- kısmi iyileşme
senaryo[12] = {"saglikli": 0.72, "hafif": 0.23, "orta": 0.05}
senaryo[13] = {"saglikli": 0.62, "hafif": 0.28, "orta": 0.10}
senaryo[14] = {"saglikli": 0.55, "hafif": 0.28, "orta": 0.17}
senaryo[15] = {"saglikli": 0.48, "hafif": 0.27, "orta": 0.25}
senaryo[16] = {"saglikli": 0.42, "hafif": 0.25, "orta": 0.33}
senaryo[17] = {"saglikli": 0.58, "hafif": 0.22, "orta": 0.20}  # 2. müdahale -- yine kısmi
senaryo[18] = {"saglikli": 0.48, "hafif": 0.20, "orta": 0.32}
senaryo[19] = {"saglikli": 0.40, "hafif": 0.18, "orta": 0.42}
senaryo[20] = {"saglikli": 0.32, "hafif": 0.16, "orta": 0.44, "agir": 0.08}
senaryo[21] = {"saglikli": 0.26, "hafif": 0.14, "orta": 0.42, "agir": 0.18}
senaryo[22] = {"saglikli": 0.20, "hafif": 0.12, "orta": 0.38, "agir": 0.30}
senaryo[23] = {"saglikli": 0.16, "hafif": 0.10, "orta": 0.32, "agir": 0.42}
senaryo[24] = {"saglikli": 0.12, "hafif": 0.08, "orta": 0.26, "agir": 0.54}
for ay in range(25, 31):
    ilerleme = (ay - 25) / 5
    senaryo[ay] = {
        "saglikli": max(0.02, 0.10 - ilerleme*0.08),
        "hafif": max(0.02, 0.06 - ilerleme*0.04),
        "orta": max(0.05, 0.20 - ilerleme*0.15),
        "agir": 0.60 - ilerleme*0.20,
        "cok_agir": 0.05 + ilerleme*0.35,
    }
for ay in range(31, 37):
    ilerleme = (ay - 31) / 5
    senaryo[ay] = {
        "saglikli": 0.01,
        "agir": max(0.10, 0.35 - ilerleme*0.25),
        "cok_agir": 0.60 + ilerleme*0.25,
    }

MUDAHALE_AYLARI = [11, 17]

PENCERE_SAYISI_AY_BASI = 100
np.random.seed(42)

siddet_havuzu = {s: df[df["siddet"] == s] for s in df["siddet"].unique()}

aylik_kayitlar = []
for ay in range(1, 37):
    oranlar = senaryo[ay]
    for siddet, oran in oranlar.items():
        n = int(round(PENCERE_SAYISI_AY_BASI * oran))
        if n <= 0 or siddet not in siddet_havuzu:
            continue
        havuz = siddet_havuzu[siddet]
        secilen = havuz.sample(n=n, replace=True, random_state=ay)
        aylik_kayitlar.append(secilen.assign(ay=ay))

senaryo_df = pd.concat(aylik_kayitlar, ignore_index=True)

# --- ÇİZİM (iki katman: üstte şiddet, altta konum) ---
yillar_aylar = []
for yil in [2024, 2025, 2026]:
    for ay in range(1, 13):
        yillar_aylar.append(f"{yil}/{ay}")

renkler_siddet = {"saglikli": "#4CAF50", "hafif": "#FDD835", "orta": "#FB8C00", "agir": "#E53935", "cok_agir": "#8B0000"}
sira_siddet = ["saglikli", "hafif", "orta", "agir", "cok_agir"]

konum_karsiligi = {"Normal": "saglikli", "IR": "ic_bilezik", "OR": "dis_bilezik", "B": "bilya"}
senaryo_df["konum"] = senaryo_df["Etiket"].map(konum_karsiligi)
renkler_konum = {"saglikli": "#4CAF50", "ic_bilezik": "#E53935", "dis_bilezik": "#1E88E5", "bilya": "#8E24AA"}
sira_konum = ["saglikli", "ic_bilezik", "dis_bilezik", "bilya"]

kompozisyon_siddet = senaryo_df.groupby(["ay", "siddet"]).size().unstack(fill_value=0).reindex(range(1, 37), fill_value=0)
kompozisyon_konum = senaryo_df.groupby(["ay", "konum"]).size().unstack(fill_value=0).reindex(range(1, 37), fill_value=0)

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10), sharex=True)

alt_toplam = np.zeros(36)
for s in sira_siddet:
    if s in kompozisyon_siddet.columns:
        degerler = kompozisyon_siddet[s].values
        ax1.bar(range(36), degerler, bottom=alt_toplam, color=renkler_siddet[s], label=s)
        alt_toplam += degerler
ax1.set_ylabel("Pencere sayısı")
ax1.set_title("Şiddete göre kırılım (hafif / orta / ağır / çok ağır)")
ax1.legend(loc="upper left")

alt_toplam = np.zeros(36)
for k in sira_konum:
    if k in kompozisyon_konum.columns:
        degerler = kompozisyon_konum[k].values
        ax2.bar(range(36), degerler, bottom=alt_toplam, color=renkler_konum[k], label=k)
        alt_toplam += degerler
ax2.set_ylabel("Pencere sayısı")
ax2.set_title("Konuma göre kırılım (iç bilezik / dış bilezik / bilya)")
ax2.legend(loc="upper left")

for ay in MUDAHALE_AYLARI:
    for ax in (ax1, ax2):
        ax.axvline(ay - 1, color="blue", linestyle=":", linewidth=1.5)
    ax1.text(ay - 1, PENCERE_SAYISI_AY_BASI + 5, "müdahale", rotation=90,
              color="blue", fontsize=8, ha="center", va="bottom")

plt.xticks(range(36), yillar_aylar, rotation=90, fontsize=8)
plt.xlabel("Ay (SİMÜLE EDİLMİŞ senaryo - gerçek tarih değil)")
fig.suptitle("Kademeli arıza gelişimi, konum kırılımı ve yetersiz müdahaleler - simüle edilmiş senaryo", y=1.0)
plt.tight_layout()
plt.savefig("zaman_grafigi_gercekci.png", dpi=120)
print("zaman_grafigi_gercekci.png kaydedildi")