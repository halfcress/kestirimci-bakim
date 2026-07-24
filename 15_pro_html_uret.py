import pandas as pd
import json

MAKINELER = {
    "Makine_1_HizliPatlayan": "Makine 1 — Hızlı Patlayan",
    "Makine_2_YavasSurunen": "Makine 2 — Yavaş Sürünen",
    "Makine_3_MudaheleNuksetme": "Makine 3 — Müdahale-Nüksetme",
}
SKOR = {"saglikli": 0, "hafif": 1, "orta": 2, "agir": 3, "cok_agir": 4}

veri = {}
tum_olaylar = []

for key, ad in MAKINELER.items():
    yillik = pd.read_csv(f"{key}_yillik.csv")
    gunluk = pd.read_csv(f"{key}_gunluk.csv")
    saatlik = pd.read_csv(f"{key}_saatlik.csv")
    dakikalik = pd.read_csv(f"{key}_dakikalik.csv")
    akim_yillik = pd.read_csv(f"{key}_akim_yillik.csv")
    akim_gunluk = pd.read_csv(f"{key}_akim_gunluk.csv")

    gunluk_by_ay = {}
    for ay_no, grup in gunluk.groupby("ay_no"):
        gunluk_by_ay[str(int(ay_no))] = grup.to_dict(orient="records")

    veri[key] = {
        "ad": ad,
        "yillik": yillik.to_dict(orient="records"),
        "gunluk_by_ay": gunluk_by_ay,
        "onset_gun": int(saatlik["gun"].iloc[0]),
        "saatlik": saatlik.to_dict(orient="records"),
        "onset_saat": int(dakikalik["saat"].iloc[0]),
        "dakikalik": dakikalik.to_dict(orient="records"),
        "akim_yillik": akim_yillik.to_dict(orient="records"),
    }

    onceki_skor = 0
    for _, row in yillik.iterrows():
        skor = SKOR[row["durum"]]
        if skor > onceki_skor:
            tum_olaylar.append({"ay": row["ay_adi"], "ay_no": int(row["ay_no"]), "makine": ad,
                                 "olay": f"Şiddet arttı → {row['durum'].upper()}", "tip": "kotulesme"})
        if row["mudahale_yapildi"]:
            tum_olaylar.append({"ay": row["ay_adi"], "ay_no": int(row["ay_no"]), "makine": ad,
                                 "olay": "Bakım müdahalesi yapıldı", "tip": "mudahale"})
        onceki_skor = skor

    for _, row in akim_yillik.iterrows():
        if row["elektriksel_anomali_orani"] > 0:
            tum_olaylar.append({"ay": row["ay_adi"], "ay_no": int(row["ay_no"]), "makine": ad,
                                 "olay": "MCSA elektriksel anomali tespit etti", "tip": "mcsa"})

tum_olaylar.sort(key=lambda o: o["ay_no"])

VERI_JSON = json.dumps(veri, ensure_ascii=False)
OLAYLAR_JSON = json.dumps(tum_olaylar, ensure_ascii=False)

