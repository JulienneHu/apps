from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionIndex import main as get_realtime_option_price
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
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
        try:
            option_data = get_realtime_option_price(self.company, self.date, self.strike)
            if option_data is None or len(option_data[0]) < 2:
                raise ValueError("Option data is missing or incomplete")
            prices, open_interests, volumes = option_data
        except Exception as e:
            prices, open_interests, volumes = ['NA', 'NA'], ['NA', 'NA'], ['NA', 'NA']
        finally:
            self.data_fetched.emit(prices, open_interests, volumes)

