from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import main as get_realtime_option_price

class FetchStockThread(QThread):
    # Define a signal to send the fetched data back to the main thread
    data_fetched = pyqtSignal(str, str, str)

    def __init__(self, stock_name):
        super().__init__()
        self.stock_name = stock_name

    def run(self):
        try:
            price, price_change, percentage_change = get_realtime_stock_price(self.stock_name)
            if price is not None and price_change is not None and percentage_change is not None:
                self.data_fetched.emit(str(round(price, 2)), str(round(price_change, 2)), str(round(percentage_change, 2)))
            else:
                raise ValueError("Missing data")
        except Exception as e:
            self.data_fetched.emit('NA', 'NA', 'NA')

class FetchOptionThread(QThread):
    data_fetched = pyqtSignal(list)

    def __init__(self, company, date, strike):
        super().__init__()
        self.company = company
        self.date = date
        self.strike = strike

    def run(self):
        try:
            prices = get_realtime_option_price(self.company, self.date, self.strike)
            if not prices or any(p is None for p in prices):
                raise ValueError("Incomplete data")
            self.data_fetched.emit([str(price) for price in prices])
        except Exception as e:
            self.data_fetched.emit(['NA', 'NA'])  # Assume two prices are expected

