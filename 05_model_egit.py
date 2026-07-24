import pandas as pd

df = pd.read_csv("ozellik_veriseti.csv")
print(df["Etiket"].value_counts())
print("\nToplam satır:", len(df))
print("\nİlk 5 satır:\n", df.head())
