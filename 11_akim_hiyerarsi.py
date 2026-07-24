import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("ozellik_veriseti_akim.csv")

def siddet_grupla(row):
    if row["Etiket"] == "Saglikli": return "saglikli"
    if row["Etiket"] == "BRB": return "BRB"
    mm = row["HasarCapi"]
    if mm <= 0.9: return "hafif"
    if mm <= 1.3: return "orta"
    if mm <= 1.5: return "agir"
    return "cok_agir"

df["siddet"] = df.apply(siddet_grupla, axis=1)
konum_karsiligi = {"Saglikli": "saglikli", "IR": "ic_bilezik", "OR": "dis_bilezik", "BRB": "elektriksel"}
df["konum"] = df["Etiket"].map(konum_karsiligi)

SIDDET_SKOR = {"saglikli": 0, "hafif": 1, "orta": 2, "agir": 3, "cok_agir": 4}


def havuz_sec(siddet, konum_baskin, n):
    alt = df[(df["siddet"] == siddet) & (df["konum"] == konum_baskin)]
    if len(alt) < 5:
        alt = df[df["siddet"] == siddet]
    if len(alt) == 0:
        return None
    return alt.sample(n=n, replace=True)


def ornekle_rulman(oranlar, konum_baskin, n=60):
    parcalar = []
    for siddet, oran in oranlar.items():
        adet = int(round(n * oran))
        if adet <= 0:
            continue
        secilen = havuz_sec(siddet, konum_baskin, adet)
        if secilen is not None:
            parcalar.append(secilen)
    if not parcalar:
        return {"ortalama_skor": 0}
    birlesik = pd.concat(parcalar, ignore_index=True)
    return {"ortalama_skor": birlesik["siddet"].map(SIDDET_SKOR).mean()}


def durum_etiketi(skor):
    if skor < 0.5: return "saglikli"
    if skor < 1.5: return "hafif"
    if skor < 2.5: return "orta"
    if skor < 3.5: return "agir"
    return "cok_agir"


MAKINELER = {
    "Makine_1_HizliPatlayan": {
        "konum": "ic_bilezik", "elektriksel_ay": 4,
        "aylik": {
            **{ay: {"saglikli": 1.0} for ay in range(1, 9)},
            9:  {"saglikli": 0.85, "hafif": 0.15},
            10: {"saglikli": 0.50, "hafif": 0.20, "orta": 0.30},
            11: {"saglikli": 0.20, "hafif": 0.10, "orta": 0.30, "agir": 0.40},
            12: {"saglikli": 0.05, "orta": 0.15, "agir": 0.35, "cok_agir": 0.45},
        },
    },
    "Makine_2_YavasSurunen": {
        "konum": "dis_bilezik", "elektriksel_ay": 2,
        "aylik": {
            **{ay: {"saglikli": 1.0} for ay in range(1, 5)},
            5:  {"saglikli": 0.90, "hafif": 0.10},
            6:  {"saglikli": 0.80, "hafif": 0.20},
            7:  {"saglikli": 0.70, "hafif": 0.25, "orta": 0.05},
            8:  {"saglikli": 0.60, "hafif": 0.25, "orta": 0.15},
            9:  {"saglikli": 0.50, "hafif": 0.20, "orta": 0.30},
            10: {"saglikli": 0.40, "hafif": 0.15, "orta": 0.35, "agir": 0.10},
            11: {"saglikli": 0.30, "hafif": 0.10, "orta": 0.35, "agir": 0.25},
            12: {"saglikli": 0.22, "hafif": 0.08, "orta": 0.30, "agir": 0.40},
        },
    },
    "Makine_3_MudaheleNuksetme": {
        "konum": "bilya", "elektriksel_ay": 2,
        "aylik": {
            **{ay: {"saglikli": 1.0} for ay in range(1, 4)},
            4:  {"saglikli": 0.90, "hafif": 0.10},
            5:  {"saglikli": 0.80, "hafif": 0.20},
            6:  {"saglikli": 0.65, "hafif": 0.25, "orta": 0.10},
            7:  {"saglikli": 0.85, "hafif": 0.15},
            8:  {"saglikli": 0.60, "hafif": 0.25, "orta": 0.15},
            9:  {"saglikli": 0.40, "hafif": 0.20, "orta": 0.30, "agir": 0.10},
            10: {"saglikli": 0.55, "hafif": 0.20, "orta": 0.25},
            11: {"saglikli": 0.25, "hafif": 0.15, "orta": 0.35, "agir": 0.25},
            12: {"saglikli": 0.08, "hafif": 0.05, "orta": 0.20, "agir": 0.42, "cok_agir": 0.25},
        },
    },
}

AY_ISIMLERI = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]
ELEKTRIKSEL_PIK_ORANI = 0.30


for makine_adi, tanim in MAKINELER.items():
    konum_baskin = tanim["konum"]
    aylik_oranlar = tanim["aylik"]
    elektriksel_ay = tanim["elektriksel_ay"]

    yillik_satirlar = []
    for ay in range(1, 13):
        ozet = ornekle_rulman(aylik_oranlar[ay], konum_baskin, n=80)
        elektriksel_oran = ELEKTRIKSEL_PIK_ORANI if ay == elektriksel_ay else 0.0
        yillik_satirlar.append({
            "ay_no": ay, "ay_adi": AY_ISIMLERI[ay-1],
            "ortalama_skor": round(ozet["ortalama_skor"], 3),
            "durum": durum_etiketi(ozet["ortalama_skor"]),
            "elektriksel_anomali_orani": elektriksel_oran,
        })
    yillik_df = pd.DataFrame(yillik_satirlar)
    yillik_df.to_csv(f"{makine_adi}_akim_yillik.csv", index=False)

    gunluk_satirlar = []
    for gun in range(1, 31):
        elektriksel_oran = ELEKTRIKSEL_PIK_ORANI if 10 <= gun <= 15 else 0.0
        gunluk_satirlar.append({
            "ay_no": elektriksel_ay, "gun": gun,
            "elektriksel_anomali_orani": elektriksel_oran,
            "durum": "elektriksel_anomali" if elektriksel_oran > 0 else "saglikli",
        })
    gunluk_df = pd.DataFrame(gunluk_satirlar)
    gunluk_df.to_csv(f"{makine_adi}_akim_gunluk.csv", index=False)

    print(f"{makine_adi}: akım yıllık={len(yillik_df)} satır, akım günlük={len(gunluk_df)} satır "
          f"(elektriksel anomali: ay {elektriksel_ay}, gün 10-15)")

print("\nAkım dosyaları oluşturuldu.")