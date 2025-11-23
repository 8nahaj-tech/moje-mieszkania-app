import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- 1. KONFIGURACJA PRO ---
st.set_page_config(page_title="Wrocław Estate Center", page_icon="🏙️", layout="wide")

# --- 2. STYLIZACJA (TABS + DARK MODE) ---
st.markdown("""
<style>
    /* Tło */
    .stApp {
        background: linear-gradient(135deg, #141E30 0%, #243B55 100%);
        color: white;
    }
    
    /* Stylizacja Zakładek */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: rgba(255,255,255,0.05);
        border-radius: 10px 10px 0 0;
        color: white;
        font-weight: bold;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00d2ff !important;
        color: black !important;
    }

    /* Karta Oferty */
    .offer-card {
        background-color: rgba(0, 0, 0, 0.3);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* Teksty */
    .offer-title { font-size: 20px; font-weight: 600; color: #f0f0f0; margin-bottom: 10px; }
    .price-tag { font-size: 32px; font-weight: 800; color: #00d2ff; text-shadow: 0 0 10px rgba(0, 210, 255, 0.3); }
    
    /* Przycisk linku */
    a.link-btn {
        display: inline-block;
        background-color: #ff416c;
        color: white !important;
        padding: 8px 20px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: 0.3s;
    }
    a.link-btn:hover { background-color: #ff4b2b; transform: scale(1.05); }

    /* Zdjęcie */
    img { border-radius: 10px; object-fit: cover; }
    
    /* Przycisk Skanuj */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #1CB5E0 0%, #000851 100%);
        border: none;
        color: white;
        padding: 15px;
        font-weight: bold;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. BAZA DANYCH LINKÓW (TUTAJ DODAJESZ NOWE) ---

# Zakładka 1: Twoje ulubione
LINKS_MOJE = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8"
]

# Zakładka 2: Mieszkania (Przykładowe z Wrocławia)
LINKS_MIESZKANIA = [
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a" # Przykładowy
]

# Zakładka 3: Kawalerki
LINKS_KAWALERKI = [
    "https://www.otodom.pl/pl/oferta/gotowe-do-odbioru-centrum-duzy-balkon-ID4z3Xy", # Przykładowy
]

# Zakładka 4: Domy
LINKS_DOMY = [
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2",
]


# --- 4. FUNKCJA POBIERANIA DANYCH ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    offer_data = {
        "title": "Ładowanie...", "price_str": "Brak ceny",
        "image_url": "https://via.placeholder.com/600x400?text=Brak+Zdjecia", "link": url
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Pobieranie tytułu (H1)
            h1_tag = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1_tag: offer_data["title"] = h1_tag.get_text().strip()
            
            # Pobieranie JSON
            script_data = soup.find("script", id="__NEXT_DATA__")
            if script_data:
                try:
                    data = json.loads(script_data.string)
                    ad_target = data['props']['pageProps']['ad']['target']
                    
                    raw_price = ad_target.get('Price', 0)
                    if isinstance(raw_price, (int, float)):
                        offer_data["price_str"] = f"{raw_price:,.0f} zł".replace(",", " ")
                    
                    images = data['props']['pageProps']['ad']['images']
                    if images: offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                except: pass
    except: pass
    return offer_data

# --- 5. FUNKCJA WYŚWIETLAJĄCA ZAKŁADKĘ ---
def render_tab(links_list, tab_name):
    if not links_list:
        st.info(f"Brak linków w kategorii: {tab_name}")
        return

    if st.button(f"🔄 SKANUJ KATEGORIĘ: {tab_name.upper()}", key=tab_name):
        progress_bar = st.progress(0)
        
        for i, link in enumerate(links_list):
            data = get_offer_data(link)
            progress_bar.progress((i + 1) / len(links_list))
            
            st.markdown(f"""
            <div class="offer-card">
                <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center;">
                    <div style="flex: 1; min-width: 250px;">
                        <img src="{data['image_url']}" style="width: 100%; height: 200px; object-fit: cover; border-radius: 10px;">
                    </div>
                    <div style="flex: 2; min-width: 250px;">
                        <div class="offer-title">{data['title']}</div>
                        <div class="price-tag">{data['price_str']}</div>
                        <div style="margin-top: 15px;">
                            <a href="{data['link']}" target="_blank" class="link-btn">👉 PRZEJDŹ DO OFERTY</a>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            time.sleep(0.3) # Mała pauza
            
        progress_bar.empty()
    else:
        st.write(f"Kliknij przycisk powyżej, aby sprawdzić ceny dla **{len(links_list)} ofert**.")

# --- 6. GŁÓWNY INTERFEJS ---
st.title("🏙️ Wrocław Estate Center")

# Definiujemy zakładki
tab1, tab2, tab3, tab4 = st.tabs(["⭐ MOJE WYBRANE", "🏢 MIESZKANIA", "🛋️ KAWALERKI", "🏡 DOMY"])

with tab1:
    st.header("Moje Ulubione")
    render_tab(LINKS_MOJE, "moje")

with tab2:
    st.header("Ciekawe Mieszkania (Wrocław)")
    st.markdown("[🔍 Szukaj nowych mieszkań na Otodom (Wrocław)](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw?viewType=listing)")
    render_tab(LINKS_MIESZKANIA, "mieszkania")

with tab3:
    st.header("Kawalerki pod wynajem/start")
    st.markdown("[🔍 Szukaj kawalerek (do 35m²)](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw?areaMax=35&viewType=listing)")
    render_tab(LINKS_KAWALERKI, "kawalerki")

with tab4:
    st.header("Domy i Szeregowce")
    st.markdown("[🔍 Szukaj domów we Wrocławiu](https://www.otodom.pl/pl/wyniki/sprzedaz/dom/dolnoslaskie/wroclaw/wroclaw/wroclaw?viewType=listing)")
    render_tab(LINKS_DOMY, "domy")
