import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSlider, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                             QGridLayout, QFrame, QSizePolicy, QDateEdit)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QDate)
from PyQt5.QtGui import QFont
from datetime import date, datetime
from scipy.stats import norm
import numpy as np
import pytz
import holidays
import logging

from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import get_realtime_option_price, calls_or_puts
from assets.stylesheet import stylesheet
from assets.creations import create_input_field, create_date_field
from assets.BsCal import BlackScholes
from assets.BsFetch import FetchStockThread, FetchOptionThread


class OptionStrategyVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet(stylesheet)

    def initUI(self):
        self.setWindowTitle("Black-Scholes Option Pricing Model")
        self.setGeometry(200, 100, 1000, 768)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)
        control_panel.setMaximumWidth(800)

        input_layout_1 = QHBoxLayout()
        self.symbol_input = create_input_field('Symbol', 'AAPL')
        curr = datetime.now().strftime('%Y-%m-%d-%H-%M') 
        self.today_date = create_input_field('Today', curr)
        self.date_input = create_date_field('Maturity', '2024-07-19')
        self.x_input = create_input_field('Strike', '210')
        input_layout_1.addWidget(self.symbol_input)
        input_layout_1.addWidget(self.today_date)
        input_layout_1.addWidget(self.date_input)
        input_layout_1.addWidget(self.x_input)
        
        input_layout_2 = QHBoxLayout()
        self.interest_input = create_input_field('r', '0.07')
        self.volatility_input = create_input_field('σ', '0.2')
        input_layout_2.addWidget(self.interest_input)
        input_layout_2.addWidget(self.volatility_input)

        self.fetch_data_button = QPushButton('Fetch Data / Refresh', control_panel)
        self.fetch_data_button.clicked.connect(self.fetch_data)
        
        input_layout_4 = QHBoxLayout()
        self.stock_price_input = create_input_field('SPrice', '210', False)
        self.price_change_input = create_input_field('Real', '0', False)
        self.percent_change_input = create_input_field('Pct', '0', False)
        input_layout_4.addWidget(self.stock_price_input)
        input_layout_4.addWidget(self.price_change_input)
        input_layout_4.addWidget(self.percent_change_input)
        
        input_layout_5 = QHBoxLayout()
        self.call_premium_input = create_input_field('MarketC', '9.8', False)
        self.call_ask_input = create_input_field('AskC', '0.00', False)
        self.call_bid_input = create_input_field('BidC', '0.00', False)    
        input_layout_5.addWidget(self.call_premium_input)
        input_layout_5.addWidget(self.call_ask_input)
        input_layout_5.addWidget(self.call_bid_input)

        input_layout_6 = QHBoxLayout()
        self.put_premium_input = create_input_field('MarketP', '14.5', False) 
        self.put_ask_input = create_input_field('AskP', '0.00', False)
        self.put_bid_input = create_input_field('BidP', '0.00', False)
        input_layout_6.addWidget(self.put_premium_input)
        input_layout_6.addWidget(self.put_ask_input)
        input_layout_6.addWidget(self.put_bid_input)
        
        input_layout_7 = QHBoxLayout()
        self.time_input = create_input_field('T', '50', False)
        self.impvC_input = create_input_field('C_IMPV', '0.00', False)
        self.impvP_input = create_input_field('P_IMPV', '0.00', False)
        input_layout_7.addWidget(self.time_input)
        input_layout_7.addWidget(self.impvC_input)
        input_layout_7.addWidget(self.impvP_input)

        input_layout_8 = QHBoxLayout()
        self.call_price_input = create_input_field('Call Price', '0.00', False)
        self.put_price_input = create_input_field('Put Price', '0.00', False)
        input_layout_8.addWidget(self.call_price_input)
        input_layout_8.addWidget(self.put_price_input)
        
        input_layout_9 = QHBoxLayout()
        self.call_delta_input = create_input_field('Call Delta', '0.00', False)
        self.put_delta_input = create_input_field('Put Delta', '0.00', False)
        input_layout_9.addWidget(self.call_delta_input)
        input_layout_9.addWidget(self.put_delta_input)

        control_layout.addLayout(input_layout_1)
        control_layout.addLayout(input_layout_2)
        control_layout.addWidget(self.fetch_data_button)
        control_layout.addLayout(input_layout_4)
        control_layout.addLayout(input_layout_5)
        control_layout.addLayout(input_layout_6)
        control_layout.addLayout(input_layout_7)
        control_layout.addLayout(input_layout_8)
        control_layout.addLayout(input_layout_9)
        grid_layout.addWidget(control_panel, 0, 0)
        self.show()

    # def create_input_field(self, label, default_value, editable=True):
    #     container = QWidget()
    #     layout = QHBoxLayout()
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(5)
        
    #     lbl = QLabel(label)
    #     font = QFont()
    #     font.setPointSize(32)
    #     lbl.setFont(font)
    #     lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
    #     input_field = QLineEdit(default_value)
    #     input_field.setAlignment(Qt.AlignCenter)
    #     input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
    #     input_field.setReadOnly(not editable)
        
    #     layout.addWidget(lbl)
    #     layout.addWidget(input_field)
        
    #     layout.setStretch(0, 0)
    #     layout.setStretch(1, 1)
        
    #     container.setLayout(layout)
    #     container.input_field = input_field
    #     return container

    # def create_date_field(self, label, default_value):
    #     container = QWidget()
    #     layout = QHBoxLayout()
    #     layout.setContentsMargins(0, 0, 0, 0)
    #     layout.setSpacing(5)
        
    #     lbl = QLabel(label)
    #     font = QFont()
    #     font.setPointSize(32)
    #     lbl.setFont(font)
    #     lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
    #     date_input = QDateEdit(QDate.fromString(default_value, "yyyy-MM-dd"))
    #     date_input.setCalendarPopup(True)
    #     date_input.setDisplayFormat("yyyy-MM-dd")
    #     date_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
    #     layout.addWidget(lbl)
    #     layout.addWidget(date_input)
        
    #     layout.setStretch(0, 0)
    #     layout.setStretch(1, 1)
        
    #     container.setLayout(layout)
    #     container.input_field = date_input
    #     return container
    
    def fetch_data(self):
        company = self.symbol_input.input_field.text()
        date = self.date_input.input_field.text()
        strike = float(self.x_input.input_field.text())

        self.fetch_stock_price(company)

        self.fetch_stock_price(company)

        stock_price = self.stock_price_input.input_field.text()
        if stock_price != 'NA':
            stock_price = float(stock_price)

        self.update_option_premiums()
        
        today_date = self.today_date.input_field.text()
        today_date = today_date[:10]
        maturity_date = self.date_input.input_field.text()
        T = QDate.fromString(today_date, "yyyy-MM-dd").daysTo(QDate.fromString(maturity_date, "yyyy-MM-dd"))
        if datetime.now().hour >= 14:
            T -= 1
        self.time_input.input_field.setText(str(T))
        
        call_premium = None
        put_premium = None
        call_ask = None
        call_bid = None
        put_ask = None
        put_bid = None
        call_price = None
        put_price = None
        call_delta = None
        put_delta = None
        impvC = None
        impvP = None
        
        if stock_price and self.call_premium_input.input_field.text() != 'NA' and self.put_premium_input.input_field.text() != 'NA':
            r = float(self.interest_input.input_field.text())
            sigma = float(self.volatility_input.input_field.text())
            T = T / 365.0
           
            call_premium = float(self.call_premium_input.input_field.text())
            put_premium = float(self.put_premium_input.input_field.text())
            
            impvC = BlackScholes().blsimpv('c', stock_price, strike, T, r, call_premium, sigma)
            impvP = BlackScholes().blsimpv('p', stock_price, strike, T, r, put_premium, sigma)

            self.impvC_input.input_field.setText("{:.2f}".format(impvC) if impvC is not None else "NA")
            self.impvP_input.input_field.setText("{:.2f}".format(impvP) if impvP is not None else "NA")

            call_price = BlackScholes().blsprice('c', stock_price, strike, T, r, sigma)
            put_price = BlackScholes().blsprice('p', stock_price, strike, T, r, sigma)
            
            call_ask = float(self.call_ask_input.input_field.text())
            call_bid = float(self.call_bid_input.input_field.text())
            put_ask = float(self.put_ask_input.input_field.text())
            put_bid = float(self.put_bid_input.input_field.text())

            if call_price > call_ask:
                self.call_price_input.input_field.setStyleSheet("color: #007560;")
            elif call_price < call_bid:
                self.call_price_input.input_field.setStyleSheet("color: #bd1414;")
            else:
                self.call_price_input.input_field.setStyleSheet("color: black;")

            if put_price > put_ask:
                self.put_price_input.input_field.setStyleSheet("color: #007560;")
            elif put_price < put_bid:
                self.put_price_input.input_field.setStyleSheet("color: #bd1414;")
            else:
                self.put_price_input.input_field.setStyleSheet("color: black;")
                
            self.call_price_input.input_field.setText("{:.2f}".format(call_price))
            self.put_price_input.input_field.setText("{:.2f}".format(put_price))

            call_delta = BlackScholes().blsdelta('c', stock_price, strike, T, r, sigma)
            put_delta = BlackScholes().blsdelta('p', stock_price, strike, T, r, sigma)
            self.call_delta_input.input_field.setText("{:.2f}".format(call_delta))
            self.put_delta_input.input_field.setText("{:.2f}".format(put_delta))
        else:
            self.impvC_input.input_field.setText("NA")
            self.impvP_input.input_field.setText("NA")
            self.call_price_input.input_field.setText("NA")
            self.put_price_input.input_field.setText("NA")
            self.call_delta_input.input_field.setText("NA")
            self.put_delta_input.input_field.setText("NA")
        
    def fetch_stock_price(self, company):
        if hasattr(self, 'stock_fetch_thread'):
            self.stock_fetch_thread.quit()
            self.stock_fetch_thread.wait()

        self.stock_fetch_thread = FetchStockThread(company)
        self.stock_fetch_thread.data_fetched.connect(self.update_stock_price_input)
        self.stock_fetch_thread.start()

    def update_stock_price_input(self, price, price_change, percent_change):
        price_str = str(price) if price is not None else "NA"
        price_change_str ="$" + str(price_change) if price_change is not None else "NA"
        percent_change_str = str(percent_change) + '%' if percent_change is not None else "NA"

        self.stock_price_input.input_field.setText(price_str)
        self.price_change_input.input_field.setText(price_change_str)
        self.percent_change_input.input_field.setText(percent_change_str)

        if price_change and price_change > 0:
            color = "#007560"
        elif price_change and price_change < 0:
            color = "#bd1414"
        else:
            color = "black"

        self.stock_price_input.input_field.setStyleSheet(f"color: {color};")
        self.price_change_input.input_field.setStyleSheet(f"color: {color};")
        self.percent_change_input.input_field.setStyleSheet(f"color: {color};")
        
    def update_option_premiums(self):
        company = self.symbol_input.input_field.text()
        date = self.date_input.input_field.text()
        strike = float(self.x_input.input_field.text())

        if hasattr(self, 'option_fetch_thread'):
            self.option_fetch_thread.terminate()

        self.option_fetch_thread = FetchOptionThread(company, date, strike)
        self.option_fetch_thread.data_fetched.connect(self.fill_premium_inputs)
        self.option_fetch_thread.start()

    def fill_premium_inputs(self, prices, ask_prices, bid_prices):
        call_premium_str = str(prices[0]) if prices and prices[0] is not None else "NA"
        put_premium_str = str(prices[1]) if prices and prices[1] is not None else "NA"
        call_ask_str = str(ask_prices[0]) if ask_prices and ask_prices[0] is not None else "NA"
        put_ask_str = str(ask_prices[1]) if ask_prices and ask_prices[1] is not None else "NA"
        call_bid_str = str(bid_prices[0]) if bid_prices and bid_prices[0] is not None else "NA"
        put_bid_str = str(bid_prices[1]) if bid_prices and bid_prices[1] is not None else "NA"
        
        self.call_premium_input.input_field.setText(call_premium_str)
        self.put_premium_input.input_field.setText(put_premium_str)
        self.call_ask_input.input_field.setText(call_ask_str)
        self.put_ask_input.input_field.setText(put_ask_str)
        self.call_bid_input.input_field.setText(call_bid_str)
        self.put_bid_input.input_field.setText(put_bid_str)
        
        if not prices:
            self.impvC_input.input_field.setText("NA")
            self.impvP_input.input_field.setText("NA")
            self.call_price_input.input_field.setText("NA")
            self.put_price_input.input_field.setText("NA")
            self.call_delta_input.input_field.setText("NA")
            self.put_delta_input.input_field.setText("NA")
            return

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionStrategyVisualizer()
    sys.exit(app.exec_())
