class UnitConverter:
    """Klasa bazowa do przeliczania jednostek."""

    def __init__(self):
        self.factors = {}

    def convert(self, value, from_unit, to_unit):
        """Pojedyncze przeliczenie."""
        if from_unit not in self.factors or to_unit not in self.factors:
            return None

        try:
            value = float(value)
        except ValueError:
            return None

        # Wzór: (Wartość * Wspołczynnik_Wejścia) / Współczynnik_Wyjścia
        base_value = value * self.factors[from_unit]
        return base_value / self.factors[to_unit]

    def convert_to_all(self, value, from_unit):
        """Zamienia jedną wartość na WSZYSTKIE inne dostępne w tej kategorii."""
        results = {}
        for unit in self.factors:
            if unit == from_unit:
                results[unit] = value
            else:
                wynik = self.convert(value, from_unit, unit)
                if wynik is not None:
                    # Formatowanie: float dla bardzo małych/dużych liczb, zaokrąglenie dla reszty
                    if wynik != 0 and (abs(wynik) < 0.0001 or abs(wynik) > 1000000):
                        results[unit] = wynik
                    else:
                        results[unit] = round(wynik, 5)
                else:
                    results[unit] = "Błąd"
        return results

    def get_units(self):
        return list(self.factors.keys())


class MassConverter(UnitConverter):
    def __init__(self):
        super().__init__()
        # Baza: Kilogram (kg)
        self.factors = {
            'kg': 1.0,
            'g': 0.001,
            'mg': 0.000001,
            'µg': 0.000000001,
            't_metryczna': 1000.0,
            'funt': 0.453592,  # lb
            'uncja': 0.0283495,  # oz
            'karat': 0.0002,  # ct
            'grain': 0.0000647989,
            'kamien': 6.35029,  # stone
            'slug': 14.5939,
            't_krotka': 907.185,  # USA
            't_dluga': 1016.05  # UK
        }


class SpeedConverter(UnitConverter):
    def __init__(self):
        super().__init__()
        # Baza: Metr na sekundę (m/s)
        self.factors = {
            'm/s': 1.0,
            'km/h': 0.277778,
            'km/s': 1000.0,
            'cm/s': 0.01,
            'mi/h': 0.44704,
            'ft/s': 0.3048,
            'in/s': 0.0254,
            'wezel': 0.514444,
            'mach': 340.3,
            'c': 299792458
        }


class VolumeConverter(UnitConverter):
    def __init__(self):
        super().__init__()
        # Baza: Litr (l)
        self.factors = {
            'l': 1.0,
            'ml': 0.001,
            'cm3': 0.001,
            'dm3': 1.0,
            'm3': 1000.0,
            'galon_usa': 3.78541,
            'barylka_ropy': 158.987,
            'garniec': 4.0
        }


class CurrencyConverter(UnitConverter):
    def __init__(self):
        super().__init__()
        # 1. Kursy "Awaryjne" (sztywne) - gdyby nie było internetu
        self.factors = {
            'PLN': 1.0,
            'USD': 4.0,
            'EUR': 4.5,
            'GBP': 5.0,
            'CHF': 4.5,
            # Dodatki krypto/kruszce (NBP tego nie ma w tabeli A)
            'BTC': 170000.0,
            'zloto_1g': 520.0
        }

    def update_rates(self, new_rates):
        """
        Aktualizuje kursy na podstawie danych z NBP.
        """
        if new_rates:
            print("--- Aktualizacja kursów z NBP ---")
            for currency, rate in new_rates.items():
                # Aktualizujemy tylko te waluty, które przyszły z NBP
                self.factors[currency] = rate


class ForceConverter(UnitConverter):
    def __init__(self):
        super().__init__()
        # Baza: Newton (N)
        self.factors = {
            'N': 1.0,
            'kN': 1000.0,  # Kiloniuton
            'mN': 0.001,  # Miliniuton
            'gramsila': 0.00980665,  # Gram-siła (gf)
            'kgsila': 9.80665,  # Kilogram-siła (kgf)
            'dyna': 0.00001,  # Dyna (dyn)
            'tonasila_ang': 9964.02,  # Tona-siła angielska (Long Ton-force)
            'tonasila_metr': 9806.65,  # Tona-siła metryczna
            'poundal': 0.138255,  # Poundal (pdl)
            'lbf': 4.44822  # Funt-siła (pound-force) - standard w USA/UK

        }
