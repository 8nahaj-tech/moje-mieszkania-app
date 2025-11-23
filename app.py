import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import os
from datetime import datetime
from sklearn.linear_model import LinearRegression
import numpy as np

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Estate Monitor AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    
    /* Karta Oferty */
    .property-card {
        background: #1f2937; border-radius: 12px; border: 1px solid #374151;
        overflow: hidden; margin-bottom: 20px;
    }
    .card-img { width: 100%; height: 180px; object-fit: cover; }
    .card-body { padding: 15px; }
    .price { font-size: 20px; font-weight: bold; color: #fff; }
    .title { font-size: 13px; color: #9ca3af; margin-bottom: 10px; height: 40px; overflow: hidden; }
    .metrics { display: flex; gap: 10px; font-size: 12px; color: #60a5fa; margin-bottom: 10px;}
    
    /* Sekcja AI */
    .ai-section {
        background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
        padding: 20px; border-radius: 15px; margin-top: 30px; border: 1px solid #3b82f6;
    }
    .ai-result { font-size: 30px; font-weight: 800; color: #60a5fa; }
</style>
""", unsafe_allow_html=True)

# --- 2. LINKI ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 3. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"title": "...", "price": 0, "area": 0, "img": None, "link": url}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            h1 = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1: data["title"] = h1.get_text().strip()
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

# --- 4. MODEL AI (Regresja Liniowa) ---
def train_and_predict(dataset, user_area):
    # Filtrujemy dane (tylko te co mają cenę i metraż > 0)
    valid_data = [d for d in dataset if d['price'] > 0 and d['area'] > 0]
    
    if len(valid_data) < 2:
        return None, "Za mało danych do nauki AI (minimum 2 oferty)."

    # Przygotowanie danych dla modelu
    # X = Metraż (cecha), y = Cena (cel)
    X = np.array([d['area'] for d in valid_data]).reshape(-1, 1)
    y = np.array([d['price'] for d in valid_data])

    # TRENING MODELU
    model = LinearRegression()
    model.fit(X, y)

    # PREDUKCJA
    prediction = model.predict(np.array([[user_area]]))[0]
    
    return model, prediction

# --- 5. INTERFEJS ---
st.title("🤖 Estate Monitor AI")
st.caption("Pobieram dane -> Uczę maszynę -> Przewiduję ceny")

if st.button("🚀 URUCHOM SYSTEM", type="primary"):
    
    # 1. POBIERANIE DANYCH
    progress = st.progress(0)
    dataset = []
    
    cols = st.columns(len(LINKS)) # Miniaturki na górze
    
    for i, link in enumerate(LINKS):
        progress.progress((i + 1) / len(LINKS))
        d = get_data(link)
        dataset.append(d)
        
        # Wyświetlanie miniaturek ofert
        with cols[i]:
            if d['img']: st.image(d['img'], use_container_width=True)
            st.caption(f"{d['price']:,.0f} zł | {d['area']} m²")
            
    progress.empty()

    # 2. SEKCJA AI
    st.markdown("---")
    st.markdown("### 🔮 AI Predyktor Cen")
    
    # Suwak dla użytkownika
    col_ai_1, col_ai_2 = st.columns([1, 2])
    
    with col_ai_1:
        user_area = st.slider("Wybierz metraż do wyceny (m²):", 20, 120, 50)
        
        # Uruchamiamy AI
        model, predicted_price = train_and_predict(dataset, user_area)
        
        if model:
            st.markdown(f"""
            <div class="ai-section">
                <div>Szacowana wartość dla <b>{user_area} m²</b>:</div>
                <div class="ai-result">{predicted_price:,.0f} zł</div>
                <div style="font-size:12px; margin-top:5px">Model nauczył się na podstawie {len(dataset)} Twoich ofert.</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error(predicted_price)

    # 3. WYKRES (WIZUALIZACJA LOGIKI AI)
    with col_ai_2:
        if model:
            # Tworzymy dane do wykresu
            df = pd.DataFrame(dataset)
            df = df[df['area'] > 0] # Tylko poprawne dane
            
            # Dodajemy punkt predykcji (czerwony)
            st.write("📈 **Jak myśli AI? (Niebieskie = Twoje oferty, Czerwony = Predykcja)**")
            
            # Prosty wykres punktowy
            chart_data = df[['area', 'price']]
            
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(8, 4))
            # Tło wykresu
            fig.patch.set_facecolor('#0e1117')
            ax.set_facecolor('#1f2937')
            
            # Punkty danych (Oferty)
            ax.scatter(df['area'], df['price'], color='#60a5fa', s=100, label='Znalezione Oferty')
            
            # Linia trendu (To co AI wyliczyło)
            line_x = np.linspace(df['area'].min(), df['area'].max(), 100).reshape(-1, 1)
            line_y = model.predict(line_x)
            ax.plot(line_x, line_y, color='white', linestyle='--', alpha=0.5, label='Trend AI')
            
            # Punkt predykcji (Wynik)
            ax.scatter([user_area], [predicted_price], color='#ef4444', s=200, zorder=5, label='Twoja Wycena')
            
            # Stylizacja
            ax.tick_params(colors='white')
            ax.spines['bottom'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.set_xlabel('Metraż (m²)', color='white')
            ax.set_ylabel('Cena (PLN)', color='white')
            ax.legend()
            
            st.pyplot(fig)

else:
    st.info("Kliknij przycisk, aby pobrać dane i wytrenować model.")
