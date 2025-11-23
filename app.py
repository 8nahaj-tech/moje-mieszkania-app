import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- 1. KONFIGURACJA PRO (Ciemny motyw i układ) ---
st.set_page_config(page_title="Invest Monitor PRO", page_icon="🏢", layout="wide")

# --- 2. STYLIZACJA CSS (Dark Mode + Profesjonalny wygląd) ---
st.markdown("""
<style>
    /* Główne tło - elegancki ciemny granat */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        color: #ffffff;
    }
    
    /* Pasek postępu */
    .stProgress > div > div > div > div {
        background-color: #00d2ff;
    }

    /* Przycisk Główny */
    div.stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #00d2ff 0%, #3a7bd5 100%);
        border: none;
        color: white;
        padding: 16px;
        font-size: 20px;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 210, 255, 0.4);
        transition: transform 0.2s;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
    }
    
    /* Karta Oferty (Ramka) */
    .offer-card {
        background-color: rgba(255, 255, 255, 0.1); /* Półprzezroczyste tło */
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        margin-bottom: 20px;
    }

    /* Tytuł oferty */
    .offer-title {
        font-size: 22px;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 10px;
        line-height: 1.4;
    }

    /* Cena */
    .price-tag {
        font-size: 36px;
        font-weight: 800;
        color: #00d2ff;
        text-shadow: 0 0 10px rgba(0, 210, 255, 0.5);
        margin-bottom: 15px;
    }

    /* Przycisk linku */
    a.link-btn {
        display: inline-block;
        background-color: #ff416c;
        color: white !important;
        padding: 10px 25px;
        border-radius: 50px;
        text-decoration: none;
        font-weight: bold;
        font-size: 14px;
        box-shadow: 0 4px 10px rgba(255, 65, 108, 0.4);
    }
    a.link-btn:hover {
        background-color: #ff4b2b;
    }

    /* Zdjęcie */
    img {
        border-radius: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.5);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. TWOJE LINKI ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 4. FUNKCJA POBIERAJĄCA DANE ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    offer_data = {
        "title": "Ładowanie tytułu...",
        "price_str": "Brak ceny",
        "image_url": "https://via.placeholder.com/600x400?text=Brak+Zdjecia",
        "link": url
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # --- POPRAWKA: POBIERANIE TYTUŁU ---
            # 1. Szukamy głównego nagłówka H1 (to co widzi człowiek na stronie)
            h1_tag = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            
            if h1_tag:
                # Jeśli jest H1, bierzemy z niego czysty tekst
                offer_data["title"] = h1_tag.get_text().strip()
            else:
                # Fallback: Tytuł karty przeglądarki
                if soup.title:
                    offer_data["title"] = soup.title.string.replace(" - Otodom", "").strip()

            # --- POBIERANIE CENY I ZDJĘCIA (Z JSONa bo tam łatwiej) ---
            script_data = soup.find("script", id="__NEXT_DATA__")
            if script_data:
                try:
                    data = json.loads(script_data.string)
                    ad_target = data['props']['pageProps']['ad']['target']
                    
                    # Cena
                    raw_price = ad_target.get('Price', 0)
                    if isinstance(raw_price, (int, float)):
                        offer_data["price_str"] = f"{raw_price:,.0f} zł".replace(",", " ")
                    
                    # Zdjęcie
                    images = data['props']['pageProps']['ad']['images']
                    if images and len(images) > 0:
                        offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                except:
                    pass
    except:
        offer_data["title"] = "Błąd połączenia z ofertą"
        
    return offer_data

# --- 5. INTERFEJS ---
st.title("🏢 Invest Monitor PRO")
st.markdown("Poniżej znajdziesz aktualny status obserwowanych nieruchomości.")

if st.button("🚀 SKANUJ RYNEK"):
    
    st.write("") # Odstęp
    progress_bar = st.progress(0)
    
    for i, link in enumerate(LINKS):
        # Pobieramy dane
        data = get_offer_data(link)
        progress_bar.progress((i + 1) / len(LINKS))
        
        # Wyświetlamy kartę w HTML
        st.markdown(f"""
        <div class="offer-card">
            <div style="display: flex; flex-wrap: wrap; gap: 20px;">
                <div style="flex: 1; min-width: 300px;">
                    <img src="{data['image_url']}" style="width: 100%; height: auto; object-fit: cover;">
                </div>
                <div style="flex: 2; min-width: 300px;">
                    <div class="offer-title">{data['title']}</div>
                    <div class="price-tag">{data['price_str']}</div>
                    <div style="margin-top: 20px;">
                        <a href="{data['link']}" target="_blank" class="link-btn">👉 ZOBACZ NA OTODOM</a>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        time.sleep(0.5)

    progress_bar.empty()

else:
    st.info("System gotowy. Kliknij przycisk powyżej.")
