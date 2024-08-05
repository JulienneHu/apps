from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionProfile import main as get_option, calls_or_puts
class FetchStockThread(QThread):
    data_fetched = pyqtSignal(object, object, object)

    def __init__(self, stock_name):
        super().__init__()
        self.stock_name = stock_name

    def run(self):
        try:
            price, price_change, percentage_change = get_realtime_stock_price(self.stock_name)
            if price is None or price_change is None or percentage_change is None:
                raise ValueError("Data is missing")
            price = round(price, 2)
            price_change = round(price_change, 2)
            percentage_change = round(percentage_change, 2)
        except Exception as e:
            price, price_change, percentage_change = 'NA', 'NA', 'NA'
        finally:
            self.data_fetched.emit(price, price_change, percentage_change)


class FetchOptionThread(QThread):
    data_fetched = pyqtSignal(list, list, list)

    def __init__(self, company, date, strike):
        super().__init__()
        self.company = company
        self.date = date
        self.strike = strike

    def run(self):
        prices, open_interests, volumes = get_option(self.company, self.date, self.strike)
        self.data_fetched.emit(prices, open_interests, volumes)  # Emit all data at once

