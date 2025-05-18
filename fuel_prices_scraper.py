import requests
from bs4 import BeautifulSoup
import json
import logging
from datetime import datetime
import os

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
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji
        date_text = None
        date_header = soup.find('th', text=lambda t: t and "2025" in t)
        if date_header:
            date_text = date_header.text.strip()
        
        # Pobieranie cen paliw
        prices = []
        
        # Znajdujemy wszystkie komórki z cenami (wartości w tabeli)
        price_cells = soup.find_all('td', text=lambda t: t and '.' in t and len(t) < 6)
        
        # Bierzemy pierwsze 4 komórki, które powinny odpowiadać cenom PB95, PB98, ON, LPG
        for i, cell in enumerate(price_cells[:4]):
            if i < len(FUEL_TYPES):
                price = cell.text.strip()
                # Próbujemy przekonwertować na float, jeśli to możliwe
                try:
                    price_value = float(price.replace(',', '.'))
                    prices.append(price_value)
                except ValueError:
                    prices.append(None)
        
        # Jeśli mamy mniej niż 4 ceny, uzupełniamy resztę jako None
        while len(prices) < 4:
            prices.append(None)
        
        # Tworzymy słownik z danymi
        result = {
            "date": date_text,
            "prices": {
                FUEL_TYPES[i]: prices[i] for i in range(len(FUEL_TYPES)) if i < len(prices)
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas przetwarzania województwa {voivodeship_name}: {str(e)}")
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
