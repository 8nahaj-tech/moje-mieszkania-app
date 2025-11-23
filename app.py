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

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Estate AI Tycoon", page_icon="📈", layout="wide")

# --- 2. STYLIZACJA (WALL STREET DARK) ---
st.markdown("""
<style>
    .stApp { background-color: #000000; color: #e0e0e0; }
    
    /* Ukrycie UI */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Panel Analityczny */
    .analysis-card {
        background: #111; border: 1px solid #333; padding: 20px; border-radius: 10px;
        margin-bottom: 20px;
    }
    .big-number { font-size: 36px; font-weight: 800; color: #00ff00; }
    .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Wykresy */
    .chart-container { background: #111; padding: 10px; border-radius: 10px; border: 1px solid #222; }
    
    /* Karty Ofert */
    .property-card {
        background: #1a1a1a; border: 1px solid #333; border-radius: 8px; overflow: hidden; margin-bottom: 15px;
    }
    .card-title { font-size: 14px; padding: 10px; color: #fff; height: 50px; overflow: hidden; }
    
    a { text-decoration: none; color: #3b82f6; }
</style>
""", unsafe_allow_html=True)

# --- 3. DANE "WSZCZEPIONE" (SYMULACJA HISTORII I ZAGRANICY) ---
# AI użyje tego, żeby "rozumieć" rynek szerszy niż tylko Twoje 5 linków

# Symulacja trendu cen we Wrocławiu (ostatnie 24 miesiące) - średnia cena za m2
HISTORY_WROCLAW = {
    "date": pd.date_range(start="2023-01-01", periods=24, freq='M'),
    "price_sqm": [
        9800, 9900, 10100, 10200, 10350, 10500, 
        10800, 11000, 11200, 11300, 11500, 11600, # 2023
        11800, 12000, 12200, 12500, 12700, 12900,
        13100, 13200, 13400, 13500, 13700, 13900  # 2024
    ]
}

# Średnie ceny w stolicach obok (dla porównania potencjału)
FOREIGN_MARKETS = {
    "Berlin": 28000,  # zł/m2 (w przeliczeniu)
    "Praga": 22000,
    "Warszawa": 17000,
    "Wrocław (Ty)": 0 # To policzymy
}

LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# Backup danych live
BACKUP_LIVE = [
    {"price": 450000, "area": 35}, {"price": 580000, "area": 48},
    {"price": 720000, "area": 60}, {"price": 850000, "area": 75}
]

# --- 4. ENGINE ANALITYCZNY ---

def predict_future(current_sqm_price):
    # AI bierze historyczne dane Wrocławia
    df_hist = pd.DataFrame(HISTORY_WROCLAW)
    df_hist['month_num'] = range(len(df_hist))
    
    # Uczymy model trendu czasowego
    X = df_hist['month_num'].values.reshape(-1, 1)
    y = df_hist['price_sqm'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    # Przewidujemy +12 miesięcy w przód
    future_months = np.array(range(24, 36)).reshape(-1, 1)
    future_prices = model.predict(future_months)
    
    # Obliczamy % wzrostu rocznego wg modelu
    growth_factor = future_prices[-1] / y[-1]
    
    return growth_factor, df_hist, future_prices

def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"price": 0, "area": 0, "img": None, "link": url}
    try:
        r = requests.get(url, headers=headers, timeout=3)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if script:
                j = json.loads(script.string)
                target = j['props']['pageProps']['ad']['target']
                data["price"] = float(target.get('Price', 0))
                data["area"] = float(target.get('Area', 0))
                imgs = j['props']['pageProps']['ad']['images']
                if imgs: data["img"] = imgs[0].get('medium')
    except: pass
    return data

# --- 5. INTERFEJS ---
st.title("📈 Estate AI: Global Insight")

# Sidebar
st.sidebar.header("🎛️ Parametry Symulacji")
user_sqm = st.sidebar.slider("Twój Metraż (m²)", 25, 120, 50)
investment_years = st.sidebar.slider("Horyzont Inwestycji (lata)", 1, 5, 1)

