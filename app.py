import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time

# --- 1. KONFIGURACJA STRONY ---
st.set_page_config(page_title="Wrocław Estate Center", page_icon="🏙️", layout="wide")

# --- 2. STYLIZACJA CSS (WYGLĄD + ANIMACJA ASYSTENTA) ---
st.markdown("""
<style>
    /* Tło aplikacji */
    .stApp {
        background: linear-gradient(135deg, #141E30 0%, #243B55 100%);
        color: white;
    }
    
    /* --- NOWA ANIMACJA: "LOT PRZEWODNIKA" --- */
    @keyframes guide-sequence {
        /* 1. Start: Okolice zakładki "Moje Wybrane" (lewa góra) */
        0%   { left: 2%;  top: 110px; transform: scale(1) rotate(0deg); filter: drop-shadow(0 0 10px rgba(255,255,255,0.4)); }
        10%  { left: 2%;  top: 110px; transform: scale(1.1) rotate(5deg); } /* Lekkie uniesienie */

        /* 2. Lot do przycisku "SKANUJ" (środek ekranu) */
        25%  { left: 45%; top: 230px; transform: scale(1) rotate(10deg); }
        /* "WSKAZANIE": Powiększenie i złota poświata */
        35%  { left: 45%; top: 230px; transform: scale(1.4) rotate(0deg); filter: drop-shadow(0 0 35px rgba(255, 215, 0, 1)); }
        40%  { left: 45%; top: 230px; transform: scale(1) rotate(0deg); }

        /* 3. Lot w dół do obszaru "ofert" */
        55%  { left: 15%; top: 600px; transform: scale(1) rotate(-10deg); filter: drop-shadow(0 0 10px rgba(255,255,255,0.4)); }

        /* 4. "UŚMIECH I OCZKO" -> Radosny piruet i zielone światło sukcesu */
        65%  { left: 15%; top: 600px; transform: scale(1.2) rotate(0deg); }
        70%  { left: 15%; top: 600px; transform: scale(1.3) rotate(360deg); filter: drop-shadow(0 0 30px rgba(50, 255, 50, 1)); } /* OBRÓT! */
        75%  { left: 15%; top: 600px; transform: scale(1.2) rotate(340deg); }
        80%  { left: 15%; top: 600px; transform: scale(1.2) rotate(380deg); }

        /* 5. Odlot poza ekran */
        100% { left: 120%; top: 300px; transform: scale(1) rotate(20deg); }
    }

    .harry-potter {
        position: fixed;
        z-index: 99999; /* Zawsze na wierzchu */
        width: 110px;   /* Rozmiar postaci */
        /* Animacja trwa 25s, jest płynna (ease-in-out) i zapętlona */
        animation: guide-sequence 25s ease-in-out infinite;
        pointer-events: none; /* Kliknięcia przez niego przechodzą */
    }

    /* Stylizacja Zakładek */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; white-space: pre-wrap; background-color: rgba(255,255,255,0.05);
        border-radius: 10px 10px 0 0; color: white; font-weight: bold;
    }
    .stTabs [aria-selected="true"] { background-color: #00d2ff !important; color: black !important; }

    /* Karty Ofert */
    .offer-card {
        background-color: rgba(0, 0, 0, 0.3); padding: 20px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* Teksty i Przyciski */
    .offer-title { font-size: 20px; font-weight: 600; color: #f0f0f0; margin-bottom: 10px; }
    .price-tag { font-size: 32px; font-weight: 800; color: #00d2ff; text-shadow: 0 0 10px rgba(0, 210, 255, 0.3); }
    
    div.stButton > button {
        width: 100%; background: linear-gradient(90deg, #1CB5E0 0%, #000851 100%);
        border: none; color: white; padding: 15px; font-weight: bold; border-radius: 10px;
    }
    
    a.link-btn {
        display: inline-block; background-color: #ff416c; color: white !important;
        padding: 8px 20px; border-radius: 50px; text-decoration: none; font-weight: bold; font-size: 14px;
        transition: 0.3s;
    }
    a.link-btn:hover { background-color: #ff4b2b; transform: scale(1.05); }
    
    img.offer-img { border-radius: 10px; object-fit: cover; width:100%; height:200px; }
</style>
""", unsafe_allow_html=True)

# --- 3. WSTAWIENIE MAGA-ASYSTENTA ---
# Używamy niezawodnej grafiki 3D z GitHuba
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
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a"
]
LINKS_KAWALERKI = [
    "https://www.otodom.pl/pl/oferta/gotowe-do-odbioru-centrum-duzy-balkon-ID4z3Xy",
]
LINKS_DOMY = [
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2",
]


# --- 5. FUNKCJE ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    offer_data = {"title": "Ładowanie...", "price_str": "Brak ceny", "image_url": "https://via.placeholder.com/600x400?text=Brak+Zdjecia", "link": url}
    
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
                        <img src="{data['image_url']}" class="offer-img">
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
            time.sleep(0.3)
        progress_bar.empty()
    else:
        st.write(f"Ofert do sprawdzenia: **{len(links_list)}**")

# --- 6. GŁÓWNY INTERFEJS ---
st.title("🏙️ Wrocław Estate Center")

tab1, tab2, tab3, tab4 = st.tabs(["⭐ MOJE WYBRANE", "🏢 MIESZKANIA", "🛋️ KAWALERKI", "🏡 DOMY"])

with tab1:
    st.header("Moje Ulubione")
    render_tab(LINKS_MOJE, "moje")
with tab2:
    st.header("Mieszkania Wrocław")
    st.markdown("[🔍 Szukaj na Otodom](https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/dolnoslaskie/wroclaw/wroclaw/wroclaw?viewType=listing)")
    render_tab(LINKS_MIESZKANIA, "mieszkania")
with tab3:
    st.header("Kawalerki")
    render_tab(LINKS_KAWALERKI, "kawalerki")
with tab4:
    st.header("Domy")
    render_tab(LINKS_DOMY, "domy")
