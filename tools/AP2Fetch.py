from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from realPrice.realStock import get_realtime_stock_price
from realPrice.realOptionProfile import main as get_realtime_option_price
class FetchStockThread(QThread):
    # Define a signal to send the fetched data back to the main thread
    data_fetched = pyqtSignal(object, object, object)

    def __init__(self, stock_name):
        super().__init__()
        self.stock_name = stock_name

    def run(self):
        try:
            price, price_change, percentage_change = get_realtime_stock_price(self.stock_name)
            # Ensure the values are not None and are numeric, else set them to 'NA'
            price = round(price, 2) if price is not None else 'NA'
            price_change = round(price_change, 2) if price_change is not None else 'NA'
            percentage_change = round(percentage_change, 2) if percentage_change is not None else 'NA'
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
            prices, open_interests, volumes = get_realtime_option_price(self.company, self.date, self.strike)
            prices = [str(p) if p is not None else 'NA' for p in prices]
            open_interests = [str(oi) if oi is not None else 'NA' for oi in open_interests]
            volumes = [str(v) if v is not None else 'NA' for v in volumes]
        except Exception as e:
            prices = ['NA', 'NA']  # Adjust depending on the expected number of elements
            open_interests = ['NA', 'NA']
            volumes = ['NA', 'NA']
        finally:
            self.data_fetched.emit(prices, open_interests, volumes)

