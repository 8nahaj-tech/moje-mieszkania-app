import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import time
import random

# Tytuł i opis strony
st.set_page_config(page_title="Łowca Mieszkań", page_icon="🏢")
st.title("🏢 Tropiciel Cen Mieszkań")
st.write("Ta aplikacja sprawdza aktualne ceny wybranych mieszkań na Otodom.")

# Lista Twoich mieszkań (możesz tu dodawać nowe)
lista_mieszkan = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# Przycisk uruchamiający sprawdzanie
if st.button("🔄 Sprawdź aktualne ceny"):
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7"
    }
    
    pasek_postepu = st.progress(0)
    
    for i, url in enumerate(lista_mieszkan):
        # Aktualizacja paska postępu
        pasek_postepu.progress((i + 1) / len(lista_mieszkan))
        
        try:
            response = requests.get(url, headers=headers)
            cena_wyswietlana = "Brak danych"
            tytul = "Nieznana oferta"
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                script_data = soup.find("script", id="__NEXT_DATA__")
                
                if script_data:
                    try:
                        data = json.loads(script_data.string)
                        ad_target = data['props']['pageProps']['ad']['target']
                        cena_raw = ad_target.get('Price', 0)
                        tytul = ad_target.get('Title', 'Brak tytułu')
                        
                        if isinstance(cena_raw, (int, float)):
                            cena_wyswietlana = f"{cena_raw:,.0f} zł".replace(",", " ")
                    except:
                        pass
                
                # Wyświetlanie ładnego kafelka z wynikiem
                st.success(f"**{tytul}**")
                st.metric(label="Aktualna Cena", value=cena_wyswietlana)
                st.markdown(f"[🔗 Zobacz ofertę]({url})")
                st.divider()
                
            else:
                st.error(f"Nie udało się pobrać danych z linku nr {i+1}")
                
        except Exception as e:
            st.error(f"Błąd: {e}")
            
        # Krótka pauza żeby nie zablokowali
        time.sleep(1)
        
    st.balloons() # Efekt wizualny na koniec
    st.info("Koniec sprawdzania!")

else:
    st.info("Kliknij przycisk powyżej, aby pobrać najnowsze ceny.")
