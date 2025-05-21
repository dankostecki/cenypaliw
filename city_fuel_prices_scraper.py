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
        logging.FileHandler("city_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("city_fuel_prices_scraper")

# URL strony z cenami dla miast
CITY_PRICES_URL = "https://www.wnp.pl/rynki/gielda-i-notowania/ceny-paliw/"

# Mapowanie nazw paliw
FUEL_MAP = {
    "E95": "PB95",
    "E98": "PB98",
    "ON": "ON",
    "LPG": "LPG"
}

# Kolejność paliw w naszym systemie
OUR_FUEL_ORDER = ["PB95", "PB98", "ON", "LPG"]

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

def scrape_cities_data():
    """Pobiera dane dla miast wojewódzkich"""
    logger.info("Pobieranie danych dla miast wojewódzkich")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(CITY_PRICES_URL, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Błąd podczas pobierania strony: {response.status_code}")
            return None, None
        
        # Zapisujemy HTML do pliku dla celów debugowych
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/city_prices_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji
        date_text = None
        date_header = soup.find('h2', text=lambda t: t and re.search(r'w dniu \d{4}-\d{2}-\d{2}', t))
        if date_header:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_header.text)
            if date_match:
                date_text = date_match.group(1)
                logger.info(f"Znaleziono datę: {date_text}")
        else:
            logger.warning("Nie znaleziono daty na stronie")
        
        # Szukanie tabeli z cenami miast wojewódzkich
        cities_data = {}
        table = None
        
        # Szukamy elementu h2 z odpowiednim tekstem, a następnie najbliższej tabeli po nim
        title_element = soup.find('h2', text=lambda t: t and "Detaliczne ceny paliw w poszczególnych miastach wojewódzkich" in t)
        if title_element:
            # Znajdź najbliższą tabelę po elemencie h2
            table = title_element.find_next('table')
        
        if not table:
            logger.error("Nie znaleziono tabeli z cenami miast")
            return date_text, {}
        
        # Pobierz nagłówki tabeli
        headers = []
        header_row = table.find('thead').find('tr')
        for th in header_row.find_all('th'):
            headers.append(th.text.strip())
        
        # Sprawdź, czy mamy oczekiwane nagłówki (MIASTO, ON, E95, E98, LPG)
        if len(headers) < 5 or "MIASTO" not in headers:
            logger.error(f"Nieoczekiwana struktura nagłówków tabeli: {headers}")
            return date_text, {}
        
        # Znajdź indeksy kolumn dla każdego typu paliwa
        fuel_indices = {}
        for i, header in enumerate(headers):
            if header in FUEL_MAP:
                fuel_indices[FUEL_MAP[header]] = i
        
        # Pobierz dane z wierszy tabeli
        rows = table.find('tbody').find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= len(headers):
                city_name = cells[0].text.strip()
                
                # Tworzenie słownika z cenami w naszej kolejności
                prices = {}
                for fuel_type in OUR_FUEL_ORDER:
                    if fuel_type in fuel_indices:
                        # Pobierz indeks kolumny dla tego paliwa
                        idx = fuel_indices[fuel_type]
                        if idx < len(cells):
                            price_text = cells[idx].text.strip()
                            price_value = extract_price(price_text)
                            prices[fuel_type] = price_value
                
                cities_data[city_name] = {
                    "prices": prices
                }
                logger.info(f"Pobrano dane dla miasta: {city_name}")
        
        logger.info(f"Pobrano dane dla {len(cities_data)} miast")
        return date_text, cities_data
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas pobierania danych dla miast: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, {}

def main():
    """Główna funkcja programu"""
    logger.info("Rozpoczynam pobieranie cen paliw dla miast")
    
    # Pobierz dane miast
    date_text, cities_data = scrape_cities_data()
    
    results = {
        "update_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cities_date": date_text,
        "cities": cities_data
    }
    
    # Zapisujemy wyniki do pliku JSON
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Zapisujemy tylko najnowsze dane dla miast
    cities_file = os.path.join(output_dir, "cities.json")
    with open(cities_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Dane miast zostały zapisane do pliku {cities_file}")

if __name__ == "__main__":
    main()
