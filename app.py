import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Estate Command Center", page_icon="🏢", layout="wide")

# --- 2. STYLIZACJA (HYBRYDA: ANALITYKA + OFERTY) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e0e0e0; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* SEKCJA GÓRNA - KPI */
    .analysis-card {
        background: #111827; border: 1px solid #374151; padding: 20px; border-radius: 12px;
        margin-bottom: 20px; text-align: center;
    }
    .big-number { font-size: 32px; font-weight: 800; color: #10b981; } /* Zielony */
    .label { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: 1px; }

    /* SEKCJA DOLNA - KARTY OFERT */
    .property-card {
        background: #1f2937; border-radius: 12px; border: 1px solid #374151;
        overflow: hidden; margin-bottom: 20px; display: flex; flex-direction: column; height: 100%;
    }
    .card-img { width: 100%; height: 200px; object-fit: cover; }
    .card-content { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; }
    
    .price-tag { font-size: 22px; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .title-tag { font-size: 14px; color: #d1d5db; height: 40px; overflow: hidden; margin-bottom: 10px; }
    
    /* AI OPIS w karcie */
    .ai-desc { 
        background: #1e3a8a; color: #bfdbfe; font-size: 11px; padding: 8px; 
        border-radius: 6px; margin-bottom: 10px; line-height: 1.4;
    }

    /* HISTORIA CEN w karcie */
    .history-row { font-size: 11px; color: #9ca3af; display: flex; justify-content: space-between; border-bottom: 1px solid #374151; padding: 2px 0; }

    /* PRZYCISK */
    a.offer-btn {
        display: block; width: 100%; text-align: center; background-color: #2563eb; 
        color: white !important; padding: 10px; border-radius: 8px; text-decoration: none; 
        font-weight: bold; margin-top: auto;
    }
    a.offer-btn:hover { background-color: #1d4ed8; }
</style>
""", unsafe_allow_html=True)

# --- 3. DANE I HISTORIA (DANE ZASZYTE + PLIK) ---
HISTORY_WROCLAW = {
    "date": pd.date_range(start="2023-01-01", periods=24, freq='M'),
    "price_sqm": [
        9800, 9900, 10100, 10200, 10350, 10500, 10800, 11000, 11200, 11300, 11500, 11600,
        11800, 12000, 12200, 12500, 12700, 12900, 13100, 13200, 13400, 13500, 13700, 13900
    ]
}

FOREIGN_MARKETS = { "Berlin": 28000, "Praga": 22000, "Warszawa": 17000, "Wrocław (Ty)": 0 }

LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

HISTORY_FILE = 'historia_cen.csv'

# --- 4. FUNKCJE ---

# A. Obsługa Historii Plikowej (CSV)
def save_price_history(link, price):
    if price == 0: return
    today = datetime.now().strftime("%Y-%m-%d")
    new_data = {"Data": today, "Link": link, "Cena": price}
    
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        check = df[(df['Link'] == link) & (df['Data'] == today)]
        if check.empty:
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(HISTORY_FILE, index=False)
    else:
        pd.DataFrame([new_data]).to_csv(HISTORY_FILE, index=False)

def get_history_list(link):
    if not os.path.exists(HISTORY_FILE): return []
    df = pd.read_csv(HISTORY_FILE)
    df_link = df[df['Link'] == link].sort_values(by="Data", ascending=False).head(3)
    return df_link.to_dict('records')

# B. Scraper
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"title": "Wczytywanie...", "price": 0, "price_str": "---", "area": 0, "rooms": 0, "img": None, "link": url}
    try:
        r = requests.get(url, headers=headers, timeout=4)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            h1 = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1: data["title"] = h1.get_text().strip()
            
            script = soup.find("script", id="__NEXT_DATA__")
            if script:
                j = json.loads(script.string)
                target = j['props']['pageProps']['ad']['target']
                data["price"] = float(target.get('Price', 0))
                data["price_str"] = f"{data['price']:,.0f} zł".replace(",", " ")
                data["area"] = float(target.get('Area', 0))
                rooms = target.get('Rooms_num', [0])
                if isinstance(rooms, list): data["rooms"] = int(rooms[0])
                imgs = j['props']['pageProps']['ad']['images']
                if imgs: data["img"] = imgs[0].get('medium')
                
                # ZAPISUJEMY HISTORIĘ PRZY KAŻDYM POBRANIU
                save_price_history(url, data["price"])
    except: pass
    return data

# C. Analityka Rynkowa (Trend AI)
def predict_market_trend(avg_price_live, user_sqm, years):
    df_hist = pd.DataFrame(HISTORY_WROCLAW)
    X = np.array(range(len(df_hist))).reshape(-1, 1)
    y = df_hist['price_sqm'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Prognoza przyszłości
    future_idx = np.array(range(24, 24 + (years * 12))).reshape(-1, 1)
    future_trend = model.predict(future_idx)
    
    # Obliczenie wartości
    current_val = avg_price_live * user_sqm
    growth_ratio = future_trend[-1] / y[-1]
    future_val = current_val * growth_ratio
    profit = future_val - current_val
    
    return current_val, future_val, profit, df_hist, future_trend

# D. Opis AI dla konkretnego mieszkania
def generate_ai_desc(title, area, price, rooms):
    if area == 0: return "Analiza w toku..."
    sqm = price / area
    desc = f"🤖 **AI:** {rooms}-pokojowe ({area} m²). "
    if sqm < 10000: desc += "Cena OKAZYJNA. "
    elif sqm > 14000: desc += "Standard Premium. "
    else: desc += "Cena rynkowa. "
    return desc

# --- 5. INTERFEJS GŁÓWNY ---

st.sidebar.header("🎛️ Symulator Rynku")
user_sqm_sim = st.sidebar.slider("Metraż symulacji (m²)", 30, 100, 50)
invest_time = st.sidebar.slider("Czas inwestycji (lata)", 1, 5, 2)

st.title("🏙️ Estate Command Center")

if st.button("🚀 SKANUJ OFERTY I RYNEK", type="primary"):
    
    # 1. POBIERANIE DANYCH (MIESZKANIA)
    progress = st.progress(0)
    live_results = []
    
    for i, link in enumerate(LINKS):
        progress.progress((i + 1) / len(LINKS))
        d = get_data(link)
        if d['price'] > 0: live_results.append(d)
    
    progress.empty()
    
    # Obliczanie średniej ceny z Twoich ofert (dla sekcji górnej)
    if live_results:
        avg_live_sqm = sum([d['price']/d['area'] for d in live_results if d['area'] > 0]) / len(live_results)
    else:
        avg_live_sqm = 11500 # Fallback
        
    # --- SEKCJA GÓRNA: ANALITYKA (STRATEGIA) ---
    st.subheader("📊 Analiza Makro (Symulacja Wzrostu)")
    curr, fut, prof, df_h, fut_p = predict_market_trend(avg_live_sqm, user_sqm_sim, invest_time)
    
    kpi1, kpi2, kpi3 = st.columns(3)
    with kpi1:
        st.markdown(f"""<div class="analysis-card"><div class="label">WARTOŚĆ DZIŚ ({user_sqm_sim}m²)</div><div class="big-number">{curr:,.0f} zł</div></div>""", unsafe_allow_html=True)
    with kpi2:
        st.markdown(f"""<div class="analysis-card"><div class="label">PROGNOZA (ZA {invest_time} LAT)</div><div class="big-number" style="color:#10b981">{fut:,.0f} zł</div><small>+{prof:,.0f} zł</small></div>""", unsafe_allow_html=True)
    with kpi3:
        # Berlin Gap
        gap = (FOREIGN_MARKETS["Berlin"] - avg_live_sqm) / avg_live_sqm * 100
        st.markdown(f"""<div class="analysis-card"><div class="label">POTENCJAŁ (GAP DO BERLINA)</div><div class="big-number" style="color:#3b82f6">+{gap:.0f}%</div></div>""", unsafe_allow_html=True)

    # --- SEKCJA DOLNA: TWOJE OFERTY (GRID) ---
    st.divider()
    st.subheader("🏠 Twoje Obserwowane Oferty")
    
    cols = st.columns(3)
    
    for i, d in enumerate(live_results):
        # Generowanie opisu i historii dla konkretnego kafelka
        ai_txt = generate_ai_desc(d['title'], d['area'], d['price'], d['rooms'])
        hist_list = get_history_list(d['link'])
        
        with cols[i % 3]:
            with st.container(border=True): # Bezpieczny kontener
                # Zdjęcie
                if d['img']: st.image(d['img'], use_container_width=True)
                else: st.image("https://via.placeholder.com/400x300", use_container_width=True)
                
                # Dane główne
                st.markdown(f"### {d['price_str']}")
                st.caption(d['title'])
                
                # Parametry
                c1, c2 = st.columns(2)
                with c1: st.metric("Metraż", f"{d['area']} m²")
                with c2: st.metric("Pokoje", f"{d['rooms']}")
                
                # AI Opis
                st.info(ai_txt)
                
                # Link
                st.link_button("👉 PRZEJDŹ DO OFERTY", d['link'], use_container_width=True)
                
                # Historia Cen (Tabelka)
                with st.expander("📜 Historia Ceny"):
                    if hist_list:
                        for h in hist_list:
                            st.markdown(f"<div class='history-row'><span>{h['Data']}</span> <b>{h['Cena']:,.0f} zł</b></div>", unsafe_allow_html=True)
                    else:
                        st.write("Pierwszy zapis.")

    # Pobieranie CSV
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "rb") as f:
            st.download_button("💾 Pobierz Historię (CSV)", f, "historia_cen.csv")

else:
    st.info("Kliknij przycisk, aby zeskanować oferty i przeliczyć prognozy.")
