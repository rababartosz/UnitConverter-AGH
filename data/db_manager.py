import sqlite3
import csv  
import os
from datetime import datetime

class DBManager:
    def __init__(self, db_name="conversions.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Tabela historii (sesyjna)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                input_value REAL,
                input_unit TEXT,
                output_value REAL,
                output_unit TEXT
            )
        """)
        # Tabela walut (długoterminowa - tej nie czyścimy)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS currency_rates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                currency TEXT,
                rate REAL
            )
        """)
        self.conn.commit()

    # --- FUNKCJA 1: Czyści historię (Reset Sesji) ---
    def clear_session_history(self):
        """Usuwa wszystkie wpisy z tabeli historii."""
        self.cursor.execute("DELETE FROM history")
        self.conn.commit()
        print("[BAZA] Historia sesji wyczyszczona.")

    # --- FUNKCJA 2: Eksport do CSV ---
    def export_history_to_csv(self, filename):
        """Eksportuje zawartość tabeli history do pliku CSV."""

        self.cursor.execute("SELECT category, input_value, input_unit, output_value, output_unit FROM history")
        rows = self.cursor.fetchall()

        if not rows:
            return False, "Brak danych do zapisania."

        try:
            # 2.  encoding='utf-8-sig' naprawia krzaki w Excelu (dodaje BOM)
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=';')

                writer.writerow(["Kategoria", "Wartość Wejściowa", "Jednostka We", "Wynik", "Jednostka Wy"])

                writer.writerows(rows)

            return True, f"Zapisano w pliku:\n{filename}"
        except Exception as e:
            return False, str(e)

    def add_history(self, category, in_val, in_unit, out_val, out_unit):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO history (date, category, input_value, input_unit, output_value, output_unit)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (date, category, in_val, in_unit, out_val, out_unit))
        self.conn.commit()
        print(f"[BAZA] Dodano do sprawozdania: {in_val} {in_unit} -> {out_val} {out_unit}")

    def add_currency_rate(self, currency, rate):
        date = datetime.now().strftime("%Y-%m-%d")
        check = self.cursor.execute("SELECT id FROM currency_rates WHERE date=? AND currency=?", (date, currency)).fetchone()
        if not check:
            self.cursor.execute("INSERT INTO currency_rates (date, currency, rate) VALUES (?, ?, ?)", (date, currency, rate))
            self.conn.commit()

    def get_currency_history(self, currency):
        self.cursor.execute("SELECT date, rate FROM currency_rates WHERE currency = ? ORDER BY date ASC", (currency,))
        return self.cursor.fetchall()

    def close(self):

        self.conn.close()
