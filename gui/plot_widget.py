import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from datetime import datetime


class CurrencyGraph(ctk.CTkFrame):
    def __init__(self, master, db_manager, api_history, currency_code, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db_manager
        self.api_history = api_history  # To są dane z ostatnich 2 tygodni (niezapisane w bazie)
        self.currency_code = currency_code

        self.fig = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.plot_data()

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def plot_data(self):
        self.ax.clear()

        # --- WARSTWA 1: DANE Z API (Niebieska Linia) ---
        # To pokazuje trend z ostatnich 2 tygodni
        if self.api_history:
            dates_api = [row[0] for row in self.api_history]
            values_api = [row[1] for row in self.api_history]
            self.ax.plot(dates_api, values_api, color='#1f77b4', label='Rynek (2 tyg)', linewidth=2)

        # --- WARSTWA 2: DANE Z BAZY (Czerwone Kropki) ---
        # To pokazuje, kiedy aplikacja została otworzona
        db_data = self.db.get_currency_history(self.currency_code)
        if db_data:
            dates_db = [datetime.strptime(row[0], "%Y-%m-%d") for row in db_data]
            values_db = [row[1] for row in db_data]
            # scatter = kropki
            self.ax.scatter(dates_db, values_db, color='red', s=50, zorder=5, label='Twój zapis')

        # Formatowanie
        self.ax.set_title(f"Kurs: {self.currency_code}")
        self.ax.grid(True, linestyle='--', alpha=0.7)
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))  # Tylko miesiąc-dzień
        self.fig.autofmt_xdate(rotation=45)

        self.ax.legend()  # Pokaż legendę (co jest niebieskie, co czerwone)
