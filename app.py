import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pandas as pd
import numpy as np

# --- IMPORTY AI Z OBSŁUGĄ BŁĘDÓW ---
try:
    from sklearn.linear_model import LinearRegression
    import matplotlib.pyplot as plt
    AI_DOSTEPNE = True
except ImportError:
    AI_DOSTEPNE = False

# --- 1. KONFIGURACJA ---
st.set_page_config(page_title="Estate Monitor AI", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: white; }
    .ai-box { background: #1e3a8a; padding: 20px; border-radius: 10px; border: 1px solid #3b82f6; margin-top: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 2. DANE ---
LINKS = [
    "https://www.otodom.pl/pl/oferta/nowe-wykonczone-2-pok-ogrod-blisko-uczelni-ID4yZO0",
    "https://www.otodom.pl/pl/oferta/piekne-mieszkanie-dwupoziomowe-4-pokojowe-z-balkon-ID4z2b8",
    "https://www.otodom.pl/pl/oferta/mieszkanie-dwupoziomowe-z-ogrodem-pod-lesnica-ID4z02A",
    "https://www.otodom.pl/pl/oferta/3-pokoje-z-balkonem-w-nowym-apartamentowcu-ID4yU9a",
    "https://www.otodom.pl/pl/oferta/5-pokoi-szereg-ogrodek-stacja-pkp-wroclaw-ID4yBI2"
]

# --- 3. SCRAPER ---
def get_data(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"price": 0, "area": 0, "img": None, "link": url}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            soup = BeautifulSoup(r.content, "html.parser")
            script = soup.find("script", id="__NEXT_DATA__")
            if script:
                j = json.loads(script.string)
                target = j['props']['pageProps']['ad']['target']
                data["price"] = float(target.get('Price', 0))
                data["area"] = float(target.get('Area', 0))
                imgs = j['props']['pageProps']['ad']['images']
                if imgs: data["img"] = imgs[0].get('medium')
    except: pass
    return data

# --- 4. FUNKCJA AI ---
def run_ai(dataset, user_area):
    # Filtrujemy tylko poprawne dane
    valid = [d for d in dataset if d['price'] > 0 and d['area'] > 0]
    
    if len(valid) < 2:
        st.warning(f"⚠️ Za mało danych do AI. Pobrano poprawnie: {len(valid)} ofert. Potrzeba minimum 2.")
        return

    # Przygotowanie danych
    X = np.array([d['area'] for d in valid]).reshape(-1, 1)
    y = np.array([d['price'] for d in valid])

    # Trening
    model = LinearRegression()
    model.fit(X, y)
    prediction = model.predict(np.array([[user_area]]))[0]

    # WYNIK
    st.markdown(f"""
    <div class="ai-box">
        <h3>🔮 AI Przewiduje:</h3>
        Wartość mieszkania <b>{user_area} m²</b> to:
        <h1 style="color:#60a5fa">{prediction:,.0f} zł</h1>
    </div>
    """, unsafe_allow_html=True)

    # WYKRES
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#1f2937')
    
    # Punkty
    ax.scatter(df['area'], df['price'], color='#60a5fa', s=100, label='Oferty')
    # Predykcja
    ax.scatter([user_area], [prediction], color='#ef4444', s=200, label='Twoja Wycena')
    # Linia trendu
    line_x = np.linspace(df['area'].min(), df['area'].max(), 100).reshape(-1, 1)
    line_y = model.predict(line_x)
    ax.plot(line_x, line_y, color='white', linestyle='--', alpha=0.5)
    
    ax.tick_params(colors='white')
    ax.legend()
    st.pyplot(fig)


# --- 5. INTERFEJS ---
st.title("🤖 Estate Monitor AI - Tryb Diagnostyczny")

if not AI_DOSTEPNE:
    st.error("❌ BŁĄD: Biblioteki AI nie są zainstalowane! Sprawdź plik requirements.txt (czy jest tam scikit-learn i matplotlib).")
else:
    st.success("✅ Biblioteki AI są gotowe.")

if st.button("🚀 URUCHOM ANALIZĘ"):
    
    progress = st.progress(0)
    dataset = []
    
    cols = st.columns(len(LINKS))
    
    for i, link in enumerate(LINKS):
        progress.progress((i + 1) / len(LINKS))
        d = get_data(link)
        dataset.append(d)
        
        with cols[i]:
            if d['img']: st.image(d['img'])
            st.caption(f"{d['price']:,.0f} zł | {d['area']} m²")
    
    progress.empty()
    
    # Przekazujemy dane do DataFrame żeby łatwiej rysować wykres
    df = pd.DataFrame(dataset)
    df = df[df['area'] > 0] # Tylko poprawne
    
    st.divider()
    
    if df.empty:
        st.error("❌ Nie udało się pobrać cen z Otodom. Strona mogła zablokować zapytania lub zmienić strukturę.")
    else:
        st.write(f"📊 Zebrano dane z {len(df)} ofert. Uruchamiam AI...")
        
        # Suwak
        user_area = st.slider("Wybierz metraż (m²)", 20, 100, 50)
        
        # Odpalenie AI
        run_ai(dataset, user_area)
