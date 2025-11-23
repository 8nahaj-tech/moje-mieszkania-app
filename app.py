import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np

# --- IMPORTY AI ---
try:
    from sklearn.linear_model import LinearRegression
    import matplotlib.pyplot as plt
    AI_READY = True
except ImportError:
    AI_READY = False

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Estate AI Core", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    
    /* Sekcja AI */
    .ai-container {
        background: linear-gradient(180deg, #1e3a8a 0%, #111827 100%);
        border: 1px solid #3b82f6;
        padding: 25px; border-radius: 15px; margin-top: 20px;
    }
    .prediction-value { font-size: 40px; font-weight: 800; color: #60a5fa; text-shadow: 0 0 20px rgba(59, 130, 246, 0.5); }
    .debug-info { font-size: 12px; color: #6b7280; font-family: monospace; }
</style>
""", unsafe_allow_html=True)

# --- 2. LINKI (LIVE) ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 3. DANE ZAPASOWE (GDYBY OTODOM BLOKOWAŁ) ---
# To są przykładowe dane z Wrocławia, żeby AI miało na czym pracować w razie awarii
BACKUP_DATA = [
    {"price": 450000, "area": 35, "title": "Dane historyczne 1"},
    {"price": 580000, "area": 48, "title": "Dane historyczne 2"},
    {"price": 720000, "area": 60, "title": "Dane historyczne 3"},
    {"price": 850000, "area": 75, "title": "Dane historyczne 4"},
    {"price": 1200000, "area": 100, "title": "Dane historyczne 5"},
]

# --- 4. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"price": 0, "area": 0, "img": None, "link": url, "found": False}
    try:
        r = requests.get(url, headers=headers, timeout=5)
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
                if data["price"] > 0: data["found"] = True
    except: pass
    return data

# --- 5. MÓZG AI ---
def brain_process(df, user_area):
    # Regresja Liniowa
    X = df['area'].values.reshape(-1, 1)
    y = df['price'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    predicted_price = model.predict([[user_area]])[0]
    return model, predicted_price

# --- 6. INTERFEJS ---
st.title("🧠 Mózg Nieruchomości")
st.write("System uczy się relacji CENA <-> METRAŻ na podstawie dostępnych ofert.")

if not AI_READY:
    st.error("⚠️ Brak bibliotek AI! Zaktualizuj requirements.txt")
    st.stop()

# SUWAK DO STEROWANIA AI (Zawsze widoczny)
st.sidebar.header("🎛️ Panel Sterowania AI")
user_sqm = st.sidebar.slider("Jaki metraż chcesz wycenić?", 25, 120, 50, step=1)

if st.button("🚀 URUCHOM PROCES UCZENIA"):
    
    # 1. ZBIERANIE DANYCH
    live_data = []
    progress = st.progress(0)
    
    for i, link in enumerate(LINKS):
        progress.progress((i + 1) / len(LINKS))
        d = get_data(link)
        if d['found']:
            live_data.append(d)
    
    progress.empty()

    # 2. DECYZJA: UŻYWAMY DANYCH LIVE CZY ZAPASOWYCH?
    df = pd.DataFrame(live_data)
    
    source_info = ""
    if len(df) >= 2:
        source_info = f"✅ Sukces! AI uczy się na {len(df)} aktualnych ofertach z Otodom."
    else:
        source_info = f"⚠️ Otodom zablokował połączenie (pobrano {len(df)} ofert). AI przełącza się na **DANE ZAPASOWE**, żeby pokazać wynik."
        df = pd.DataFrame(BACKUP_DATA) # Ładujemy backup

    st.info(source_info)

    # 3. OBLICZENIA AI
    model, prediction = brain_process(df, user_sqm)

    # 4. WIZUALIZACJA WYNIKU
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class="ai-container">
            <div style="color:#9ca3af; font-size:14px">Szacowana cena dla <b>{user_sqm} m²</b>:</div>
            <div class="prediction-value">{prediction:,.0f} zł</div>
            <div style="font-size:11px; margin-top:10px; color:#34d399">
                Model: Regresja Liniowa<br>
                Baza wiedzy: {len(df)} nieruchomości
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        # WYKRES
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#1f2937')
        
        # Punkty z danych
        ax.scatter(df['area'], df['price'], color='#3b82f6', s=80, label='Znane oferty')
        
        # Linia trendu (jak myśli AI)
        x_range = np.linspace(df['area'].min(), df['area'].max(), 100).reshape(-1, 1)
        y_range = model.predict(x_range)
        ax.plot(x_range, y_range, color='white', linestyle='--', alpha=0.3, label='Linia trendu')
        
        # Wynik użytkownika
        ax.scatter([user_sqm], [prediction], color='#ef4444', s=200, label='TWÓJ WYNIK', zorder=5)
        
        ax.set_xlabel("Metraż (m²)", color="white")
        ax.set_ylabel("Cena (PLN)", color="white")
        ax.tick_params(colors='white')
        ax.legend()
        ax.grid(color='white', alpha=0.05)
        
        st.pyplot(fig)

    # Tabela z danymi na których się uczył
    with st.expander("🔍 Zobacz dane, na których uczył się model"):
        st.dataframe(df[['title', 'area', 'price']])

else:
    st.write("👈 Kliknij przycisk, aby nakarmić AI danymi.")
