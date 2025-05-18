import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import os
import re

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
    "zachodniopomorskie": "https://www.reflex.com.pl/zachodnipomorskie-wojewodztwo"
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
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Błąd podczas pobierania strony: {response.status_code}")
            return None
        
        # Zapisujemy HTML do pliku dla celów debugowych
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/{voivodeship_name}.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji
        date_text = None
        date_header = soup.find('th', text=lambda t: t and "2025" in t)
        if date_header:
            date_text = date_header.text.strip()
        
        # Pobieranie cen paliw
        prices = [None, None, None, None]  # Inicjalizujemy listę z 4 wartościami None
        
        # Znajdź wszystkie wiersze tabeli - każdy wiersz reprezentuje inny rodzaj paliwa
        # Pierwszy obrazek i pierwszy td w każdym wierszu reprezentuje cenę paliwa
        rows = soup.find_all('tr')
        
        fuel_index = 0
        for row in rows:
            # Sprawdzamy, czy wiersz zawiera obrazek (logo paliwa)
            img = row.find('img')
            if img and fuel_index < 4:  # Ograniczamy do 4 paliw
                # Znajdź pierwszą komórkę z ceną w tym wierszu
                cells = row.find_all('td')
                if cells and len(cells) >= 2:  # Pierwszy cell to obrazek, drugi to cena
                    price_cell = cells[1]  # Druga komórka zawiera cenę
                    if price_cell:
                        price_text = price_cell.get_text(strip=True)
                        price_value = extract_price(price_text)
                        prices[fuel_index] = price_value
                        logger.info(f"Znaleziono cenę dla {FUEL_TYPES[fuel_index]}: {price_value}")
                fuel_index += 1
        
        # Tworzymy słownik z danymi
        result = {
            "date": date_text,
            "prices": {
                FUEL_TYPES[i]: prices[i] for i in range(len(FUEL_TYPES))
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas przetwarzania województwa {voivodeship_name}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def main():
    """Główna funkcja programu"""
    logger.info("Rozpoczynam pobieranie cen paliw")
    
    results = {
        "update_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "voivodeships": {}
    }
    
    for voivodeship_name, url in VOIVODESHIPS.items():
        voivodeship_data = scrape_voivodeship(voivodeship_name, url)
        if voivodeship_data:
            results["voivodeships"][voivodeship_name] = voivodeship_data
    
    # Zapisujemy wyniki do pliku JSON
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Zapisujemy najnowsze dane
    latest_file = os.path.join(output_dir, "latest.json")
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # Zapisujemy dane również z datą w nazwie pliku
    date_file = os.path.join(output_dir, f"fuel_prices_{datetime.now().strftime('%Y-%m-%d')}.json")
    with open(date_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Dane zostały zapisane do plików {latest_file} i {date_file}")


if __name__ == "__main__":
    main()