if st.button("🚀 URUCHOM ANALIZĘ RYNKOWĄ", type="primary"):
    
    # 1. ZBIERANIE DANYCH LIVE
    progress = st.progress(0)
    live_data = []
    
    cols_scan = st.columns(5)
    for i, link in enumerate(LINKS):
        progress.progress((i + 1) / len(LINKS))
        d = get_data(link)
        if d['price'] > 0: live_data.append(d)
        
        # Mini podgląd skanowania
        with cols_scan[i]:
            if d['img']: st.image(d['img'], use_container_width=True)
            else: st.caption("Skanowanie...")
            
    progress.empty()

    # Fallback jeśli Otodom zablokuje
    if not live_data:
        live_data = BACKUP_LIVE
        st.warning("⚠️ Używam danych zapasowych do obliczeń.")

    # 2. OBLICZENIA WARTOŚCI BIEŻĄCEJ
    df_live = pd.DataFrame(live_data)
    
    # Średnia cena za metr z Twoich ofert
    avg_price_per_sqm_live = (df_live['price'] / df_live['area']).mean()
    current_value = avg_price_per_sqm_live * user_sqm

    # 3. PROGNOZA PRZYSZŁOŚCI (AI TREND)
    growth_factor, df_hist, future_prices = predict_future(avg_price_per_sqm_live)
    
    # Korekta o lata inwestycji (procent składany uproszczony)
    total_growth = growth_factor ** investment_years
    future_value = current_value * total_growth
    profit = future_value - current_value

    st.markdown("---")

    # --- SEKCJA GŁÓWNA: KPI ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown(f"""
        <div class="analysis-card">
            <div class="label">WARTOŚĆ DZIŚ</div>
            <div class="big-number">{current_value:,.0f} zł</div>
            <div style="color:#888">{avg_price_per_sqm_live:,.0f} zł/m²</div>
        </div>
        """, unsafe_allow_html=True)
        
    with c2:
        color = "#00ff00" if profit > 0 else "red"
        st.markdown(f"""
        <div class="analysis-card">
            <div class="label">PROGNOZA (ZA {investment_years} LAT)</div>
            <div class="big-number" style="color:{color}">{future_value:,.0f} zł</div>
            <div style="color:{color}">+{profit:,.0f} zł (Szacunek AI)</div>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        # Porównanie z Berlinem
        gap_berlin = (FOREIGN_MARKETS['Berlin'] - avg_price_per_sqm_live) / avg_price_per_sqm_live * 100
        st.markdown(f"""
        <div class="analysis-card">
            <div class="label">POTENCJAŁ (GAP DO BERLINA)</div>
            <div class="big-number" style="color:#3b82f6">+{gap_berlin:.0f}%</div>
            <div style="color:#888">Tyle brakuje do cen w DE</div>
        </div>
        """, unsafe_allow_html=True)

    # --- ZAKŁADKI WYKRESÓW ---
    tab_trend, tab_global = st.tabs(["📉 TREND HISTORYCZNY + PROGNOZA", "🌍 RYNKI ZAGRANICZNE"])
    
    with tab_trend:
        st.markdown("##### Model uczy się na danych historycznych Wrocławia i rysuje przyszłość")
        
        fig, ax = plt.subplots(figsize=(10, 4))
        fig.patch.set_facecolor('#111')
        ax.set_facecolor('#111')
        
        # Historia (Biała linia)
        dates_hist = df_hist['date']
        prices_hist = df_hist['price_sqm'] * user_sqm / 1000 # Cena za całe mieszkanie w tys.
        ax.plot(dates_hist, prices_hist, color='white', label='Historia (Wrocław)', linewidth=2)
        
        # Prognoza (Zielona przerywana)
        future_dates = [dates_hist.iloc[-1] + timedelta(days=30*i) for i in range(1, 13)]
        future_vals = future_prices * user_sqm / 1000
        ax.plot(future_dates, future_vals, color='#00ff00', linestyle='--', label='Prognoza AI', linewidth=2)
        
        # Kropka "Teraz"
        ax.scatter([dates_hist.iloc[-1]], [prices_hist.iloc[-1]], color='#3b82f6', s=100, zorder=5)
        
        ax.set_ylabel("Cena Mieszkania (tys. zł)", color="#888")
        ax.tick_params(colors='#888')
        ax.grid(color='#333', linestyle=':')
        ax.legend(facecolor='#222', labelcolor='white')
        
        st.pyplot(fig)
        
    with tab_global:
        st.markdown("##### Gdzie jesteśmy względem sąsiadów? (Cena za m²)")
        
        # Aktualizujemy Wrocław naszymi danymi
        FOREIGN_MARKETS["Wrocław (Ty)"] = avg_price_per_sqm_live
        
        # Sortowanie
        sorted_markets = dict(sorted(FOREIGN_MARKETS.items(), key=lambda item: item[1], reverse=True))
        
        # Wykres słupkowy
        cities = list(sorted_markets.keys())
        prices = list(sorted_markets.values())
        colors = ['#444'] * len(cities)
        # Podświetlamy Wrocław
        try:
            wro_idx = cities.index("Wrocław (Ty)")
            colors[wro_idx] = '#3b82f6'
        except: pass
        
        fig2, ax2 = plt.subplots(figsize=(10, 4))
        fig2.patch.set_facecolor('#111')
        ax2.set_facecolor('#111')
        
        bars = ax2.bar(cities, prices, color=colors)
        ax2.bar_label(bars, fmt='{:,.0f}', color='white')
        
        ax2.tick_params(colors='white')
        ax2.spines['top'].set_visible(False)
        ax2.spines['right'].set_visible(False)
        ax2.spines['left'].set_visible(False)
        ax2.get_yaxis().set_visible(False)
        
        st.pyplot(fig2)

else:
    st.info("👈 Ustaw metraż w panelu bocznym i kliknij przycisk.")
