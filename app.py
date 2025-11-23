import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd

# --- 1. KONFIGURACJA STRONY (Musi być na samej górze) ---
st.set_page_config(page_title="Pro Estate Monitor", page_icon="🏢", layout="wide")

# --- 2. STYLIZACJA CSS (To tutaj dzieje się magia wyglądu) ---
st.markdown("""
<style>
    /* Tło całej aplikacji - profesjonalny ciemny gradient */
    .stApp {
        background: linear-gradient(to bottom right, #0f2027, #203a43, #2c5364);
        color: white;
    }
    
    /* Stylizacja przycisku głównego */
    div.stButton > button {
        width: 100%;
        background-color: #00d2ff; 
        color: #000000;
        font-weight: bold;
        border: none;
        padding: 15px;
        font-size: 18px;
        transition: 0.3s;
        border-radius: 10px;
    }
    div.stButton > button:hover {
        background-color: #3a7bd5;
        color: white;
    }

    /* Stylizacja linku jako guzika */
    a.custom-button {
        display: inline-block;
        padding: 10px 20px;
        background-color: #FF416C;
        color: white !important;
        text-decoration: none;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    a.custom-button:hover {
        background-color: #FF4B2B;
    }

    /* Wygląd ceny */
    .price-tag {
        font-size: 32px;
        font-weight: 800;
        color: #00d2ff; /* Jasny błękit */
        margin-bottom: 5px;
    }
    
    /* Wygląd tytułu */
    .offer-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 5px;
        color: #f0f0f0;
    }

    /* Ramka wokół zdjęcia */
    img {
        border-radius: 12px;
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
        "title": "Nieznana oferta",
        "price_str": "Brak ceny",
        "image_url": "https://via.placeholder.com/400x300?text=Brak+Zdjecia", # Zaślepka jak nie ma fotki
        "link": url
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            script_data = soup.find("script", id="__NEXT_DATA__")
            
            if script_data:
                data = json.loads(script_data.string)
                ad_target = data['props']['pageProps']['ad']['target']
                
                # Tytuł i Cena
                offer_data["title"] = ad_target.get('Title', 'Tytuł niedostępny')
                raw_price = ad_target.get('Price', 0)
                
                if isinstance(raw_price, (int, float)):
                    offer_data["price_str"] = f"{raw_price:,.0f} zł".replace(",", " ")
                
                # Zdjęcie
                try:
                    images = data['props']['pageProps']['ad']['images']
                    if images and len(images) > 0:
                        offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                except:
                    pass
    except:
        pass
        
    return offer_data

# --- 5. GŁÓWNY INTERFEJS ---

st.title("🏢 Pro Estate Monitor")
st.markdown("### 🔍 Panel śledzenia inwestycji")
st.write("Kliknij przycisk poniżej, aby zeskanować rynek.")

if st.button("🚀 SKANUJ OFERTY (START)"):
    
    st.divider()
    progress_bar = st.progress(0)
    
    for i, link in enumerate(LINKS):
        # Pobieranie danych
        data = get_offer_data(link)
        progress_bar.progress((i + 1) / len(LINKS))
        
        # --- UKŁAD WYŚWIETLANIA (KARTA) ---
        with st.container():
            col1, col2 = st.columns([1, 2], gap="large")
            
            # Kolumna ze zdjęciem
            with col1:
                st.image(data["image_url"], use_container_width=True)
            
            # Kolumna z tekstem (używamy HTML dla ładnego wyglądu)
            with col2:
                st.markdown(f"""
                <div class="offer-title">{data['title']}</div>
                <div class="price-tag">{data['price_str']}</div>
                <br>
                <a href="{data['link']}" target="_blank" class="custom-button">👉 Zobacz ofertę na Otodom</a>
                """, unsafe_allow_html=True)
        
        st.divider() # Linia oddzielająca
        time.sleep(0.5)

    progress_bar.empty()
    st.success("✅ Skanowanie zakończone pomyślnie.")

else:
    st.info("Oczekiwanie na uruchomienie skanera...")
