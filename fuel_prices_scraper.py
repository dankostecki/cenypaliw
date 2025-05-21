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

# URL strony z cenami krajowymi
NATIONAL_URL = "https://www.reflex.com.pl/ceny-detaliczne-polska"

# URL strony z cenami w miastach wojewódzkich
CITIES_URL = "https://www.wnp.pl/rynki/gielda-i-notowania/ceny-paliw/"

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

# Nazwy paliw dla województw (w kolejności występowania na stronie Reflex)
FUEL_TYPES = ['PB95', 'PB98', 'ON', 'LPG']

# Typy paliw dla miast (niezależne od kolejności na stronie - wykryjemy je dynamicznie)
CITY_FUEL_TYPES = ['ON', 'PB95', 'PB98', 'LPG']  # tylko informacyjnie

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

def scrape_national_date():
    """Pobiera datę z krajowej strony cen paliw"""
    logger.info("Pobieranie daty z krajowej strony cen paliw")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(NATIONAL_URL, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Błąd podczas pobierania strony krajowej: {response.status_code}")
            return None
        
        # Zapisujemy HTML do pliku dla celów debugowych
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/national_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji
        date_text = None
        date_header = soup.find('th', text=lambda t: t and re.search(r'\d{4}-\d{2}-\d{2}', t))
        if date_header:
            date_text = date_header.text.strip()
            logger.info(f"Znaleziono datę krajową: {date_text}")
        else:
            logger.warning("Nie znaleziono daty na stronie krajowej")
        
        return date_text
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas pobierania daty krajowej: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def scrape_cities():
    """Pobiera dane o cenach paliw w miastach wojewódzkich"""
    logger.info("Pobieranie danych o cenach paliw w miastach wojewódzkich")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(CITIES_URL, headers=headers, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Błąd podczas pobierania strony z cenami w miastach: {response.status_code}")
            return None, None
        
        # Zapisujemy HTML do pliku dla celów debugowych
        debug_dir = "debug"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/cities_page.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Szukanie daty aktualizacji
        cities_date = None
        date_header = soup.find('h2', text=lambda t: t and "ceny paliw" in t.lower() and re.search(r'\d{4}-\d{2}-\d{2}', t))
        if date_header:
            # Wyciągnij datę z tekstu za pomocą wyrażenia regularnego
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_header.text)
            if date_match:
                cities_date = date_match.group(1)
                logger.info(f"Znaleziono datę dla miast: {cities_date}")
            else:
                logger.warning("Data dla miast znaleziona, ale nie pasuje do oczekiwanego formatu")
        else:
            logger.warning("Nie znaleziono daty dla miast")
        
        # Znajdź tabelę z cenami
        table = soup.find('table', class_='table')
        if not table:
            logger.error("Nie znaleziono tabeli z cenami w miastach")
            return None, cities_date
        
        # Znajdź kolumny nagłówkowe (nazwy paliw)
        thead = table.find('thead')
        if not thead:
            logger.error("Nie znaleziono nagłówka tabeli z cenami w miastach")
            return None, cities_date
        
        # Pobierz nagłówki kolumn
        headers = []
        header_row = thead.find('tr')
        if header_row:
            headers = [th.text.strip() for th in header_row.find_all('th')]
            logger.info(f"Znalezione nagłówki tabeli: {headers}")
        
        # Znajdź indeksy kolumn dla poszczególnych paliw - niezależne od kolejności!
        fuel_indices = {}
        for i, header in enumerate(headers):
            if header == 'ON':
                fuel_indices['ON'] = i
                logger.info(f"Kolumna ON na pozycji {i}")
            elif header == 'PB95':
                fuel_indices['PB95'] = i
                logger.info(f"Kolumna PB95 na pozycji {i}")
            elif header == 'PB98':
                fuel_indices['PB98'] = i
                logger.info(f"Kolumna PB98 na pozycji {i}")
            elif header == 'LPG':
                fuel_indices['LPG'] = i
                logger.info(f"Kolumna LPG na pozycji {i}")
        
        # Indeks kolumny z nazwami miast
        city_index = None
        for i, header in enumerate(headers):
            if header == 'MIASTO' or 'MIASTO' in header:
                city_index = i
                logger.info(f"Kolumna MIASTO na pozycji {i}")
                break
        
        if city_index is None:
            logger.error("Nie znaleziono kolumny z nazwami miast")
            return None, cities_date
        
        # Pobierz dane z wierszy
        cities_data = {}
        tbody = table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) <= max(city_index, max(fuel_indices.values(), default=0)):
                    continue
                
                # Pobierz nazwę miasta
                city_name = cells[city_index].text.strip().replace('"', '')
                
                # Pobierz ceny paliw
                prices = {}
                for fuel_type, col_index in fuel_indices.items():
                    price_text = cells[col_index].text.strip()
                    price = extract_price(price_text)
                    prices[fuel_type] = price
                    logger.info(f"Miasto {city_name}, paliwo {fuel_type}: {price}")
                
                cities_data[city_name] = {"prices": prices}
        
        logger.info(f"Pobrano dane dla {len(cities_data)} miast")
        
        return cities_data, cities_date
        
    except Exception as e:
        logger.error(f"Wystąpił błąd podczas pobierania danych o cenach w miastach: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None, None

def scrape_voivodeship(voivodeship_name, url):
    """Pobiera dane dla konkretnego województwa"""
    logger.info(f"Pobieranie danych dla województwa: {voivodeship_name}")
    
    try:
        # Weryfikacja URL przed wysłaniem (bezpieczeństwo)
        if not url.startswith("https://www.reflex.com.pl/"):
            logger.error(f"Niewłaściwy adres URL dla województwa {voivodeship_name}: {url}")
            return None
            
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
    
    # Pobierz datę z krajowej strony
    national_date = scrape_national_date()
    
    # Pobierz dane z województw
    voivodeships_data = {}
    for voivodeship_name, url in VOIVODESHIPS.items():
        voivodeship_data = scrape_voivodeship(voivodeship_name, url)
        if voivodeship_data:
            voivodeships_data[voivodeship_name] = voivodeship_data
    
    # Pobierz dane z miast wojewódzkich
    cities_data, cities_date = scrape_cities()
    
    # Przygotuj wynikowy słownik
    results = {
        "update_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "national_date": national_date,
        "cities_date": cities_date,
        "voivodeships": voivodeships_data,
        "cities": cities_data if cities_data else {}
    }
    
    # Zapisujemy wyniki do pliku JSON
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True)
    
    # Zapisujemy tylko najnowsze dane (bez tworzenia plików historycznych)
    latest_file = os.path.join(output_dir, "latest.json")
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Dane zostały zapisane do pliku {latest_file}")
    
    # Dodatkowe informacje o liczbie pobranych danych
    logger.info(f"Pobrano dane dla {len(voivodeships_data)} województw i {len(cities_data if cities_data else {})} miast")


if __name__ == "__main__":
    main()
