import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Kestirimci Bakım Dashboard", layout="wide", page_icon="🔧")

MAKINELER = {
    "Makine_1_HizliPatlayan": "Makine 1",
    "Makine_2_YavasSurunen": "Makine 2",
    "Makine_3_MudaheleNuksetme": "Makine 3",
}
DURUM_METNI = {
    "saglikli": "İYİ", "hafif": "İZLEMEDE", "orta": "MÜDAHALE GEREKEBİLİR",
    "agir": "ACİL MÜDAHALE", "cok_agir": "KRİTİK",
}
RENK_HEX = {"saglikli": "#2ECC71", "hafif": "#F1C40F", "orta": "#E67E22", "agir": "#E74C3C", "cok_agir": "#8B0000"}
KONUM_RENK = {"saglikli": "#2ECC71", "ic_bilezik": "#E74C3C", "dis_bilezik": "#3498DB", "bilya": "#9B59B6"}
SIDDET_SIRA = ["saglikli", "hafif", "orta", "agir", "cok_agir"]
KONUM_SIRA = ["saglikli", "ic_bilezik", "dis_bilezik", "bilya"]

if "secili_makine" not in st.session_state:
    st.session_state.secili_makine = None
if "secili_ay" not in st.session_state:
    st.session_state.secili_ay = None
if "secili_gun" not in st.session_state:
    st.session_state.secili_gun = None
if "secili_saat" not in st.session_state:
    st.session_state.secili_saat = None


def iki_panel_grafik(df, x_kolon, x_baslik, baslik):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                         subplot_titles=("Şiddete göre kırılım", "Konuma göre kırılım"),
                         vertical_spacing=0.12)
    for s in SIDDET_SIRA:
        col = f"frac_{s}"
        if col in df.columns:
            fig.add_trace(go.Bar(x=df[x_kolon], y=df[col] * 100, name=s, marker_color=RENK_HEX[s],
                                  legendgroup="siddet", showlegend=True), row=1, col=1)
    for k in KONUM_SIRA:
        col = f"loc_{k}"
        if col in df.columns:
            fig.add_trace(go.Bar(x=df[x_kolon], y=df[col] * 100, name=k, marker_color=KONUM_RENK[k],
                                  legendgroup="konum", showlegend=True), row=2, col=1)
    fig.update_layout(barmode="stack", height=550, title=baslik, margin=dict(t=60, b=10))
    fig.update_yaxes(title_text="%", row=1, col=1)
    fig.update_yaxes(title_text="%", row=2, col=1)
    fig.update_xaxes(title_text=x_baslik, row=2, col=1)
    return fig


st.title("🔧 Kestirimci Bakım Dashboard")
st.caption("SİMÜLE EDİLMİŞ senaryo — gerçek tarih/veri değildir")

kolonlar = st.columns(3)
durum_metinleri = []
for i, (makine_key, makine_ad) in enumerate(MAKINELER.items()):
    yillik = pd.read_csv(f"{makine_key}_yillik.csv")
    guncel = yillik.iloc[-1]
    with kolonlar[i]:
        st.markdown(
            f"<div style='text-align:center; border:4px solid {RENK_HEX[guncel['durum']]}; border-radius:50%; "
            f"width:150px; height:150px; display:flex; align-items:center; justify-content:center; margin:auto;'>"
            f"<b>{makine_ad}</b></div>", unsafe_allow_html=True)
        if st.button(f"{makine_ad} detayına git", key=f"btn_{makine_key}", use_container_width=True):
            st.session_state.secili_makine = makine_key
            st.session_state.secili_ay = None
            st.session_state.secili_gun = None
            st.session_state.secili_saat = None
    durum_metinleri.append(f"**{makine_ad}:** {DURUM_METNI[guncel['durum']]}")

st.markdown(
    f"<div style='border:2px solid red; padding:16px; border-radius:8px;'>"
    f"<b>Makinelerin genel sağlık durumu:</b><br><br>" + "<br>".join(durum_metinleri) + "</div>",
    unsafe_allow_html=True,
)

st.divider()

