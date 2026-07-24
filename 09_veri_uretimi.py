import pandas as pd
import numpy as np

np.random.seed(42)

df = pd.read_csv("ozellik_veriseti.csv")
kategori_karsiligi = {0: "saglikli", 7: "hafif", 14: "orta", 21: "agir", 28: "cok_agir"}
df["siddet"] = df["HasarCapi"].map(kategori_karsiligi)
konum_karsiligi = {"Normal": "saglikli", "IR": "ic_bilezik", "OR": "dis_bilezik", "B": "bilya"}
df["konum"] = df["Etiket"].map(konum_karsiligi)

SIDDET_SIRA = ["saglikli", "hafif", "orta", "agir", "cok_agir"]
KONUM_SIRA = ["saglikli", "ic_bilezik", "dis_bilezik", "bilya"]
SIDDET_SKOR = {"saglikli": 0, "hafif": 1, "orta": 2, "agir": 3, "cok_agir": 4}


def havuz_sec(siddet, konum_baskin, n):
    alt = df[(df["siddet"] == siddet) & (df["konum"] == konum_baskin)]
    if len(alt) < 5:
        alt = df[df["siddet"] == siddet]
    if len(alt) == 0:
        return None
    return alt.sample(n=n, replace=True)


def ornekle(oranlar, konum_baskin, n=60):
    parcalar = []
    for siddet, oran in oranlar.items():
        adet = int(round(n * oran))
        if adet <= 0:
            continue
        secilen = havuz_sec(siddet, konum_baskin, adet)
        if secilen is not None:
            parcalar.append(secilen)
    if not parcalar:
        birlesik = pd.DataFrame({"siddet": ["saglikli"], "konum": ["saglikli"]})
    else:
        birlesik = pd.concat(parcalar, ignore_index=True)

    toplam = len(birlesik)
    siddet_kesir = {f"frac_{s}": (birlesik["siddet"] == s).sum() / toplam for s in SIDDET_SIRA}
    konum_kesir = {f"loc_{k}": (birlesik["konum"] == k).sum() / toplam for k in KONUM_SIRA}
    ortalama_skor = birlesik["siddet"].map(SIDDET_SKOR).mean()

    sonuc = {"ortalama_skor": ortalama_skor}
    sonuc.update(siddet_kesir)
    sonuc.update(konum_kesir)
    return sonuc


def durum_etiketi(skor):
    if skor < 0.5: return "saglikli"
    if skor < 1.5: return "hafif"
    if skor < 2.5: return "orta"
    if skor < 3.5: return "agir"
    return "cok_agir"


MAKINELER = {
    "Makine_1_HizliPatlayan": {
        "konum": "ic_bilezik",
        "aylik": {
            **{ay: {"saglikli": 1.0} for ay in range(1, 9)},
            9:  {"saglikli": 0.85, "hafif": 0.15},
            10: {"saglikli": 0.50, "hafif": 0.20, "orta": 0.30},
            11: {"saglikli": 0.20, "hafif": 0.10, "orta": 0.30, "agir": 0.40},
            12: {"saglikli": 0.05, "orta": 0.15, "agir": 0.35, "cok_agir": 0.45},
        },
        "mudahale_aylari": [],
    },
    "Makine_2_YavasSurunen": {
        "konum": "dis_bilezik",
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
        "mudahale_aylari": [],
    },
    "Makine_3_MudaheleNuksetme": {
        "konum": "bilya",
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
        "mudahale_aylari": [6, 9],
    },
}

AY_ISIMLERI = ["Ocak","Şubat","Mart","Nisan","Mayıs","Haziran","Temmuz","Ağustos","Eylül","Ekim","Kasım","Aralık"]

ONSET_GUN = 15
ONSET_SAAT = 14
ONSET_DAKIKA = 30


for makine_adi, tanim in MAKINELER.items():
    konum_baskin = tanim["konum"]
    aylik_oranlar = tanim["aylik"]

    yillik_satirlar = []
    for ay in range(1, 13):
        ozet = ornekle(aylik_oranlar[ay], konum_baskin, n=80)
        satir = {"ay_no": ay, "ay_adi": AY_ISIMLERI[ay-1], "durum": durum_etiketi(ozet["ortalama_skor"]),
                 "mudahale_yapildi": ay in tanim["mudahale_aylari"]}
        satir.update(ozet)
        yillik_satirlar.append(satir)
    yillik_df = pd.DataFrame(yillik_satirlar)
    yillik_df.to_csv(f"{makine_adi}_yillik.csv", index=False)

    ilk_arizali_ay = next(ay for ay in range(1, 13) if aylik_oranlar[ay].get("saglikli", 0) < 1.0)
    onceki_oran_ay = aylik_oranlar.get(ilk_arizali_ay - 1, {"saglikli": 1.0})
    hedef_oran_ay = aylik_oranlar[ilk_arizali_ay]

    gunluk_satirlar = []
    for ay in range(1, 13):
        if aylik_oranlar[ay].get("saglikli", 0) >= 1.0:
            continue
        for gun in range(1, 31):
            if ay == ilk_arizali_ay:
                gun_orani = onceki_oran_ay if gun < ONSET_GUN else hedef_oran_ay
            else:
                gun_orani = aylik_oranlar[ay]
            ozet = ornekle(gun_orani, konum_baskin, n=40)
            satir = {"ay_no": ay, "gun": gun, "durum": durum_etiketi(ozet["ortalama_skor"])}
            satir.update(ozet)
            gunluk_satirlar.append(satir)
    gunluk_df = pd.DataFrame(gunluk_satirlar)
    gunluk_df.to_csv(f"{makine_adi}_gunluk.csv", index=False)

    saatlik_satirlar = []
    for saat in range(24):
        saat_orani = onceki_oran_ay if saat < ONSET_SAAT else hedef_oran_ay
        ozet = ornekle(saat_orani, konum_baskin, n=30)
        satir = {"gun": ONSET_GUN, "saat": saat, "durum": durum_etiketi(ozet["ortalama_skor"])}
        satir.update(ozet)
        saatlik_satirlar.append(satir)
    saatlik_df = pd.DataFrame(saatlik_satirlar)
    saatlik_df.to_csv(f"{makine_adi}_saatlik.csv", index=False)

    dakikalik_satirlar = []
    for dakika in range(60):
        dakika_orani = onceki_oran_ay if dakika < ONSET_DAKIKA else hedef_oran_ay
        ozet = ornekle(dakika_orani, konum_baskin, n=15)
        satir = {"saat": ONSET_SAAT, "dakika": dakika, "durum": durum_etiketi(ozet["ortalama_skor"])}
        satir.update(ozet)
        dakikalik_satirlar.append(satir)
    dakikalik_df = pd.DataFrame(dakikalik_satirlar)
    dakikalik_df.to_csv(f"{makine_adi}_dakikalik.csv", index=False)

    print(f"{makine_adi}: yıllık={len(yillik_df)}, günlük={len(gunluk_df)}, "
          f"saatlik={len(saatlik_df)} (gün {ONSET_GUN}), dakikalik={len(dakikalik_df)} (saat {ONSET_SAAT})")

print("\nTüm dosyalar (keskin arıza başlangıçlı) oluşturuldu.")