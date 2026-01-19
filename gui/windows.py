import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from logic.conversions import MassConverter, SpeedConverter, VolumeConverter, ForceConverter, CurrencyConverter
from data.db_manager import DBManager
from services.nbp_api import NBPClient
from gui.plot_widget import CurrencyGraph
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class UnitConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Super Przelicznik (Wersja Sprawozdawcza)")
        self.geometry("1000x650")

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.db = DBManager()

        # Czyścimy historię na starcie (Nowa Sesja)
        self.db.clear_session_history()

        self.nbp = NBPClient()
        self.api_history_cache = {}
        self.current_rates_cache = {}

        self.converters = {
            "Masa": MassConverter(),
            "Prędkość": SpeedConverter(),
            "Objętość": VolumeConverter(),
            "Siła": ForceConverter(),
            "Waluty": CurrencyConverter()
        }

        # Zmienne do pamiętania CO przeliczamy (Źródło)
        self.current_source_unit = None
        self.current_source_value = None

        self.after(100, self.start_background_download)

        self.is_updating = False
        self.create_layout()
        self.current_converter = None
        self.entries = {}
        self.load_category("Masa")

    def create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.create_sidebar()
        self.create_main_frame()

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1)  # Pusty odstęp na dole

        logo_label = ctk.CTkLabel(self.sidebar_frame, text="Konwerter", font=ctk.CTkFont(size=20, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        row_idx = 1
        for category_name in self.converters.keys():
            btn = ctk.CTkButton(self.sidebar_frame, text=category_name,
                                command=lambda name=category_name: self.load_category(name))
            btn.grid(row=row_idx, column=0, padx=20, pady=10)
            row_idx += 1

        # Przycisk Eksportu na dole paska
        export_btn = ctk.CTkButton(self.sidebar_frame, text="Eksportuj do CSV",
                                   fg_color="orange", hover_color="#d68a00",
                                   command=self.export_csv)
        export_btn.grid(row=row_idx + 1, column=0, padx=20, pady=40)

    def create_main_frame(self):
        self.scrollable_frame = ctk.CTkScrollableFrame(self, label_text="Wybierz kategorię")
        self.scrollable_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.scrollable_frame.grid_columnconfigure(1, weight=1)

    def load_category(self, category_name):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        self.scrollable_frame.configure(label_text=f"Kategoria: {category_name}")
        self.current_converter = self.converters[category_name]
        self.entries = {}
        self.current_category_name = category_name  # Zapamiętujemy nazwę dla bazy

        start_row = 0
        if category_name == "Waluty":
            chart_btn = ctk.CTkButton(self.scrollable_frame, text="Pokaż wykres (Live 2 tyg + Historia)",
                                      fg_color="green", command=self.open_chart_window)
            chart_btn.grid(row=0, column=0, columnspan=3, pady=10, sticky="ew")
            start_row = 1

        units = self.current_converter.get_units()
        for i, unit in enumerate(units):
            row_idx = i + start_row

            # 1. Etykieta
            label = ctk.CTkLabel(self.scrollable_frame, text=unit, width=60, anchor="e")
            label.grid(row=row_idx, column=0, padx=5, pady=5)

            # 2. Pole wpisywania
            entry = ctk.CTkEntry(self.scrollable_frame, placeholder_text="0.0")
            entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
            entry.bind("<KeyRelease>", lambda event, u=unit: self.on_typing(u))
            self.entries[unit] = entry

            # 3. Przycisk Zapisz (Dyskietka)
            save_btn = ctk.CTkButton(self.scrollable_frame, text="Zapisz", width=60,
                                     fg_color="#3a7ebf",
                                     command=lambda u=unit: self.save_single_result(u))
            save_btn.grid(row=row_idx, column=2, padx=5, pady=5)

    def on_typing(self, active_unit):
        if self.is_updating: return
        self.is_updating = True
        try:
            text_value = self.entries[active_unit].get()
            if text_value == "":
                for unit, entry in self.entries.items(): entry.delete(0, "end")
                self.current_source_value = None  # Reset
            else:
                text_value = text_value.replace(",", ".")
                value = float(text_value)

                # ZAPAMIĘTUJEMY CO WPISAŁ UŻYTKOWNIK
                self.current_source_value = value
                self.current_source_unit = active_unit

                results = self.current_converter.convert_to_all(value, active_unit)
                for unit, result in results.items():
                    if unit != active_unit:
                        entry_widget = self.entries[unit]
                        entry_widget.delete(0, "end")
                        entry_widget.insert(0, str(result))
        except ValueError:
            pass
        finally:
            self.is_updating = False

    # Zapisywanie pojedynczego wiersza
    def save_single_result(self, target_unit):
        """Zapisuje wynik z konkretnego wiersza do bazy."""
        # Sprawdzamy, czy w ogóle coś przeliczono
        if self.current_source_value is None:
            messagebox.showwarning("Błąd", "Najpierw wpisz jakąś wartość!")
            return
        # Pobieramy wartość z pola docelowego
        try:
            target_value_str = self.entries[target_unit].get()
            if not target_value_str: return
            target_value = float(target_value_str)

            # Zapis do bazy
            self.db.add_history(
                category=self.current_category_name,
                in_val=self.current_source_value,
                in_unit=self.current_source_unit,
                out_val=target_value,
                out_unit=target_unit
            )
            info_text = f"{self.current_source_value} {self.current_source_unit}  ➜  {target_value} {target_unit}"
            messagebox.showinfo("Zapisano", f"Dodano do sprawozdania:\n\n{info_text}")

        except ValueError:
            messagebox.showerror("Błąd", "Wystąpił błąd przy pobieraniu wartości.")
    # Obsługa przycisku Eksport ---
    def export_csv(self):

        nazwa_pliku = datetime.now().strftime("sprawozdanie_%Y-%m-%d_%H-%M-%S.csv")

        success, message = self.db.export_history_to_csv(nazwa_pliku)

        if success:
            messagebox.showinfo("Eksport", message)
        else:
            messagebox.showerror("Błąd", message)
    def start_background_download(self):
        def task():
            print("[APP] Start pobierania danych...")
            rates = self.nbp.get_current_rates()
            if rates:
                self.converters["Waluty"].update_rates(rates)
                self.current_rates_cache = rates
            kluczowe_waluty = ['EUR', 'USD', 'zloto_1g']
            for waluta in kluczowe_waluty:
                history = self.nbp.get_last_2_weeks_data(waluta)
                self.api_history_cache[waluta] = history
            print("[APP] Dane gotowe.")

        threading.Thread(target=task, daemon=True).start()

    def on_close(self):
        print("[APP] Zamykanie... Zapisywanie walut.")
        if self.current_rates_cache:
            try:
                for kod, kurs in self.current_rates_cache.items():
                    if kod in ['EUR', 'USD', 'zloto_1g', 'BTC']:
                        self.db.add_currency_rate(kod, kurs)
            except Exception as e:
                print(e)
        self.destroy()

    def open_chart_window(self):
        chart_window = ctk.CTkToplevel(self)
        chart_window.title("Historia Walut")
        chart_window.geometry("800x600")
        tabview = ctk.CTkTabview(chart_window)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        waluty_do_wykresu = ["EUR", "USD", "zloto_1g"]
        for waluta in waluty_do_wykresu:
            tabview.add(waluta)
            api_data = self.api_history_cache.get(waluta, [])
            graph = CurrencyGraph(master=tabview.tab(waluta), db_manager=self.db,
                                  api_history=api_data, currency_code=waluta)
            graph.pack(fill="both", expand=True)