HTML = r"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<title>Endüstri İzleme Paneli</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0b0d12; --sidebar: #12151c; --panel: #171b23; --panel2: #1c212b;
    --border: #262b35; --text: #e6e9ee; --muted: #7d8797;
    --accent: #ff6b35; --accent-soft: rgba(255,107,53,0.15);
    --electric: #22d3ee; --electric-soft: rgba(34,211,238,0.15);
  }
  * { box-sizing: border-box; }
  body {
    background: var(--bg); color: var(--text); margin: 0;
    font-family: 'Inter', system-ui, sans-serif; font-size: 14px;
    display: flex; min-height: 100vh;
  }
  .mono { font-family: 'JetBrains Mono', monospace; }

  #sidebar {
    width: 240px; background: var(--sidebar); border-right: 1px solid var(--border);
    padding: 20px 16px; flex-shrink: 0;
  }
  .logo { font-weight: 700; font-size: 16px; letter-spacing: 0.3px; margin-bottom: 24px; display:flex; align-items:center; gap:8px;}
  .logo .dot { width:9px; height:9px; border-radius:50%; background: var(--accent); display:inline-block; }
  .nav-item { padding: 8px 10px; border-radius: 6px; color: var(--muted); font-size: 13px; margin-bottom: 2px; cursor: pointer; }
  .nav-item.active { background: var(--panel2); color: var(--text); }
  .sidebar-label { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin: 20px 0 8px 10px; }
  .makine-row {
    padding: 10px 10px; border-radius: 6px; cursor: pointer; display:flex; align-items:center; gap:10px;
    color: var(--muted); font-size: 13px; margin-bottom: 2px; border: 1px solid transparent;
  }
  .makine-row:hover { background: var(--panel2); }
  .makine-row.secili { background: var(--accent-soft); border-color: var(--accent); color: var(--text); }
  .status-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink:0; }

  #main { flex: 1; padding: 28px 32px; overflow-x: hidden; }
  .top-header { display:flex; justify-content:space-between; align-items:baseline; margin-bottom: 20px; }
  .top-header h1 { font-size: 22px; margin:0; }
  .top-header .tarih { color: var(--muted); font-size: 13px; }

  .stat-kartlar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
  .stat-kart { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 16px 18px; }
  .stat-kart.vurgulu { background: linear-gradient(135deg, var(--accent), #d84315); border-color: var(--accent); }
  .stat-num { font-size: 28px; font-weight: 700; font-family: 'JetBrains Mono', monospace; }
  .stat-lbl { font-size: 12px; color: var(--muted); margin-top: 2px; }
  .stat-kart.vurgulu .stat-lbl { color: rgba(255,255,255,0.85); }

  .grid-2 { display: grid; grid-template-columns: 2.1fr 1fr; gap: 16px; margin-bottom: 20px; align-items: start; }
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 18px; }
  .panel-baslik { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px; }
  .breadcrumb { font-size: 12px; color: var(--muted); margin-bottom: 10px; }
  .breadcrumb span { cursor: pointer; color: var(--accent); }
  .breadcrumb span:hover { text-decoration: underline; }

  .gauge-wrap { display:flex; flex-direction:column; align-items:center; padding: 6px 0 2px; }
  .gauge-durum { font-size: 13px; color: var(--muted); margin-top: 2px; margin-bottom: 6px;}

  .uyari-kutu { background: rgba(255,107,53,0.12); border-left: 3px solid var(--accent); padding: 10px 14px; font-size: 13px; border-radius: 4px; margin-top: 10px; }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align:left; color: var(--muted); font-weight: 500; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; padding: 8px 10px; border-bottom: 1px solid var(--border); }
  td { padding: 10px 10px; border-bottom: 1px solid var(--border); }
  tr:last-child td { border-bottom: none; }
  .etiket { display:inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .etiket.kotulesme { background: rgba(231,76,60,0.15); color: #e74c3c; }
  .etiket.mudahale { background: rgba(52,152,219,0.15); color: #3498db; }
  .etiket.mcsa { background: var(--electric-soft); color: var(--electric); }
  @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
  .fade-in { animation: fadeIn 0.3s ease; }
</style>
</head>
<body>

<div id="sidebar">
  <div class="logo"><span class="dot"></span>ENDÜSTRİ İZLEME</div>
  <div class="nav-item active" id="navAnaIzleme" onclick="anaIzlemeGoster()">Ana İzleme</div>
  <div class="nav-item">Raporlar</div>
  <div class="nav-item">Ayarlar</div>
  <div class="sidebar-label">Makineler</div>
  <div id="makineListesi"></div>
</div>

<div id="main">
  <div class="top-header">
    <h1>Kestirimci Bakım Paneli</h1>
    <div class="tarih mono">SİMÜLE EDİLMİŞ SENARYO — gerçek tarih değildir</div>
  </div>

  <div class="stat-kartlar" id="statKartlar"></div>

  <div class="panel" id="genelGorunumu" style="display:none; margin-bottom:20px;">
    <div class="panel-baslik">Genel Sağlık Durumu</div>
    <div id="genelKartlar" style="display:flex; gap:24px; justify-content:center; padding:16px 0;"></div>
    <div style="text-align:center;">
      <button id="detaylarBtn" onclick="olaylarToggle()" style="background:var(--accent-soft); color:var(--accent); border:1px solid var(--accent); padding:8px 20px; border-radius:6px; cursor:pointer; font-family:Inter; font-size:13px;">Detaylar ▾</button>
    </div>
    <div id="olaylarWrap" style="max-height:0; overflow:hidden; transition:max-height 0.35s ease; margin-top:14px;">
      <table>
        <thead><tr><th>Ay</th><th>Makine</th><th>Olay</th></tr></thead>
        <tbody id="olaylarTablosu"></tbody>
      </table>
    </div>
  </div>

  <div id="detayGorunumu">
    <div class="grid-2">
      <div class="panel">
        <div class="breadcrumb" id="breadcrumb"></div>
        <div id="grafikAlani"></div>
      </div>
      <div>
        <div class="panel" style="margin-bottom:16px;">
          <div class="panel-baslik">Güncel Şiddet Skoru</div>
          <div class="gauge-wrap" id="gaugeAlani"></div>
          <div class="gauge-durum" id="gaugeDurumYazi"></div>
        </div>
        <div class="panel">
          <div class="panel-baslik">Konum Dağılımı (güncel ay)</div>
          <div id="konumDonut"></div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
const VERI = %%VERI_JSON%%;
const OLAYLAR = %%OLAYLAR_JSON%%;
const RENK = {saglikli:"#4C9A6A", hafif:"#D4A017", orta:"#C9752B", agir:"#B0413E", cok_agir:"#6B1F1F"};
const KONUM_RENK = {saglikli:"#4C9A6A", ic_bilezik:"#B0413E", dis_bilezik:"#3E6B99", bilya:"#7A5C99"};
const SIDDET_SIRA = ["saglikli","hafif","orta","agir","cok_agir"];
const KONUM_SIRA = ["saglikli","ic_bilezik","dis_bilezik","bilya"];
const DURUM_METNI = {saglikli:"İYİ", hafif:"İZLEMEDE", orta:"MÜDAHALE GEREKEBİLİR", agir:"ACİL MÜDAHALE", cok_agir:"KRİTİK"};
const SKOR_MAP = {saglikli:0, hafif:1, orta:2, agir:3, cok_agir:4};
const MAKINE_RENK = {};
Object.keys(VERI).forEach((k,i) => MAKINE_RENK[VERI[k].ad] = ["#ff6b35","#22d3ee","#a78bfa"][i]);
let gorunum = "genel";

let secili = Object.keys(VERI)[0];
let yol = [{tip:"makine", key: secili, etiket: VERI[secili].ad}];

function guncelSatir(key) { const y = VERI[key].yillik; return y[y.length-1]; }

function makineListesiCiz() {
  const kutu = document.getElementById("makineListesi");
  kutu.innerHTML = "";
  Object.keys(VERI).forEach(key => {
    const durum = guncelSatir(key).durum;
    const div = document.createElement("div");
    div.className = "makine-row" + (gorunum === "makine" && key === secili ? " secili" : "");
    div.innerHTML = `<span class="status-dot" style="background:${RENK[durum]}"></span>${VERI[key].ad}`;
    div.onclick = () => { secili = key; gorunum = "makine"; yol = [{tip:"makine", key: key, etiket: VERI[key].ad}]; document.getElementById("navAnaIzleme").classList.remove("active"); render(); };
    kutu.appendChild(div);
  });
}

function statKartlarCiz() {
  const anahtarlar = Object.keys(VERI);
  const kritik = anahtarlar.filter(k => ["agir","cok_agir"].includes(guncelSatir(k).durum)).length;
  const izlemede = anahtarlar.filter(k => ["hafif","orta"].includes(guncelSatir(k).durum)).length;
  const mcsaToplam = OLAYLAR.filter(o => o.tip === "mcsa").length;
  const ortalamaSkor = (anahtarlar.reduce((s,k) => s + SKOR_MAP[guncelSatir(k).durum], 0) / anahtarlar.length).toFixed(1);

  const kartlar = [
    {deger: kritik, etiket: "Kritik / Acil Müdahale", vurgulu: kritik > 0},
    {deger: izlemede, etiket: "İzlemede", vurgulu: false},
    {deger: mcsaToplam, etiket: "MCSA Anomali Kaydı", vurgulu: false},
    {deger: ortalamaSkor, etiket: "Ortalama Şiddet Skoru", vurgulu: false},
  ];
  const kutu = document.getElementById("statKartlar");
  kutu.innerHTML = kartlar.map(k => `
    <div class="stat-kart ${k.vurgulu ? 'vurgulu':''}">
      <div class="stat-num">${k.deger}</div>
      <div class="stat-lbl">${k.etiket}</div>
    </div>`).join("");
}

function gaugeCiz() {
  const satir = guncelSatir(secili);
  const skor = SKOR_MAP[satir.durum];
  const renk = RENK[satir.durum];
  const trace = [{
    type: "pie", values: [skor, 4-skor], hole: 0.72, rotation: 90, direction: "clockwise",
    marker: {colors: [renk, "#242933"]}, textinfo: "none", hoverinfo: "none", sort: false
  }];
  const layout = {
    height: 180, width: 220, showlegend: false, margin: {t:0,b:0,l:0,r:0},
    paper_bgcolor: "transparent",
    annotations: [{text: skor.toFixed(1), font:{size:26, color: renk, family:"JetBrains Mono"}, showarrow:false, y:0.5}]
  };
  Plotly.newPlot("gaugeAlani", trace, layout, {displayModeBar:false, responsive:true});
  document.getElementById("gaugeDurumYazi").innerHTML = `<div style="text-align:center;color:${renk};font-weight:600;">${DURUM_METNI[satir.durum]}</div>`;
}

function konumDonutCiz() {
  const satir = guncelSatir(secili);
  const degerler = KONUM_SIRA.map(k => (satir["loc_"+k]||0)*100);
  const trace = [{type:"pie", labels: KONUM_SIRA, values: degerler, hole:0.55,
    marker:{colors: KONUM_SIRA.map(k=>KONUM_RENK[k])}, textinfo:"label+percent", textfont:{size:10,color:"#e6e9ee"}}];
  const layout = {height:220, margin:{t:10,b:10,l:10,r:10}, showlegend:false, paper_bgcolor:"transparent",
    font:{family:"Inter", color:"#e6e9ee"}};
  Plotly.newPlot("konumDonut", trace, layout, {displayModeBar:false, responsive:true});
}

function olaylarTablosuCiz() {
  const govde = document.getElementById("olaylarTablosu");
  govde.innerHTML = OLAYLAR.map(o => `
    <tr><td class="mono">${o.ay}</td><td><span style="color:${MAKINE_RENK[o.makine]};font-weight:600;">● ${o.makine}</span></td>
    <td><span class="etiket ${o.tip}">${o.olay}</span></td></tr>`).join("");
}

function breadcrumbCiz() {
  const bc = document.getElementById("breadcrumb");
  bc.innerHTML = yol.map((a,i) => `<span onclick="git(${i})">${a.etiket}</span>`).join(" &nbsp;›&nbsp; ");
}
function git(i) { yol = yol.slice(0, i+1); render(); }

function anaIzlemeGoster() {
  gorunum = "genel";
  document.getElementById("navAnaIzleme").classList.add("active");
  render();
}

function olaylarToggle() {
  const wrap = document.getElementById("olaylarWrap");
  const btn = document.getElementById("detaylarBtn");
  if (wrap.style.maxHeight === "0px" || wrap.style.maxHeight === "") {
    wrap.style.maxHeight = wrap.scrollHeight + "px";
    btn.textContent = "Detaylar ▴";
  } else {
    wrap.style.maxHeight = "0px";
    btn.textContent = "Detaylar ▾";
  }
}

function genelKartlarCiz() {
  const kutu = document.getElementById("genelKartlar");
  kutu.innerHTML = Object.keys(VERI).map(key => {
    const durum = guncelSatir(key).durum;
    return `<div onclick="makineSec('${key}')" style="cursor:pointer; text-align:center;">
      <div style="width:110px;height:110px;border-radius:50%;border:4px solid ${RENK[durum]};
        display:flex;align-items:center;justify-content:center;background:var(--panel2);margin:0 auto 8px;">
        <span style="font-size:12px;color:${RENK[durum]};font-weight:700;">${VERI[key].ad.split('—')[0].trim()}</span>
      </div>
      <div style="font-size:12px;color:${RENK[durum]};font-weight:600;">${DURUM_METNI[durum]}</div>
    </div>`;
  }).join("");
}

function makineSec(key) {
  secili = key; gorunum = "makine"; yol = [{tip:"makine", key:key, etiket:VERI[key].ad}];
  document.getElementById("navAnaIzleme").classList.remove("active");
  render();
}

function ikiPanelGrafik(elementId, rows, xKolon, xBaslik) {
  const x = rows.map(r => r[xKolon]);
  const traces = [];
  SIDDET_SIRA.forEach(s => traces.push({x, y: rows.map(r=>(r["frac_"+s]||0)*100), name:s, type:"bar",
    marker:{color:RENK[s]}, xaxis:"x", yaxis:"y", legendgroup:"s"}));
  KONUM_SIRA.forEach(k => traces.push({x, y: rows.map(r=>(r["loc_"+k]||0)*100), name:k, type:"bar",
    marker:{color:KONUM_RENK[k]}, xaxis:"x2", yaxis:"y2", legendgroup:"k"}));
  const layout = {
    grid:{rows:2,columns:1,pattern:"independent"}, barmode:"stack", bargap:0.15, height:480,
    paper_bgcolor:"#171b23", plot_bgcolor:"#171b23",
    font:{color:"#e6e9ee", family:"Inter", size:11},
    margin:{t:20,b:36,r:140},
    xaxis:{title:xBaslik, gridcolor:"#262b35"}, xaxis2:{title:xBaslik, gridcolor:"#262b35"},
    yaxis:{title:"% Şiddet", domain:[0.55,1], gridcolor:"#262b35"},
    yaxis2:{title:"% Konum", domain:[0,0.45], gridcolor:"#262b35"},
    legend:{x:1.02, xanchor:"left", y:1, yanchor:"top", font:{size:10}}
  };
  Plotly.newPlot(elementId, traces, layout, {responsive:true, displaylogo:false});
}

function render() {
  makineListesiCiz(); statKartlarCiz();
  document.getElementById("detayGorunumu").style.display = gorunum === "makine" ? "" : "none";
  document.getElementById("genelGorunumu").style.display = gorunum === "genel" ? "" : "none";
  if (gorunum === "genel") { genelKartlarCiz(); olaylarTablosuCiz(); return; }
  gaugeCiz(); konumDonutCiz(); olaylarTablosuCiz(); breadcrumbCiz();
  const alan = document.getElementById("grafikAlani");
  alan.innerHTML = "";
  const veri = VERI[secili];

  if (yol.length === 1) {
    const div = document.createElement("div");
    div.id = "chartHolder";
    div.className = "fade-in";
    alan.appendChild(div);
    ikiPanelGrafik("chartHolder", veri.yillik, "ay_adi", "Ay");

    const elektrikselAylar = veri.akim_yillik.filter(r => r.elektriksel_anomali_orani > 0);
    if (elektrikselAylar.length > 0) {
      const ayAdlari = elektrikselAylar.map(r => veri.yillik[r.ay_no-1].ay_adi);
      Plotly.addTraces("chartHolder", {x:ayAdlari, y:ayAdlari.map(()=>105), mode:"markers+text", type:"scatter",
        marker:{symbol:"star", size:15, color:"#22d3ee", line:{width:1,color:"black"}},
        text:ayAdlari.map(()=>"MCSA"), textposition:"top center", name:"MCSA", xaxis:"x", yaxis:"y"});
    }
    document.getElementById("chartHolder").on("plotly_click", function(data) {
      const ayAdi = data.points[0].x;
      const satir = veri.yillik.find(r => r.ay_adi === ayAdi);
      if (veri.gunluk_by_ay[String(satir.ay_no)]) {
        yol.push({tip:"ay", ay_no: satir.ay_no, etiket: ayAdi}); render();
      } else {
        alan.insertAdjacentHTML("beforeend", `<div class="uyari-kutu">${ayAdi} tamamen sağlıklıydı, günlük detay yok.</div>`);
      }
    });

  } else if (yol.length === 2) {
    const rows = veri.gunluk_by_ay[String(yol[1].ay_no)];
    const div = document.createElement("div"); div.id = "chartHolder"; div.className = "fade-in"; alan.appendChild(div);
    ikiPanelGrafik("chartHolder", rows, "gun", "Gün");
    document.getElementById("chartHolder").on("plotly_click", function(data) {
      const gun = data.points[0].x;
      if (gun === veri.onset_gun) { yol.push({tip:"gun", gun:gun, etiket:"Gün "+gun}); render(); }
      else { alan.insertAdjacentHTML("beforeend", `<div class="uyari-kutu">Gün ${gun} için saatlik kayıt yok (sadece gün ${veri.onset_gun} için var).</div>`); }
    });

  } else if (yol.length === 3) {
    const div = document.createElement("div"); div.id = "chartHolder"; div.className = "fade-in"; alan.appendChild(div);
    ikiPanelGrafik("chartHolder", veri.saatlik, "saat", "Saat");
    document.getElementById("chartHolder").on("plotly_click", function(data) {
      const saat = data.points[0].x;
      if (saat === veri.onset_saat) { yol.push({tip:"saat", saat:saat, etiket:"Saat "+saat}); render(); }
      else { alan.insertAdjacentHTML("beforeend", `<div class="uyari-kutu">Saat ${saat} için dakikalık kayıt yok (sadece saat ${veri.onset_saat} için var).</div>`); }
    });

  } else if (yol.length === 4) {
    const div = document.createElement("div"); div.id = "chartHolder"; div.className = "fade-in"; alan.appendChild(div);
    ikiPanelGrafik("chartHolder", veri.dakikalik, "dakika", "Dakika");
  }
}

render();
</script>
</body>
</html>
"""

HTML = HTML.replace("%%VERI_JSON%%", VERI_JSON).replace("%%OLAYLAR_JSON%%", OLAYLAR_JSON)

with open("dashboard_pro.html", "w", encoding="utf-8") as f:
    f.write(HTML)

print("dashboard_pro.html oluşturuldu.")
print(f"Toplam olay sayısı: {len(tum_olaylar)}")