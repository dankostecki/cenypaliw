Użytkownik pokazał fragment kodu z definicją URL dla województwa zachodniopomorskiego. Wygląda na to, że używa URL:
import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import os
import re
import time

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fuel_prices_scraper")

# Lista województw i ich stron
VOIVODESHIPS = {
    "dolnoslaskie": "https://www.reflex.com.pl/dolnoslaskie-wojewodztwo",
    "kujawsko-pomorskie": "https://www.reflex.com.pl/kujawsko-pomorskie-wojewodztwo",
    "lubelskie": "https://www.reflex.com.pl/lubelskie-wojewodztwo",
    "lubuskie": "https://www.reflex.com.pl/lubuskie-wojewodztwo",
    "lodzkie": "https://www.reflex.com.pl/lodzkie-wojewodztwo",
    "malopolskie": "https://www.reflex.com.pl/malopolskie-wojewodztwo",
    "mazowieckie": "https://www.reflex.com.pl/mazowieckie-wojewodztwo",
    "opolskie": "https://www.reflex.com.pl/opolskie-wojewodztwo",
    "podkarpackie": "https://www.reflex.com.pl/podkarpackie-wojewodztwo",
    "podlaskie": "https://www.reflex.com.pl/podlaskie-wojewodztwo",
    "pomorskie": "https://www.reflex.com.pl/pomorskie-wojewodztwo",
    "slaskie": "https://www.reflex.com.pl/slaskie-wojewodztwo",
    "swietokrzyskie": "https://www.reflex.com.pl/swietokrzyskie-wojewodztwo",
    "warminsko-mazurskie": "https://www.reflex.com.pl/warminsko-mazurskie-wojewodztwo",
    "wielkopolskie": "https://www.reflex.com.pl/wielkopolskie-wojewodztwo",
    "zachodniopomorskie": "https://www.reflex.com.pl/zachodniopomorskie-wojewodztwo"
}

# Nazwy paliw
FUEL_TYPES = ['PB95', 'PB98', 'ON', 'LPG']

def extract_price(text):
    """Wyciąga liczbę z tekstu i konwertuje ją na float"""
    if not text:
        return None
    
    # Usuń wszystkie znaki oprócz cyfr, kropki i przecinka
    clean_text = ''.join(c for c in text if c.isdigit() or c in ['.', ','])
    
    # Zamień przecinek na kropkę (format polski -> angielski)
    clean_text = clean_text.replace(',', '.')
    
    try:
        return float(clean_text)
    except ValueError:
        return None

def scrape_voivodeship(voivodeship_name, url):
    """Pobiera dane dla konkretnego województwa"""
    logger.info(f"Pobieranie danych dla województwa: {voivodeship_name}")
    
    try:
        # Dodajemy parametr _nocache, aby uniknąć buforowania
        nocache_param = f"?_nocache={int(time.time())}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        full_url = url + nocache_param
        logger.info(f"Pobieranie strony: {full_url}")
        
        # Próbuj pobrać stronę kilka razy
        max_retries = 3
        for retry in range(max_retries):
            try:
                response = requests.get(full_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    break
                logger.warning(f"Próba {retry+1}/{max_retries}: status {response.status_code}")
                time.sleep(2)  # Czekaj 2 sekundy przed kolejną próbą
            except Exception as e:
                logger.warning(f"Próba {retry+1}/{max_retries} nieudana: {str(e)}")
                time.sleep(2)
        
        if response.status_code != 200:
            logger.error(f"Wszystkie próby pobierania strony nieudane: {response.status_code}")
            return create_empty_data(voivodeship_name)
        
        # Zapisz HTML do debugowania
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/{voivodeship_name}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji (różne formaty)
        date_text = find_date(soup)
        
        # Pobieranie cen paliw
        prices = find_prices(soup)
        
        # Tworzymy słownik z danymi
        result = {
            "date": date_text,
            "prices": {
                FUEL_TYPES[i]: prices[i] if i < len(prices) else None 
                for i in range(len(FUEL_TYPES))
            }
        }
        
        logger.info(f"Dane dla {voivodeship_name}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas przetwarzania województwa {voivodeship_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return create_empty_data(voivodeship_name)

def find_date(soup):
    """Znajduje datę aktualizacji w stronie"""
    date_text = None
    
    # Metoda 1: Szukanie w nagłówkach tabeli
    for th in soup.find_all('th'):
        th_text = th.get_text(strip=True)
        # Szukamy daty w formacie YYYY-MM-DD
        date_match = re.search(r'202\d-\d{2}-\d{2}', th_text)
        if date_match:
            date_text = date_match.group(0)
            break
    
    # Metoda 2: Szukanie w tekście strony
    if not date_text:
        page_text = soup.get_text()
        date_patterns
