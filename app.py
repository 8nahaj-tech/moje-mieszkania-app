import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import base64
from datetime import datetime
import os

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Estate Monitor PRO", page_icon="🏠", layout="wide")

# --- 2. STYLIZACJA CSS (NAPRAWIONA) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #f3f4f6; color: #1f2937; }

    /* KARTA OFERTY */
    .property-card {
        background: white;
        border-radius: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
        transition: transform 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .property-card:hover { transform: translateY(-5px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }

    /* ZDJĘCIE */
    .card-img-container { position: relative; height: 200px; width: 100%; }
    .card-img { width: 100%; height: 100%; object-fit: cover; }
    .badge {
        position: absolute; top: 12px; left: 12px;
        background: #2563eb; color: white; padding: 4px 12px;
        border-radius: 20px; font-size: 10px; font-weight: 800; text-transform: uppercase;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }

    /* TREŚĆ */
    .card-content { padding: 20px; flex-grow: 1; display: flex; flex-direction: column; }
    
    .price { font-size: 24px; font-weight: 800; color: #111827; margin-bottom: 8px; }
    
    .title { 
        font-size: 15px; font-weight: 500; color: #4b5563; 
        margin-bottom: 16px; line-height: 1.4; 
        height: 42px; overflow: hidden; /* Ograniczenie do 2 linii */
        display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
    }

    /* PARAMETRY */
    .params-grid {
        display: flex; gap: 15px; margin-bottom: 16px;
        padding-bottom: 16px; border-bottom: 1px solid #f3f4f6;
    }
    .param-item { font-size: 13px; color: #6b7280; font-weight: 600; display: flex; align-items: center; gap: 6px; }

    /* AI OPIS */
    .ai-box {
        background-color: #eff6ff; border-radius: 8px; padding: 12px;
        margin-bottom: 16px; font-size: 12px; color: #1e40af; line-height: 1.5;
    }

    /* PRZYCISK */
    a.btn-link {
        display: block; width: 100%; text-align: center;
        background-color: #111827; color: white !important;
        padding: 12px; border-radius: 8px; text-decoration: none; font-weight: 600; font-size: 14px;
        margin-top: auto; transition: background 0.2s;
    }
    a.btn-link:hover { background-color: #2563eb; }

    /* HISTORIA */
    .history-section {
        margin-top: 15px; font-size: 11px; color: #9ca3af;
    }
    .history-row { display: flex; justify-content: space-between; margin-top: 4px; }
    
    /* Ukrycie menu */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    .block-container { padding-top: 2rem; }
</style>
""", unsafe_allow_html=True)

# --- 3. DANE LINKÓW ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 4. SYSTEM HISTORII ---
HISTORY_FILE = 'historia_cen.csv'

def init_history():
    if not os.path.exists(HISTORY_FILE):
        df = pd.DataFrame(columns=["Data", "Link", "Cena"])
        df.to_csv(HISTORY_FILE, index=False)

def save_price(link, price):
    if price == 0: return
    init_history()
    df = pd.read_csv(HISTORY_FILE)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Sprawdzamy czy już dziś zapisaliśmy tę cenę dla tego linku
    exists = df[(df['Link'] == link) & (df['Data'] == today)]
    
    if exists.empty:
        new_row = pd.DataFrame([{"Data": today, "Link": link, "Cena": price}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)

def get_history_html(link):
    init_history()
    df = pd.read_csv(HISTORY_FILE)
    
    # Filtrujemy po linku i sortujemy od najnowszej
    hist = df[df['Link'] == link].sort_values(by="Data", ascending=False).head(5)
    
    if hist.empty:
        return "<div class='history-row'>Brak historii</div>"
    
    html = ""
    for _, row in hist.iterrows():
        cena_fmt = f"{row['Cena']:,.0f} zł".replace(",", " ")
        html += f"<div class='history-row'><span>📅 {row['Data']}</span> <span><b>{cena_fmt}</b></span></div>"
    return html

# --- 5. AI OPIS GENERATOR ---
def generate_ai_text(title, price, area, rooms):
    if area == 0: return "Analiza danych niedostępna."
    
    sqm_price = price / area
    desc = f"✨ **Analiza:** Mieszkanie {rooms}-pokojowe ({area} m²). "
    
    if sqm_price > 14000: desc += "Standard Premium/Centrum. "
    elif sqm_price < 9000: desc += "Okazja cenowa (poniżej średniej). "
    else: desc += "Cena rynkowa standardowa. "
    
    if rooms == 1: desc += "Idealne na start."
    elif rooms >= 4: desc += "Duży potencjał dla rodziny."
    
    return desc

# --- 6. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    data = {
        "title": "Wczytywanie...", "price": 0, "price_str": "---", 
        "area": 0, "rooms": 0, "img": "https://via.placeholder.com/600x400?text=Brak+Zdjecia", 
        "link": url
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            
            # Tytuł (czyszczenie Base64 i H1)
            h1 = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1: data["title"] = h1.get_text().strip()
            
            # JSON Data
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
                
                # Zapisujemy do historii
                save_price(url, data["price"])
    except: pass
    return data

# --- 7. INTERFEJS GŁÓWNY ---
st.title("Estate Monitor PRO")
st.markdown("### 📊 Panel Inwestycyjny")

if st.button("🔄 POBIERZ AKTUALNE CENY"):
    st.divider()
    bar = st.progress(0)
    cols = st.columns(3) # Grid 3 kolumny
    
    for i, link in enumerate(LINKS):
        bar.progress((i + 1) / len(LINKS))
        d = get_data(link)
        ai_desc = generate_ai_text(d['title'], d['price'], d['area'], d['rooms'])
        history_html = get_history_html(link)
        
        # Renderowanie karty (Fix HTML)
        with cols[i % 3]:
            st.markdown(f"""
            <div class="property-card">
                <div class="card-img-container">
                    <div class="badge">NA SPRZEDAŻ</div>
                    <img src="{d['img']}" class="card-img">
                </div>
                <div class="card-content">
                    <div class="price">{d['price_str']}</div>
                    <div class="title">{d['title']}</div>
                    
                    <div class="params-grid">
                        <div class="param-item">📏 {d['area']} m²</div>
                        <div class="param-item">🚪 {d['rooms']} pok.</div>
                    </div>
                    
                    <div class="ai-box">{ai_desc}</div>
                    
                    <a href="{d['link']}" target="_blank" class="btn-link">ZOBACZ OFERTĘ</a>
                    
                    <div class="history-section">
                        <strong>📜 Ostatnie odczyty cen:</strong>
                        {history_html}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    bar.empty()
    
    # Przycisk pobierania historii
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "rb") as f:
            st.download_button("💾 Pobierz historię (CSV)", f, "historia_cen.csv")
            
else:
    st.info("Kliknij przycisk powyżej, aby zeskanować rynek.")
