```markdown
# Monitor Cen Paliw w Polsce

Interaktywna mapa pokazująca ceny paliw dla poszczególnych województw w Polsce. Dane są automatycznie pobierane codziennie o 06:00 CET z serwisu Reflex.

## Funkcje

- Automatyczne codzienne pobieranie cen paliw z serwisu Reflex
- Wizualizacja cen na interaktywnej mapie Polski
- Możliwość przełączania między różnymi rodzajami paliw (PB95, PB98, ON, LPG)
- Zapisywanie historycznych danych w formacie JSON

## Jak używać

Wejdź na stronę GitHub Pages dla tego repozytorium, aby zobaczyć interaktywną mapę cen paliw.

Dane są aktualizowane codziennie o 06:00 CET.

## Struktura projektu

- `index.html` - interaktywna mapa Polski z cenami paliw
- `fuel_prices_scraper.py` - skrypt pobierający dane z serwisu Reflex
- `data/latest.json` - najnowsze dane o cenach paliw
- `data/fuel_prices_YYYY-MM-DD.json` - archiwalne dane z poszczególnych dni

## Technologie

- Python (BeautifulSoup, Requests) - pobieranie danych
- GitHub Actions - automatyczne uruchamianie skryptu
- HTML, CSS, JavaScript - wizualizacja danych na mapie
```
