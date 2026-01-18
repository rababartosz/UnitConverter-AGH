import requests
import sqlite3
from datetime import datetime, timedelta

# Konfiguracja
DB_NAME = "conversions.db"
DAYS_BACK = 7  # Pobieramy dane z ostatniego tygodnia


def get_date_range():
    """Zwraca datę początkową i końcową w formacie YYYY-MM-DD."""
    today = datetime.now()
    start_date = today - timedelta(days=DAYS_BACK)
    return start_date.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d")


def save_to_db(cursor, date, code, rate):
    """Zapisuje rekord do bazy, jeśli taki jeszcze nie istnieje."""
    # Sprawdzamy, czy wpis już jest, żeby nie robić dubli
    cursor.execute("SELECT id FROM currency_rates WHERE date=? AND currency=?", (date, code))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO currency_rates (date, currency, rate)
            VALUES (?, ?, ?)
        """, (date, code, rate))
        print(f"  [+] Zapisano: {code} z dnia {date} = {rate}")
    else:
        print(f"  [.] Pominięto: {code} z dnia {date} (już istnieje)")


def fetch_currencies(start, end, codes):
    """Pobiera historię dla zwykłych walut (USD, EUR)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    for code in codes:
        print(f"\n--- Pobieranie historii dla {code} ---")
        url = f"http://api.nbp.pl/api/exchangerates/rates/a/{code}/{start}/{end}/?format=json"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                # NBP zwraca listę stawek w polu 'rates'
                for item in data['rates']:
                    date = item['effectiveDate']
                    rate = item['mid']
                    save_to_db(cursor, date, code, rate)
            else:
                print(f"Błąd API NBP dla {code}: {response.status_code}")
        except Exception as e:
            print(f"Wyjątek: {e}")

    conn.commit()
    conn.close()


def fetch_gold(start, end):
    """Pobiera historię cen złota (inny endpoint w API)."""
    print(f"\n--- Pobieranie historii dla ZŁOTA ---")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    url = f"http://api.nbp.pl/api/cenyzlota/{start}/{end}/?format=json"

    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Dla złota format to lista obiektów [{'data': '...', 'cena': ...}]
            for item in data:
                date = item['data']
                rate = item['cena']
                save_to_db(cursor, date, "zloto_1g", rate)
        else:
            print(f"Błąd API NBP dla Złota: {response.status_code}")
    except Exception as e:
        print(f"Wyjątek: {e}")

    conn.commit()
    conn.close()


if __name__ == "__main__":
    print("URUCHAMIANIE SKRYPTU UZUPEŁNIANIA HISTORII...")
    start_date, end_date = get_date_range()
    print(f"Zakres dat: {start_date} do {end_date}")

    # 1. Pobierz waluty
    fetch_currencies(start_date, end_date, ["EUR", "USD", "CHF", "GBP"])

    # 2. Pobierz złoto
    fetch_gold(start_date, end_date)

    print("\nGOTOWE! Dane zapisane w bazie conversions.db.")
    print("Teraz uruchom 'main.py' i sprawdź wykresy.")