if st.session_state.secili_makine:
    makine_key = st.session_state.secili_makine
    makine_ad = MAKINELER[makine_key]
    yillik = pd.read_csv(f"{makine_key}_yillik.csv")
    akim_yillik = pd.read_csv(f"{makine_key}_akim_yillik.csv")

    st.subheader(f"📊 {makine_ad} — Yıllık Görünüm (aya tıklamak için aşağıdan seç)")
    fig = iki_panel_grafik(yillik, "ay_adi", "Ay", f"{makine_ad} — 12 Aylık Kırılım")

    elektriksel_aylar = akim_yillik[akim_yillik["elektriksel_anomali_orani"] > 0]
    if len(elektriksel_aylar) > 0:
        ay_adlari = yillik.loc[elektriksel_aylar["ay_no"] - 1, "ay_adi"]
        fig.add_trace(go.Scatter(x=ay_adlari, y=[105] * len(ay_adlari), mode="markers+text",
                                  marker=dict(symbol="star", size=16, color="cyan", line=dict(width=1, color="black")),
                                  text=["MCSA ⚡"] * len(ay_adlari), textposition="top center",
                                  name="MCSA elektriksel anomali", showlegend=True), row=1, col=1)
    st.plotly_chart(fig, use_container_width=True)

    if len(elektriksel_aylar) > 0:
        ay_adi_ilk = yillik.loc[elektriksel_aylar.iloc[0]["ay_no"] - 1, "ay_adi"]
        st.info(f"⚡ **{ay_adi_ilk}** ayında titreşim sağlıklı görünüyordu, ama MCSA (akım analizi) elektriksel "
                f"kökenli bir anomali yakaladı — iki sensör birbirinin kör noktasını kapatıyor.")

    ay_secenekleri = yillik["ay_adi"].tolist()
    secilen_ay = st.selectbox("Aya tıkla (seç)", ay_secenekleri, key=f"ay_sec_{makine_key}")
    if st.button("Bu ayın günlük kırılımına in", key=f"gun_git_{makine_key}"):
        st.session_state.secili_ay = int(yillik[yillik["ay_adi"] == secilen_ay]["ay_no"].iloc[0])
        st.session_state.secili_gun = None
        st.session_state.secili_saat = None

if st.session_state.secili_makine and st.session_state.secili_ay:
    makine_key = st.session_state.secili_makine
    ay_no = st.session_state.secili_ay
    gunluk = pd.read_csv(f"{makine_key}_gunluk.csv")
    gunluk_bu_ay = gunluk[gunluk["ay_no"] == ay_no]

    st.divider()
    if len(gunluk_bu_ay) == 0:
        st.success(f"Bu ay tamamen sağlıklıydı, günlük detay kaydı tutulmadı.")
    else:
        st.subheader(f"📅 Ay {ay_no} — Günlük Kırılım")
        fig2 = iki_panel_grafik(gunluk_bu_ay, "gun", "Gün", f"Ay {ay_no} — Günlük Kırılım")
        st.plotly_chart(fig2, use_container_width=True)

        gun_secenekleri = gunluk_bu_ay["gun"].tolist()
        secilen_gun = st.selectbox("Güne tıkla (seç)", gun_secenekleri, key=f"gun_sec_{makine_key}")
        if st.button("Bu günün saatlik kırılımına in", key=f"saat_git_{makine_key}"):
            st.session_state.secili_gun = secilen_gun
            st.session_state.secili_saat = None

if st.session_state.secili_makine and st.session_state.secili_gun:
    makine_key = st.session_state.secili_makine
    gun = st.session_state.secili_gun
    saatlik = pd.read_csv(f"{makine_key}_saatlik.csv")

    st.divider()
    if saatlik["gun"].iloc[0] != gun:
        st.warning(f"Bu gün için saatlik kayıt tutulmadı (sadece arızanın başladığı gün için detay var: gün {saatlik['gun'].iloc[0]}).")
    else:
        st.subheader(f"⏱️ Gün {gun} — Saatlik Kırılım")
        fig3 = iki_panel_grafik(saatlik, "saat", "Saat", f"Gün {gun} — Saatlik Kırılım")
        st.plotly_chart(fig3, use_container_width=True)

        saat_secenekleri = saatlik["saat"].tolist()
        secilen_saat = st.selectbox("Saate tıkla (seç)", saat_secenekleri, key=f"saat_sec_{makine_key}")
        if st.button("Bu saatin dakikalık kırılımına in", key=f"dakika_git_{makine_key}"):
            st.session_state.secili_saat = secilen_saat

if st.session_state.secili_makine and st.session_state.secili_saat is not None:
    makine_key = st.session_state.secili_makine
    saat = st.session_state.secili_saat
    dakikalik = pd.read_csv(f"{makine_key}_dakikalik.csv")

    st.divider()
    if dakikalik["saat"].iloc[0] != saat:
        st.warning(f"Bu saat için dakikalık kayıt tutulmadı (sadece arızanın başladığı saat için detay var: saat {dakikalik['saat'].iloc[0]}).")
    else:
        st.subheader(f"🔬 Saat {saat} — Dakikalık Kırılım (arızanın tam başlangıç anı)")
        fig4 = iki_panel_grafik(dakikalik, "dakika", "Dakika", f"Saat {saat} — Dakikalık Kırılım")
        st.plotly_chart(fig4, use_container_width=True)