import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- 1. KONFIGURACJA STRONY (PREMIUM) ---
st.set_page_config(page_title="Estate Monitor Pro", page_icon="🏢", layout="wide")

# --- 2. STYLIZACJA CSS (BUSINESS DARK MODE) ---
st.markdown("""
<style>
    /* Import czcionki (opcjonalnie systemowej, dla szybkości używamy sans-serif) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Główne tło aplikacji - Głęboki, profesjonalny granat/czarny */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }

    /* KARTA OFERTY */
    .property-card {
        background-color: #1f2937; /* Ciemnoszary, lżejszy od tła */
        border: 1px solid #374151;
        border-radius: 12px;
        overflow: hidden;
        transition: all 0.3s ease;
        margin-bottom: 24px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        display: flex;
        flex-direction: column;
        height: 100%;
    }

    .property-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.6);
        border-color: #60a5fa; /* Niebieski akcent przy najechaniu */
    }

    /* KONTENER ZDJĘCIA */
    .image-wrapper {
        position: relative;
        height: 220px;
        width: 100%;
        overflow: hidden;
    }

    .card-img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        transition: transform 0.5s ease;
    }

    .property-card:hover .card-img {
        transform: scale(1.05); /* Lekki zoom zdjęcia przy najechaniu */
    }

    /* BADGE STATUSU */
    .status-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background-color: rgba(16, 185, 129, 0.9); /* Zielony sukces */
        color: white;
        padding: 4px 10px;
        font-size: 11px;
        font-weight: 700;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        backdrop-filter: blur(4px);
    }

    /* TREŚĆ KARTY */
    .card-body {
        padding: 20px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    .price-main {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }

    .title-main {
        font-size: 15px;
        font-weight: 400;
        color: #9ca3af; /* Szary tekst */
        line-height: 1.5;
        margin-bottom: 20px;
        display: -webkit-box;
        -webkit-line-clamp: 2; /* Maks 2 linie tekstu */
        -webkit-box-orient: vertical;
        overflow: hidden;
    }

    /* PRZYCISK AKCJI */
    a.action-btn {
        display: block;
        width: 100%;
        padding: 12px 0;
        background-color: #2563eb; /* Corporate Blue */
        color: white !important;
        text-align: center;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        font-size: 14px;
        transition: background-color 0.2s;
    }

    a.action-btn:hover {
        background-color: #1d4ed8;
    }

    /* MODYFIKACJA ZAKŁADEK STREAMLIT */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #1f2937;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px;
        color: #9ca3af;
        border: none;
        background-color: transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0e1117 !important;
        color: white !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }
    
    /* Ukrycie domyślnego menu Streamlit (hamburger) dla czystego wyglądu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
</style>
""", unsafe_allow_html=True)

# --- 3. BAZA DANYCH LINKÓW ---
LINKS_MOJE = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8"
]
LINKS_MIESZKANIA = [
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/mieszkanie-3-pok-balkon-garaz-komorka-lokatorska-ID4z4ja"
]
LINKS_KAWALERKI = [
    "https://www.otodom.pl/pl/oferta/gotowe-do-odbioru-centrum-duzy-balkon-ID4z3Xy",
]
LINKS_DOMY = [
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2",
]


# --- 4. ENGINE SCRAPUJĄCY ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    # Domyślne dane (Placeholder)
    offer_data = {
        "title": "Wczytywanie oferty...", 
        "price_str": "--- zł", 
        "image_url": "https://via.placeholder.com/800x600/1f2937/ffffff?text=Brak+Zdjecia", 
        "link": url
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Tytuł
            h1_tag = soup.find("h1", attrs={"data-cy": "adPageAdTitle"})
            if h1_tag: offer_data["title"] = h1_tag.get_text().strip()
            
            # JSON Data (Cena i Zdjęcie)
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

# --- 5. RENDEROWANIE SIATKI (GRID SYSTEM) ---
def render_professional_grid(links_list, category_name):
    if not links_list:
        st.info("Brak zdefiniowanych ofert w tej kategorii.")
        return

    # Header sekcji z przyciskiem akcji po prawej
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.markdown(f"### {category_name}")
    with col_h2:
        scan_btn = st.button(f"↻ ODŚWIEŻ DANE", key=category_name, use_container_width=True)

    if scan_btn:
        progress_bar = st.progress(0)
        results = []
        
        # Pobieranie danych
        for i, link in enumerate(links_list):
            results.append(get_offer_data(link))
            progress_bar.progress((i + 1) / len(links_list))
            time.sleep(0.1) # Lekkie opóźnienie dla płynności UI
        
        progress_bar.empty()
        
        # Grid 3-kolumnowy
        cols = st.columns(3)
        
        for i, data in enumerate(results):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="property-card">
                    <div class="image-wrapper">
                        <div class="status-badge">AKTYWNA</div>
                        <img src="{data['image_url']}" class="card-img">
                    </div>
                    <div class="card-body">
                        <div>
                            <div class="price-main">{data['price_str']}</div>
                            <div class="title-main">{data['title']}</div>
                        </div>
                        <a href="{data['link']}" target="_blank" class="action-btn">ZOBACZ SZCZEGÓŁY</a>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.caption(f"Kliknij 'Odśwież', aby pobrać aktualne ceny dla {len(links_list)} nieruchomości.")

# --- 6. GŁÓWNY INTERFEJS ---
st.title("Estate Monitor Pro")
st.markdown("Panel analityczny rynku nieruchomości.")
st.write("") # Odstęp

# Zakładki
tab1, tab2, tab3, tab4 = st.tabs(["ULUBIONE", "MIESZKANIA", "KAWALERKI", "DOMY"])

with tab1:
    render_professional_grid(LINKS_MOJE, "Moja Lista Obserwowanych")

with tab2:
    st.markdown("[Przejdź do Otodom (Wrocław - Mieszkania)](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw)")
    render_professional_grid(LINKS_MIESZKANIA, "Rynek Wtórny i Pierwotny")

with tab3:
    render_professional_grid(LINKS_KAWALERKI, "Inwestycje (Kawalerki)")

with tab4:
    render_professional_grid(LINKS_DOMY, "Domy i Szeregowce")
