import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Moje Nieruchomości", page_icon="🏠", layout="wide")

# --- 2. STYLIZACJA (DESIGN INSPIROWANY OTODOM) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Nunito Sans', sans-serif;
    }

    /* Tło ogólne */
    .stApp {
        background-color: #f4f6f9; /* Jasne tło, jak nowoczesne portale */
        color: #1a1a1a;
    }

    /* SEKCJA HERO (Nagłówek) */
    .hero-section {
        background: linear-gradient(135deg, #002f34 0%, #004d40 100%); /* Kolorystyka Otodom (ciemna zieleń/morski) */
        padding: 40px 20px;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin-bottom: 30px;
        color: white;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    
    .hero-title { font-size: 3rem; font-weight: 800; margin-bottom: 10px; }
    .hero-subtitle { font-size: 1.2rem; opacity: 0.9; font-weight: 300; }

    /* PASEK WYSZUKIWANIA (Biały box) */
    .search-container {
        background-color: white;
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        margin-top: -30px; /* Nachodzi na Hero */
        margin-bottom: 40px;
        border: 1px solid #e0e0e0;
    }

    /* KARTA OFERTY */
    .property-card {
        background-color: white;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #eaebed;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }

    .property-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        border-color: #00d2ad; /* Akcent zieleni */
    }

    .image-area {
        height: 200px;
        width: 100%;
        position: relative;
    }
    
    .card-img { width: 100%; height: 100%; object-fit: cover; }

    .card-details { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; justify-content: space-between; }

    .price { font-size: 22px; font-weight: 800; color: #002f34; margin-bottom: 5px; }
    .title { font-size: 14px; font-weight: 600; color: #444; margin-bottom: 15px; line-height: 1.4; height: 40px; overflow: hidden; }
    
    /* PARAMETRY (Metraż, Pokoje) */
    .params-row {
        display: flex;
        gap: 15px;
        font-size: 13px;
        color: #666;
        margin-bottom: 15px;
        border-top: 1px solid #f0f0f0;
        padding-top: 10px;
    }
    .param-item { display: flex; align-items: center; gap: 5px; }

    /* PRZYCISK */
    a.offer-btn {
        display: block;
        text-align: center;
        background-color: transparent;
        color: #002f34;
        border: 2px solid #002f34;
        padding: 10px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        transition: 0.3s;
    }
    a.offer-btn:hover {
        background-color: #002f34;
        color: white !important;
    }

    /* Ukrycie domyślnych elementów Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container { padding-top: 0; }
    
    /* Stylizacja inputów, żeby wyglądały pro */
    div[data-baseweb="input"] { border-radius: 8px; background-color: #f9f9f9; border: 1px solid #e0e0e0; }
</style>
""", unsafe_allow_html=True)

# --- 3. DANE (Twoje Linki) ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/mieszkanie-3-pok-balkon-garaz-komorka-lokatorska-ID4z4ja",
    "https://www.otodom.pl/pl/oferta/gotowe-do-odbioru-centrum-duzy-balkon-ID4z3Xy",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 4. ENGINE SCRAPUJĄCY (ZAAWANSOWANY) ---
@st.cache_data(ttl=3600) # Cache na 1h, żeby nie męczyć Otodom przy każdym kliknięciu filtra
def scrape_offers(links_list):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    results = []
    
    for url in links_list:
        offer_data = {
            "title": "Wczytywanie...", 
            "price": 0,
            "area": 0,
            "rooms": 0,
            "image_url": "https://via.placeholder.com/600x400?text=Brak+Zdjecia", 
            "link": url
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                
                # JSON Data
                script_data = soup.find("script", id="__NEXT_DATA__")
                if script_data:
                    try:
                        data = json.loads(script_data.string)
                        target = data['props']['pageProps']['ad']['target']
                        
                        # Podstawowe
                        offer_data["title"] = target.get('Title', 'Bez tytułu')
                        offer_data["price"] = float(target.get('Price', 0))
                        offer_data["area"] = float(target.get('Area', 0))
                        offer_data["rooms"] = int(target.get('Rooms_num', [0])[0]) if isinstance(target.get('Rooms_num'), list) else 0
                        
                        # Zdjęcie
                        images = data['props']['pageProps']['ad']['images']
                        if images: 
                            offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                    except: pass
        except: pass
        
        results.append(offer_data)
    
    return pd.DataFrame(results)

# --- 5. INTERFEJS ---

# A. Sekcja HERO (Nagłówek)
st.markdown("""
<div class="hero-section">
    <div class="hero-title">Adresujemy marzenia</div>
    <div class="hero-subtitle">Znajdź dom, który Ci odpowiada (z Twojej prywatnej listy)</div>
</div>
""", unsafe_allow_html=True)

# B. Pasek Wyszukiwania (Filtry)
st.markdown('<div class="search-container">', unsafe_allow_html=True) # Początek kontenera
st.write("### 🔍 Parametry wyszukiwania")

col1, col2, col3, col4 = st.columns(4)

with col1:
    max_price = st.number_input("Cena maksymalna (zł)", min_value=0, value=1500000, step=50000)

with col2:
    min_area = st.number_input("Metraż od (m²)", min_value=0, value=20, step=5)

with col3:
    min_rooms = st.number_input("Liczba pokoi (od)", min_value=1, value=1, step=1)

with col4:
    sort_by = st.selectbox("Sortuj według", ["Cena: rosnąco", "Cena: malejąco", "Metraż: malejąco"])

st.markdown('</div>', unsafe_allow_html=True) # Koniec kontenera


# --- 6. LOGIKA FILTROWANIA ---

# Pobieramy dane (z cache lub live)
df = scrape_offers(LINKS)

# Filtrowanie
filtered_df = df[
    (df['price'] <= max_price) & 
    (df['area'] >= min_area) & 
    (df['rooms'] >= min_rooms)
]

# Sortowanie
if sort_by == "Cena: rosnąco":
    filtered_df = filtered_df.sort_values(by='price', ascending=True)
elif sort_by == "Cena: malejąco":
    filtered_df = filtered_df.sort_values(by='price', ascending=False)
elif sort_by == "Metraż: malejąco":
    filtered_df = filtered_df.sort_values(by='area', ascending=False)

# --- 7. WYŚWIETLANIE WYNIKÓW (GRID) ---

st.write(f"Znaleziono **{len(filtered_df)}** ogłoszeń spełniających kryteria:")
st.write("")

if not filtered_df.empty:
    cols = st.columns(3)
    
    for index, row in filtered_df.iterrows():
        # Formatowanie ceny
        price_fmt = f"{row['price']:,.0f} zł".replace(",", " ")
        
        with cols[index % 3]:
            st.markdown(f"""
            <div class="property-card">
                <div class="image-area">
                    <img src="{row['image_url']}" class="card-img">
                </div>
                <div class="card-details">
                    <div>
                        <div class="price">{price_fmt}</div>
                        <div class="title">{row['title']}</div>
                        
                        <div class="params-row">
                            <div class="param-item">📏 {row['area']} m²</div>
                            <div class="param-item">🚪 {row['rooms']} pok.</div>
                        </div>
                    </div>
                    <a href="{row['link']}" target="_blank" class="offer-btn">ZOBACZ OFERTĘ</a>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.write("") # Odstęp w gridzie
else:
    st.warning("😔 Niestety, żadna z obserwowanych ofert nie spełnia tych kryteriów. Spróbuj zmienić filtry.")
