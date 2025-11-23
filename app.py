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
st.set_page_config(page_title="Estate Monitor PRO", page_icon="🏢", layout="wide")

# --- 2. STYLIZACJA (CZYSTY DARK MODE) ---
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    
    /* Ukrycie menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Stylizacja metryk */
    div[data-testid="stMetricValue"] {
        font-size: 24px;
        color: #00d2ff;
    }
    
    /* Stylizacja linku */
    a {
        text-decoration: none;
    }
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

def save_price(link, price):
    if price == 0: return
    
    today = datetime.now().strftime("%Y-%m-%d")
    new_data = {"Data": today, "Link": link, "Cena": price}
    
    if os.path.exists(HISTORY_FILE):
        df = pd.read_csv(HISTORY_FILE)
        # Sprawdzamy czy już jest wpis z dzisiaj
        check = df[(df['Link'] == link) & (df['Data'] == today)]
        if check.empty:
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(HISTORY_FILE, index=False)
    else:
        df = pd.DataFrame([new_data])
        df.to_csv(HISTORY_FILE, index=False)

def get_history_df(link):
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["Data", "Cena"])
    
    df = pd.read_csv(HISTORY_FILE)
    # Filtrujemy tylko dla tego linku
    df_link = df[df['Link'] == link][["Data", "Cena"]]
    return df_link.sort_values(by="Data", ascending=False)

# --- 5. AI OPIS ---
def generate_ai_text(area, rooms):
    if area == 0: return "Brak danych."
    desc = f"Mieszkanie {rooms}-pokojowe o powierzchni {area} m². "
    if area < 35: desc += "Idealne na start lub wynajem."
    elif area > 60: desc += "Przestronne, dla rodziny."
    else: desc += "Optymalny metraż."
    return desc

# --- 6. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {
        "title": "Wczytywanie...", "price": 0, "price_str": "---", 
        "area": 0, "rooms": 0, "img": None, 
        "link": url
    }
    
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            
            # Tytuł
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
                
                # ZAPIS DO HISTORII
                save_price(url, data["price"])
    except: pass
    return data

# --- 7. INTERFEJS ---
st.title("🏙️ Estate Monitor PRO")
st.markdown("### Panel Inwestora")

if st.button("🔄 SKANUJ RYNEK (START)", type="primary"):
    st.divider()
    
    # Pasek postępu
    progress_bar = st.progress(0)
    
    # Tworzymy Grid (3 kolumny)
    cols = st.columns(3)
    
    for i, link in enumerate(LINKS):
        progress_bar.progress((i + 1) / len(LINKS))
        
        # Pobieranie danych
        d = get_data(link)
        ai_desc = generate_ai_text(d['area'], d['rooms'])
        
        # Wybieramy kolumnę
        with cols[i % 3]:
            # --- KARTA OFERTY (NATYWNY STREAMLIT) ---
            with st.container(border=True):
                # 1. Zdjęcie
                if d['img']:
                    st.image(d['img'], use_container_width=True)
                else:
                    st.image("https://via.placeholder.com/600x400?text=Brak+Zdjecia", use_container_width=True)
                
                # 2. Cena i Tytuł
                st.markdown(f"### {d['price_str']}")
                st.caption(d['title'])
                
                # 3. Parametry
                c1, c2 = st.columns(2)
                with c1: st.metric("Metraż", f"{d['area']} m²")
                with c2: st.metric("Pokoje", f"{d['rooms']}")
                
                # 4. AI Opis
                st.info(f"🤖 **AI:** {ai_desc}")
                
                # 5. Przycisk (Link)
                st.link_button("👉 PRZEJDŹ DO OFERTY", d['link'], use_container_width=True)
                
                # 6. Historia Cen (Rozwijana)
                with st.expander("📜 Historia Cen"):
                    hist_df = get_history_df(d['link'])
                    if not hist_df.empty:
                        # Formatowanie ceny w tabeli
                        hist_df['Cena'] = hist_df['Cena'].apply(lambda x: f"{x:,.0f} zł".replace(",", " "))
                        st.dataframe(hist_df, hide_index=True, use_container_width=True)
                    else:
                        st.write("Pierwszy zapis (dzisiaj).")
                        
    progress_bar.empty()
    st.success("Aktualizacja zakończona!")

    # Pobieranie pliku historii
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "rb") as f:
            st.download_button("💾 Pobierz plik Excel/CSV z historią", f, "historia_cen.csv")

else:
    st.info("Kliknij niebieski przycisk powyżej, aby pobrać najnowsze ceny.")
