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
st.set_page_config(page_title="Nieruchomości PRO + AI", page_icon="🏠", layout="wide")

# --- 2. STYLIZACJA (CLEAN DESIGN) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Roboto', sans-serif; }
    .stApp { background-color: #f0f2f5; color: #1c1e21; }

    /* KARTA OFERTY */
    .property-card {
        background: white;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        overflow: hidden;
        border: 1px solid #e1e4e8;
        transition: transform 0.2s;
    }
    .property-card:hover { transform: translateY(-3px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); }

    /* GÓRA KARTY (ZDJĘCIE) */
    .card-top { position: relative; height: 200px; }
    .card-img { width: 100%; height: 100%; object-fit: cover; }
    .badge {
        position: absolute; top: 10px; left: 10px;
        background: #0078ff; color: white; padding: 4px 10px;
        border-radius: 4px; font-size: 11px; font-weight: bold; text-transform: uppercase;
    }

    /* TREŚĆ KARTY */
    .card-content { padding: 20px; }
    .price-row { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 10px; }
    .price { font-size: 24px; font-weight: 800; color: #1c1e21; }
    .title { font-size: 16px; font-weight: 600; color: #444; margin-bottom: 15px; line-height: 1.4; height: 45px; overflow: hidden; }

    /* AI OPIS */
    .ai-desc-box {
        background-color: #f0f8ff;
        border-left: 4px solid #0078ff;
        padding: 10px;
        margin-bottom: 15px;
        font-size: 13px;
        color: #333;
        font-style: italic;
    }

    /* HISTORIA CEN */
    .history-box {
        font-size: 11px;
        color: #666;
        border-top: 1px solid #eee;
        padding-top: 10px;
        margin-top: 10px;
    }

    /* PARAMETRY */
    .params { display: flex; gap: 15px; font-size: 13px; color: #666; margin-bottom: 15px; }

    /* PRZYCISK */
    a.offer-btn {
        display: block; width: 100%; text-align: center;
        background-color: #0078ff; color: white !important;
        padding: 10px; border-radius: 6px; text-decoration: none; font-weight: bold;
        transition: background 0.2s;
    }
    a.offer-btn:hover { background-color: #005bb5; }

    /* Ukrycie menu */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
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

# --- 4. FUNKCJA GENERUJĄCA OPIS AI (SYMULACJA) ---
def generate_ai_description(title, price, area, rooms):
    if area == 0: return "🤖 AI: Brak danych do analizy."
    
    price_per_m = price / area if area > 0 else 0
    desc = "🤖 **AI Podsumowanie:** "
    
    if rooms == 1: desc += "Kompaktowa kawalerka, "
    elif rooms == 2: desc += "Funkcjonalne 2 pokoje, "
    elif rooms > 3: desc += "Przestronny apartament dla rodziny, "
    else: desc += "Mieszkanie, "
    
    desc += f"oferujące {area} m². "
    
    if price_per_m > 15000: desc += "Nieruchomość w standardzie premium. "
    elif price_per_m < 9000: desc += "Atrakcyjna cena za metr kwadratowy! "
    
    desc += "Idealne pod inwestycję lub do zamieszkania."
    return desc

# --- 5. OBSŁUGA PLIKU HISTORII ---
HISTORY_FILE = 'historia_cen.csv'

def load_history():
    if os.path.exists(HISTORY_FILE):
        return pd.read_csv(HISTORY_FILE)
    return pd.DataFrame(columns=["Data", "Link", "Cena"])

def save_to_history(link, price):
    df = load_history()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Sprawdzamy czy wpis z dzisiaj już jest
    check = df[(df['Link'] == link) & (df['Data'] == today)]
    
    if check.empty and price > 0:
        new_row = pd.DataFrame([{"Data": today, "Link": link, "Cena": price}])
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(HISTORY_FILE, index=False)

def get_price_history_for_link(link):
    df = load_history()
    if df.empty: return []
    history = df[df['Link'] == link].sort_values(by="Data", ascending=False).head(3) # Ostatnie 3 wpisy
    return history.to_dict('records')

# --- 6. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data_out = {
        "title": "Wczytywanie...", "price": 0, "price_str": "---", 
        "area": 0, "rooms": 0, "img": "https://via.placeholder.com/600x400?text=Brak", 
        "link": url
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            
            # 1. Tytuł - Próba pobrania czystego tekstu z H1
            h1 = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1:
                data_out["title"] = h1.get_text().strip()
            else:
                # Jeśli H1 nie działa, sprawdzamy czy tytuł nie jest zakodowany Base64
                # (To naprawia ten problem z "Tm93...")
                raw_title = soup.title.string if soup.title else ""
                if " " not in raw_title and len(raw_title) > 20:
                    try:
                        decoded = base64.b64decode(raw_title).decode('utf-8')
                        data_out["title"] = decoded
                    except:
                        data_out["title"] = "Oferta Otodom"
            
            # 2. JSON
            script = soup.find("script", id="__NEXT_DATA__")
            if script:
                j = json.loads(script.string)
                target = j['props']['pageProps']['ad']['target']
                
                data_out["price"] = float(target.get('Price', 0))
                data_out["price_str"] = f"{data_out['price']:,.0f} zł".replace(",", " ")
                data_out["area"] = float(target.get('Area', 0))
                
                rooms = target.get('Rooms_num', [0])
                if isinstance(rooms, list): data_out["rooms"] = int(rooms[0])
                
                imgs = j['props']['pageProps']['ad']['images']
                if imgs: data_out["img"] = imgs[0].get('medium')
                
                # Zapisz do historii
                save_to_history(url, data_out["price"])
                
    except Exception as e:
        print(e)
        
    return data_out

# --- 7. INTERFEJS ---
st.title("🏠 Twoje Centrum Nieruchomości")

if st.button("🔄 AKTUALIZUJ CENY I HISTORIĘ"):
    
    # Progress bar
    bar = st.progress(0)
    
    # Grid 3 kolumny
    cols = st.columns(3)
    
    for i, link in enumerate(LINKS):
        bar.progress((i + 1) / len(LINKS))
        
        # Pobierz dane
        d = get_data(link)
        
        # Generuj AI opis
        ai_text = generate_ai_description(d['title'], d['price'], d['area'], d['rooms'])
        
        # Pobierz historię
        hist = get_price_history_for_link(link)
        hist_html = ""
        for h in hist:
            hist_html += f"<div>📅 {h['Data']}: <b>{h['Cena']:,.0f} zł</b></div>"
        
        # Renderuj kartę (Bezpieczny HTML)
        with cols[i % 3]:
            st.markdown(f"""
            <div class="property-card">
                <div class="card-top">
                    <div class="badge">NA SPRZEDAŻ</div>
                    <img src="{d['img']}" class="card-img">
                </div>
                <div class="card-content">
                    <div class="price-row">
                        <div class="price">{d['price_str']}</div>
                    </div>
                    <div class="title">{d['title']}</div>
                    
                    <div class="params">
                        <span>📏 {d['area']} m²</span>
                        <span>🚪 {d['rooms']} pok.</span>
                    </div>

                    <div class="ai-desc-box">
                        {ai_text}
                    </div>

                    <a href="{d['link']}" target="_blank" class="offer-btn">ZOBACZ OFERTĘ</a>

                    <div class="history-box">
                        <strong>📜 Historia cen:</strong>
                        {hist_html if hist_html else "Brak historii (pierwsze sprawdzenie)"}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    bar.empty()
    st.success("Dane zaktualizowane!")
else:
    st.info("Kliknij przycisk powyżej, aby pobrać najnowsze dane i zapisać historię.")

# Pokaż link do pobrania pliku historii
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "rb") as f:
        st.download_button("💾 Pobierz pełną historię (Excel/CSV)", f, file_name="historia_cen.csv")
