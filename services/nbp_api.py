import requests
from datetime import datetime, timedelta


class NBPClient:
    def __init__(self):
        self.url_base = "http://api.nbp.pl/api/exchangerates/rates/a/"
        self.url_gold = "http://api.nbp.pl/api/cenyzlota/"

    def get_last_2_weeks_data(self, currency_code):
        """
        Pobiera historię z ostatnich 14 dni dla wykresu.
        Zwraca listę krotek: [(datetime, value), ...]
        """
        days_back = 14
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        try:
            # 1. Obsługa Złota (ma inny adres API)
            if currency_code == 'zloto_1g':
                url = f"{self.url_gold}{start_str}/{end_str}/?format=json"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [(datetime.strptime(x['data'], "%Y-%m-%d"), x['cena']) for x in data]

            # 2. Obsługa Walut (EUR, USD...)
            else:
                url = f"{self.url_base}{currency_code}/{start_str}/{end_str}/?format=json"
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    return [(datetime.strptime(x['effectiveDate'], "%Y-%m-%d"), x['mid']) for x in data['rates']]

            return []  # Jeśli API nic nie zwróci
        except Exception as e:
            print(f"Błąd pobierania historii API: {e}")
            return []

    def get_current_rates(self):
        url_curr = "http://api.nbp.pl/api/exchangerates/tables/a/?format=json"
        url_gold = "http://api.nbp.pl/api/cenyzlota/?format=json"
        rates_dict = {}
        try:
            r = requests.get(url_curr, timeout=2).json()
            for i in r[0]['rates']: rates_dict[i['code']] = i['mid']
            rates_dict['PLN'] = 1.0
        except:
            pass
        try:
            g = requests.get(url_gold, timeout=2).json()
            rates_dict['zloto_1g'] = g[0]['cena']
        except:
            pass

        return rates_dict
