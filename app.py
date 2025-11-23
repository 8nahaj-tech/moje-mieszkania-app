import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wrocław Estate Center", page_icon="🏙️", layout="wide")

# --- 2. STYLIZACJA CSS (GRID OTODOM + ANIMACJE) ---
st.markdown("""
<style>
    /* Tło aplikacji */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: white;
    }

    /* UKŁAD KARTY (Jak na Otodom) */
    .property-card {
        background-color: white;
        border-radius: 12px;
        overflow: hidden; /* Żeby zdjęcie nie wystawało */
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        margin-bottom: 20px;
        height: 100%;
        position: relative;
    }
    
    .property-card:hover {
        transform: translateY(-10px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.5);
    }

    /* ZDJĘCIE W KARCIE */
    .card-image-container {
        position: relative;
        width: 100%;
        height: 200px;
    }
    
    .card-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }

    /* BADGE "NA SPRZEDAŻ" */
    .badge {
        position: absolute;
        top: 10px;
        left: 10px;
        background-color: #00d2ff;
        color: black;
        padding: 5px 10px;
        font-size: 10px;
        font-weight: bold;
        border-radius: 4px;
        text-transform: uppercase;
        z-index: 10;
    }

    /* TREŚĆ KARTY (Dół) */
    .card-content {
        padding: 15px;
        color: #333; /* Ciemny tekst na białym tle */
    }

    .card-price {
        font-size: 24px;
        font-weight: 800;
        color: #2c3e50;
        margin-bottom: 5px;
    }

    .card-title {
        font-size: 14px;
        font-weight: 500;
        color: #666;
        line-height: 1.4;
        height: 40px; /* Stała wysokość na 2 linie tekstu */
        overflow: hidden;
        margin-bottom: 15px;
    }

    /* PRZYCISK W KARCIE */
    a.card-btn {
        display: block;
        text-align: center;
        background-color: #2c3e50;
        color: white !important;
        padding: 10px;
        border-radius: 6px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        transition: 0.2s;
    }
    a.card-btn:hover {
        background-color: #00d2ff;
        color: black !important;
    }

    /* --- ANIMACJA MAGA-ASYSTENTA --- */
    @keyframes guide-sequence {
        0%   { left: 2%;  top: 110px; transform: scale(1) rotate(0deg); }
        25%  { left: 45%; top: 200px; transform: scale(1) rotate(10deg); }
        35%  { left: 45%; top: 200px; transform: scale(1.4) rotate(0deg); filter: drop-shadow(0 0 35px rgba(255, 215, 0, 1)); }
        40%  { left: 45%; top: 200px; transform: scale(1) rotate(0deg); }
        55%  { left: 15%; top: 500px; transform: scale(1) rotate(-10deg); }
        65%  { left: 15%; top: 500px; transform: scale(1.2) rotate(0deg); }
        70%  { left: 15%; top: 500px; transform: scale(1.3) rotate(360deg); filter: drop-shadow(0 0 30px rgba(50, 255, 50, 1)); }
        100% { left: 120%; top: 300px; transform: scale(1) rotate(20deg); }
    }

    .harry-potter {
        position: fixed;
        z-index: 99999;
        width: 110px;
        animation: guide-sequence 25s ease-in-out infinite;
        pointer-events: none;
    }

    /* Stylizacja Zakładek Streamlit */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; background-color: rgba(255,255,255,0.1);
        border-radius: 8px 8px 0 0; color: white; border: none;
    }
    .stTabs [aria-selected="true"] { background-color: #00d2ff !important; color: black !important; }
    
    /* Ukrywamy standardowe marginesy Streamlit */
    .block-container { padding-top: 2rem; }
    
    /* Przycisk Skanuj */
    div.stButton > button {
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        color: white; border: none; padding: 12px; font-weight: bold; border-radius: 8px;
        text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. WSTAWIENIE MAGA ---
st.markdown("""
<img src="https://raw.githubusercontent.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis/master/Emojis/People/Mage.png" class="harry-potter">
""", unsafe_allow_html=True)

# --- 4. BAZA DANYCH ---
LINKS_MOJE = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8"
]
LINKS_MIESZKANIA = [
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/mieszkanie-3-pok-balkon-garaz-komorka-lokatorska-ID4z4ja" # Dodatkowy przykład
]
LINKS_KAWALERKI = [
    "https://www.otodom.pl/pl/oferta/gotowe-do-odbioru-centrum-duzy-balkon-ID4z3Xy",
]
LINKS_DOMY = [
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2",
]


# --- 5. FUNKCJA POBIERANIA DANYCH ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    offer_data = {"title": "Ładowanie oferty...", "price_str": "Brak ceny", "image_url": "https://via.placeholder.com/600x400?text=Brak+Zdjecia", "link": url}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            h1_tag = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1_tag: offer_data["title"] = h1_tag.get_text().strip()
            script_data = soup.find("script", id="__NEXT_DATA__")
            if script_data:
                try:
                    data = json.loads(script_data.string)
                    ad_target = data['props']['pageProps']['ad']['target']
                    raw_price = ad_target.get('Price', 0)
                    if isinstance(raw_price, (int, float)): 
                        offer_data["price_str"] = f"{raw_price:,.0f} zł".replace(",", " ")
                    images = data['props']['pageProps']['ad']['images']
                    if images: 
                        offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                except: pass
    except: pass
    return offer_data

# --- 6. FUNKCJA RENDEROWANIA SIATKI (GRID) ---
def render_grid(links_list, tab_name):
    if not links_list:
        st.info("Brak ofert w tej kategorii.")
        return

    if st.button(f"🔎 SKANUJ: {tab_name.upper()}", key=tab_name):
        progress_bar = st.progress(0)
        
        # Pobieramy dane dla wszystkich linków
        results = []
        for i, link in enumerate(links_list):
            results.append(get_offer_data(link))
            progress_bar.progress((i + 1) / len(links_list))
            time.sleep(0.2)
        
        progress_bar.empty()
        
        # --- RYSOWANIE SIATKI (3 KOLUMNY) ---
        cols = st.columns(3) # Tworzymy 3 kolumny
        
        for i, data in enumerate(results):
            # Wybieramy odpowiednią kolumnę (0, 1 lub 2)
            with cols[i % 3]:
                st.markdown(f"""
                <div class="property-card">
                    <div class="card-image-container">
                        <div class="badge">NA SPRZEDAŻ</div>
                        <img src="{data['image_url']}" class="card-image">
                    </div>
                    <div class="card-content">
                        <div class="card-price">{data['price_str']}</div>
                        <div class="card-title">{data['title']}</div>
                        <a href="{data['link']}" target="_blank" class="card-btn">ZOBACZ OFERTĘ</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    else:
        st.markdown(f"**Gotowy do pobrania {len(links_list)} ofert.** Kliknij przycisk powyżej.")

# --- 7. GŁÓWNY INTERFEJS ---
st.title("🏙️ Wrocław Estate Center")
st.markdown("Profesjonalny monitoring rynku nieruchomości.")

tab1, tab2, tab3, tab4 = st.tabs(["⭐ MOJE WYBRANE", "🏢 MIESZKANIA", "🛋️ KAWALERKI", "🏡 DOMY"])

with tab1:
    st.header("Twoja Lista Życzeń")
    render_grid(LINKS_MOJE, "moje")

with tab2:
    st.header("Mieszkania: Wrocław")
    st.markdown("[Wszystkie mieszkania na Otodom](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw)")
    render_grid(LINKS_MIESZKANIA, "mieszkania")

with tab3:
    st.header("Kawalerki (Inwestycyjne)")
    render_grid(LINKS_KAWALERKI, "kawalerki")

with tab4:
    st.header("Domy i Szeregowce")
    render_grid(LINKS_DOMY, "domy")
