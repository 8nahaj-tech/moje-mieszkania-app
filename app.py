import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import pandas as pd
import datetime

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Monitor Cen Mieszkań", page_icon="🏢", layout="wide")

# Stylizacja CSS (wygląd)
st.markdown("""
<style>
    .big-font { font-size:20px !important; font-weight: bold; }
    div.stButton > button { width: 100%; background-color: #0078D4; color: white; border-radius: 8px; height: 50px; font-size: 18px;}
    img { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- TWOJE LINKI ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- FUNKCJA POBIERAJĄCA DANE ---
def get_offer_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    offer_data = {
        "title": "Nieznana oferta",
        "price": 0,
        "price_str": "Brak danych",
        "image_url": None,
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
                
                # 1. Tytuł i Cena
                offer_data["title"] = ad_target.get('Title', 'Brak tytułu')
                raw_price = ad_target.get('Price', 0)
                
                if isinstance(raw_price, (int, float)):
                    offer_data["price"] = raw_price
                    offer_data["price_str"] = f"{raw_price:,.0f} zł".replace(",", " ")
                
                # 2. Zdjęcie (Szukamy pierwszego zdjęcia w galerii)
                try:
                    images = data['props']['pageProps']['ad']['images']
                    if images and len(images) > 0:
                        # Pobieramy wersję "medium" lub "large"
                        offer_data["image_url"] = images[0].get('medium') or images[0].get('large')
                except:
                    pass
                    
    except:
        pass
        
    return offer_data

# --- INTERFEJS APLIKACJI ---

st.title("🏢 Wizualny Monitor Ofert")
st.write("Sprawdź aktualne ceny i zobacz zdjęcia mieszkań.")

if st.button("🔄 POBIERZ DANE I ZDJĘCIA"):
    
    results = []
    progress_bar = st.progress(0)
    
    for i, link in enumerate(LINKS):
        progress_bar.progress((i + 1) / len(LINKS))
        
        # Pobieramy wszystkie dane
        data = get_offer_data(link)
        results.append(data)
        
        time.sleep(0.5) 

    progress_bar.empty()
    
    # --- WYŚWIETLANIE KAFLI ---
    st.divider()
    
    for item in results:
        # Tworzymy układ 2 kolumn: [Zdjęcie (1/3)] | [Opis (2/3)]
        col1, col2 = st.columns([1, 2])
        
        with col1:
            if item["image_url"]:
                st.image(item["image_url"], use_container_width=True)
            else:
                st.warning("Brak zdjęcia")
        
        with col2:
            st.subheader(item["title"])
            st.metric(label="Cena", value=item["price_str"])
            st.markdown(f"[🔗 Przejdź do ogłoszenia na Otodom]({item['link']})")
        
        st.divider() # Linia oddzielająca oferty

    # --- POBIERANIE RAPORTU ---
    # Przygotowanie prostych danych do Excela (bez zdjęć, bo Excel tego nie lubi w CSV)
    simple_data = [{k: v for k, v in res.items() if k != 'image_url'} for res in results]
    df = pd.DataFrame(simple_data)
    
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="💾 Pobierz tabelę (CSV)",
        data=csv,
        file_name='mieszkania_ze_zdjeciami.csv',
        mime='text/csv',
    )
