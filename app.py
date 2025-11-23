import streamlit as st
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import json

# --- DIAGNOSTYKA SYSTEMU ---
st.set_page_config(page_title="Diagnostyka AI", page_icon="🛠️", layout="wide")
st.title("🛠️ Tryb Diagnostyczny")

# 1. Sprawdzamy czy Scikit-Learn (Mózg) jest zainstalowany
try:
    from sklearn.linear_model import LinearRegression
    st.success("✅ Biblioteka 'scikit-learn' (Mózg AI) jest zainstalowana poprawnie.")
except ImportError as e:
    st.error(f"❌ BŁĄD KRYTYCZNY: Serwer nie ma biblioteki AI! Szczegóły: {e}")
    st.info("💡 Rozwiązanie: Sprawdź plik requirements.txt na GitHubie. Musi tam być napisane: scikit-learn")
    st.stop() # Zatrzymujemy program, bo nie ma sensu iść dalej

# 2. Sprawdzamy czy Matplotlib (Wykresy) jest zainstalowany
try:
    import matplotlib.pyplot as plt
    st.success("✅ Biblioteka 'matplotlib' (Wykresy) jest zainstalowana poprawnie.")
except ImportError as e:
    st.error(f"❌ BŁĄD KRYTYCZNY: Brak biblioteki do wykresów! Szczegóły: {e}")
    st.stop()

st.divider()

# --- JEŚLI DOTARLIŚMY TU, TO ZNACZY ŻE BIBLIOTEKI SĄ OK ---

# DANE ZAPASOWE (Gwarantowane)
BACKUP_DATA = [
    {"price": 350000, "area": 30},
    {"price": 450000, "area": 40},
    {"price": 550000, "area": 50},
    {"price": 650000, "area": 60},
    {"price": 850000, "area": 80},
]

st.subheader("🔮 Test Predyktora")

# Suwak
user_area = st.slider("Wybierz metraż testowy (m²):", 20, 100, 50)

if st.button("🚀 URUCHOM SZTUCZNĄ INTELIGENCJĘ"):
    
    # Tworzymy DataFrame z danych zapasowych (żeby wykluczyć błąd Otodom)
    df = pd.DataFrame(BACKUP_DATA)
    
    # Trenujemy model
    X = df['area'].values.reshape(-1, 1)
    y = df['price'].values
    
    model = LinearRegression()
    model.fit(X, y)
    
    prediction = model.predict([[user_area]])[0]
    
    # WYNIK
    st.markdown(f"""
    <div style="padding: 20px; background-color: #d1fae5; border-radius: 10px; color: #065f46;">
        <h2 style="margin:0">Wynik AI: {prediction:,.0f} zł</h2>
        <small>Działa! AI obliczyło to na podstawie danych testowych.</small>
    </div>
    """, unsafe_allow_html=True)
    
    # WYKRES
    fig, ax = plt.subplots()
    ax.scatter(df['area'], df['price'], color='blue', label='Dane')
    ax.scatter([user_area], [prediction], color='red', s=100, label='Twoja Wycena')
    ax.plot(df['area'], model.predict(X), color='gray', linestyle='--')
    ax.legend()
    st.pyplot(fig)

else:
    st.info("Kliknij przycisk, aby przetestować obliczenia.")
