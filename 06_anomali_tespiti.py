import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

df = pd.read_csv("ozellik_veriseti.csv")

# İngilizce etiketleri Türkçeye çeviriyoruz
etiket_karsiligi = {
    "Normal": "saglikli",
    "IR": "ic_bilezik",
    "OR": "dis_bilezik",
    "B": "bilya"
}
df["durum"] = df["Etiket"].map(etiket_karsiligi)

ozellik_sutunlari = ["RMS", "Std", "Tepe", "Kurtosis", "CrestFactor"]

# SADECE sağlıklı veriyi ayır -- model yalnızca bunu görecek
saglikli_veri = df[df["durum"] == "saglikli"][ozellik_sutunlari]

print(f"Modeli eğitmek için kullanılan sağlıklı pencere sayısı: {len(saglikli_veri)}")

# Isolation Forest: "bu veri noktası, gördüğüm çoğunluktan ne kadar izole/uzak" mantığıyla çalışan bir anomali tespit algoritması
model = IsolationForest(contamination=0.05, random_state=42)
model.fit(saglikli_veri)

# ŞİMDİ tüm veriye (sağlıklı + arızalı hepsine) uzaklık skoru soruyoruz
tum_ozellikler = df[ozellik_sutunlari]
df["uzaklik_skoru"] = -model.decision_function(tum_ozellikler)  # eksi işareti: büyük sayı = daha anormal

print("\nDurumlara göre ortalama uzaklık skoru:")
print(df.groupby("durum")["uzaklik_skoru"].mean().sort_values())