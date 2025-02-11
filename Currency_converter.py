import requests
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

# Посилання на API для отримання курсу валют
API_URL = "https://api.exchangerate-api.com/v4/latest/"

# Список доступних валют
CURRENCY_CODES = ["USD", "EUR", "UAH", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY"]

class CurrencyConverter:
    def __init__(self):
        """Ініціалізація вікна та підключення до бази даних"""
        self.db_connect()
        self.create_gui()
        self.load_last_conversion()
    
    def db_connect(self):
        """Підключення до бази даних та створення таблиці"""
        self.conn = sqlite3.connect("currency_history.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS conversions (
                                id INTEGER PRIMARY KEY AUTOINCREMENT,
                                from_currency TEXT,
                                to_currency TEXT,
                                amount REAL,
                                converted_amount REAL,
                                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
        self.conn.commit()
    
    def get_exchange_rate(self, from_currency):
        """Отримання курсу валют із API"""
        try:
            response = requests.get(f"{API_URL}{from_currency}")
            response.raise_for_status()
            return response.json().get("rates", {})
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Error", f"Не вдалося отримати курс валют: {e}")
            return {}
    
    def convert_currency(self):
        """Конвертація валюти та збереження у базу"""
        from_currency = self.from_currency_var.get()
        to_currency = self.to_currency_var.get()
        try:
            amount = float(self.amount_var.get())
        except ValueError:
            messagebox.showerror("Error", "Введіть коректну суму")
            return
        
        rates = self.get_exchange_rate(from_currency)
        if to_currency in rates:
            converted_amount = amount * rates[to_currency]
            self.result_var.set(f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}")
            self.cursor.execute('''INSERT INTO conversions (from_currency, to_currency, amount, converted_amount)
                                   VALUES (?, ?, ?, ?)''', (from_currency, to_currency, amount, converted_amount))
            self.conn.commit()
            self.load_conversion_history()
        else:
            messagebox.showerror("Error", "Помилка отримання курсу валют.")
    
    def load_last_conversion(self):
        """Завантаження останнього конвертування"""
        self.cursor.execute("SELECT from_currency, to_currency, amount FROM conversions ORDER BY timestamp DESC LIMIT 1")
        last_conversion = self.cursor.fetchone()
        if last_conversion:
            self.from_currency_var.set(last_conversion[0])
            self.to_currency_var.set(last_conversion[1])
            self.amount_var.set(str(last_conversion[2]))
    
    def load_conversion_history(self):
        """Завантаження історії конвертацій з можливістю нескінченного прокручування"""
        self.history_list.delete(0, tk.END)
        self.cursor.execute("SELECT from_currency, to_currency, amount, converted_amount, timestamp FROM conversions ORDER BY timestamp DESC")
        for row in self.cursor.fetchall():
            self.history_list.insert(tk.END, f"{row[4]}: {row[2]} {row[0]} → {row[3]:.2f} {row[1]}")
    
    def create_gui(self):
        """Створення графічного інтерфейсу"""
        self.window = tk.Tk()
        self.window.title("Currency Converter")
        self.window.resizable(False, False)
        
        tk.Label(self.window, text="From Currency:").grid(row=0, column=0)
        self.from_currency_var = tk.StringVar()
        ttk.Combobox(self.window, textvariable=self.from_currency_var, values=CURRENCY_CODES, state="readonly").grid(row=0, column=1)
        
        tk.Label(self.window, text="To Currency:").grid(row=1, column=0)
        self.to_currency_var = tk.StringVar()
        ttk.Combobox(self.window, textvariable=self.to_currency_var, values=CURRENCY_CODES, state="readonly").grid(row=1, column=1)
        
        tk.Label(self.window, text="Amount:").grid(row=2, column=0)
        self.amount_var = tk.StringVar()
        ttk.Entry(self.window, textvariable=self.amount_var).grid(row=2, column=1)
        
        ttk.Button(self.window, text="Convert", command=self.convert_currency).grid(row=3, column=0, columnspan=2)
        
        self.result_var = tk.StringVar()
        tk.Label(self.window, textvariable=self.result_var).grid(row=4, column=0, columnspan=2)
        
        tk.Label(self.window, text="Conversion History:").grid(row=5, column=0, columnspan=2)
        
        # Створення віджета Listbox з прокручуванням
        self.history_frame = tk.Frame(self.window)
        self.history_frame.grid(row=6, column=0, columnspan=2)
        
        self.history_list = tk.Listbox(self.history_frame, height=10, width=50)
        self.scrollbar = tk.Scrollbar(self.history_frame, orient=tk.VERTICAL, command=self.history_list.yview)
        self.history_list.config(yscrollcommand=self.scrollbar.set)
        
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.load_conversion_history()
        
        self.window.mainloop()

if __name__ == "__main__":
    CurrencyConverter()
