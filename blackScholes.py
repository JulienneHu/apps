import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSlider, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                             QGridLayout, QFrame, QSizePolicy, QDateEdit)  # Added QSizePolicy here
from PyQt5.QtCore import (Qt, QThread, pyqtSignal, QDate)
from PyQt5.QtGui import QFont
from datetime import date, datetime
from scipy.stats import norm
import numpy as np

from realPrice.realStock import get_realtime_stock_price
from realPrice.realOption import main as get_realtime_option_price

import QuantLib as ql


class BlackScholes:
    
    def __init__(self):
        self.calendar = ql.NullCalendar()
        self.day_count = ql.Actual365Fixed()

    def blsprice(self, cp_flag, S, X, T, r, v):
        # Convert input parameters to QuantLib objects
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)

        # Define the option type
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put

        # Define the payoff and exercise
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)

        # Create the European option
        european_option = ql.VanillaOption(payoff, exercise)

        # Set up the Black-Scholes-Merton process
        underlying = ql.SimpleQuote(S)
        volatility = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)

        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            ql.BlackVolTermStructureHandle(volatility)
        )

        # Price the option
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        price = european_option.NPV()
        return price

    def blsdelta(self, cp_flag, S, X, T, r, v):
        # Convert input parameters to QuantLib objects
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)

        # Define the option type
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put

        # Define the payoff and exercise
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)

        # Create the European option
        european_option = ql.VanillaOption(payoff, exercise)

        # Set up the Black-Scholes-Merton process
        underlying = ql.SimpleQuote(S)
        volatility = ql.BlackConstantVol(evaluation_date, self.calendar, v, self.day_count)
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)

        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            ql.BlackVolTermStructureHandle(volatility)
        )

        # Price the option and get delta
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))
        delta = european_option.delta()
        return delta

    def blsimpv(self, cp_flag, S, X, T, r, C, sigma_guess=0.2, tol=1e-6, max_iterations=100):
        # Convert input parameters to QuantLib objects
        evaluation_date = ql.Settings.instance().evaluationDate
        maturity_date = evaluation_date + int(T * 365)

        # Define the option type
        option_type = ql.Option.Call if cp_flag == 'c' else ql.Option.Put

        # Define the payoff and exercise
        payoff = ql.PlainVanillaPayoff(option_type, X)
        exercise = ql.EuropeanExercise(maturity_date)

        # Create the European option
        european_option = ql.VanillaOption(payoff, exercise)

        # Set up the Black-Scholes-Merton process with an initial guess for volatility
        underlying = ql.SimpleQuote(S)
        volatility = ql.SimpleQuote(sigma_guess)
        volatility_handle = ql.BlackVolTermStructureHandle(
            ql.BlackConstantVol(evaluation_date, self.calendar, ql.QuoteHandle(volatility), self.day_count)
        )
        dividend_yield = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(0.0)), self.day_count)
        risk_free_rate = ql.FlatForward(evaluation_date, ql.QuoteHandle(ql.SimpleQuote(r)), self.day_count)

        bsm_process = ql.BlackScholesMertonProcess(
            ql.QuoteHandle(underlying),
            ql.YieldTermStructureHandle(dividend_yield),
            ql.YieldTermStructureHandle(risk_free_rate),
            volatility_handle
        )

        # Set the pricing engine
        european_option.setPricingEngine(ql.AnalyticEuropeanEngine(bsm_process))

        # Implied volatility calculation
        try:
            implied_vol = european_option.impliedVolatility(C, bsm_process, tol, max_iterations)
        except RuntimeError:
            implied_vol = float('nan')
        
        return implied_vol

class FetchStockThread(QThread):
    # Define a signal to send the fetched data back to the main thread
    data_fetched = pyqtSignal(float, float, float)

    def __init__(self, stock_name):
        super().__init__()
        self.stock_name = stock_name

    def run(self):
        price, price_change, percentage_change = get_realtime_stock_price(self.stock_name)
        self.data_fetched.emit(round(price, 2), round(price_change, 2), round(percentage_change, 2))


class FetchOptionThread(QThread):
    data_fetched = pyqtSignal(list)

    def __init__(self, company, date, strike):
        super().__init__()
        self.company = company
        self.date = date
        self.strike = strike

    def run(self):
        prices = get_realtime_option_price(self.company, self.date, self.strike)
        self.data_fetched.emit(prices)


stylesheet = """
QWidget {
    font-family: Verdana, Arial, Helvetica, sans-serif;
    font-size: 14px;
    color: #333;
}

QComboBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    background: white;
    text-align: center; /* Center text in QComboBox */
    height: 32px;
    padding: 24px;
    font-size: 22px;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid; /* just a single line */
    border-top-right-radius: 3px; /* same radius as the QComboBox */
    border-bottom-right-radius: 3px;
}

QComboBox QAbstractItemView {
    selection-background-color: #ccc;
    text-align: center; /* Center text in the dropdown items */
}

QLineEdit {
    border: 1px solid #ccc;
    padding: 5px;
    border-radius: 4px;
    background: white;
    font-size: 14px;
    text-align: center;
}

QLabel {
    font-size: 14px;
}

QSlider::groove:horizontal {
    border: 1px solid #999;
    height: 8px;
    border-radius: 4px;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #eee, stop:1 #ddd);
}

QSlider::handle:horizontal {
    background: white;
    border: 1px solid #ccc;
    width: 18px;
    margin: -2px 0;
    border-radius: 3px;
}

QPushButton {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 10px;
    background: #eee;
}

QPushButton:pressed {
    background: #ddd;
    font-size: 16px;
}

QPushButton:hover {
    border-color: #bbb;
}
"""


class OptionStrategyVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet(stylesheet)

    def initUI(self):
        
        self.setWindowTitle("Black-Scholes Option Pricing Model")
        self.setGeometry(200, 100, 1000, 768)  # Set to the image width and height

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        # Left-side controls
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)

        # Adjustments for control panel layout and dimensions
        control_panel.setMaximumWidth(800)  # Adjust this value to make the control panel narrower



        # Input Fields
        # Adjust the layout for the input fields to be in lines
        input_layout_1 = QHBoxLayout()
        self.symbol_input = self.create_input_field('Symbol', 'AAPL')  # Default symbol
        # curr show in  YYYY-MM-DD-HH-MM format
        curr = datetime.now().strftime('%Y-%m-%d-%H-%M')
        today_date = date.today().isoformat()  
        self.today_date = self.create_input_field('Today', curr)  # Default date
        self.date_input = self.create_date_field('Maturity', '2024-05-17')  # Default date
        self.x_input = self.create_input_field('Strike', '150')
        input_layout_1.addWidget(self.symbol_input)
        input_layout_1.addWidget(self.today_date)
        input_layout_1.addWidget(self.date_input)
        input_layout_1.addWidget(self.x_input)
        
        input_layout_2 = QHBoxLayout()
        self.interest_input = self.create_input_field('r', '0.07')  # Default date
        self.volatility_input = self.create_input_field('σ', '0.2')  # Default date
        input_layout_2.addWidget(self.interest_input)
        input_layout_2.addWidget(self.volatility_input)

        self.fetch_data_button = QPushButton('Fetch Data / Refresh', control_panel)
        self.fetch_data_button.clicked.connect(self.fetch_data)  # Connect button click to the fetch_data method
        
        input_layout_4 = QHBoxLayout()
        self.stock_price_input = self.create_input_field('SPrice', '150', False)
        self.price_change_input = self.create_input_field('Real', '0', False)
        self.percent_change_input = self.create_input_field('Pct', '0', False)
        input_layout_4.addWidget(self.stock_price_input)   
        input_layout_4.addWidget(self.price_change_input)
        input_layout_4.addWidget(self.percent_change_input)
        
        input_layout_5 = QHBoxLayout()
        self.call_premium_input = self.create_input_field('MarketC', '9.8', False)
        self.put_premium_input = self.create_input_field('MarketP', '14.5', False)     
        input_layout_5.addWidget(self.call_premium_input)
        input_layout_5.addWidget(self.put_premium_input)

        input_layout_6 = QHBoxLayout()
        self.time_input = self.create_input_field('T', '50', False)
        self.impvC_input = self.create_input_field('C_IMPV', '0.00', False)
        self.impvP_input = self.create_input_field('P_IMPV', '0.00', False)
        input_layout_6.addWidget(self.time_input)
        input_layout_6.addWidget(self.impvC_input)
        input_layout_6.addWidget(self.impvP_input)

        input_layout_7 = QHBoxLayout()
        self.call_price_input = self.create_input_field('Call Price', '0.00', False)
        self.put_price_input = self.create_input_field('Put Price', '0.00', False)
        input_layout_7.addWidget(self.call_price_input)
        input_layout_7.addWidget(self.put_price_input)
        
        input_layout_8 = QHBoxLayout()
        self.call_delta_input = self.create_input_field('Call Delta', '0.00', False)
        self.put_delta_input = self.create_input_field('Put Delta', '0.00', False)
        input_layout_8.addWidget(self.call_delta_input)
        input_layout_8.addWidget(self.put_delta_input)

        # Add input layouts to the main control layout
        control_layout.addLayout(input_layout_1)
        control_layout.addLayout(input_layout_2)
        control_layout.addWidget(self.fetch_data_button)
        control_layout.addLayout(input_layout_4)
        control_layout.addLayout(input_layout_5)
        control_layout.addLayout(input_layout_6)
        control_layout.addLayout(input_layout_7)
        control_layout.addLayout(input_layout_8)
        # Add control panel to grid
        grid_layout.addWidget(control_panel, 0, 0)


        # Connect signals to update method
        

        # Show the window
        self.show()


    def create_input_field(self, label, default_value, editable=True):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        layout.setSpacing(5)
        
        lbl = QLabel(label)
        font = QFont()  # Create a QFont object
        font.setPointSize(32)  # Set the font size. Adjust the number as needed.
        lbl.setFont(font)  # Apply the font to the label
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        input_field = QLineEdit(default_value)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure input field can expand
        input_field.setReadOnly(not editable) 
        
        layout.addWidget(lbl)
        layout.addWidget(input_field)
        
        layout.setStretch(0, 0)  # No additional stretch for label
        layout.setStretch(1, 1)  # Allow input field to expand
        
        container.setLayout(layout)
        container.input_field = input_field
        return container
    def create_date_field(self, label, default_value):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        layout.setSpacing(5)
        
        lbl = QLabel(label)
        font = QFont()  # Create a QFont object
        font.setPointSize(32)  # Set the font size. Adjust the number as needed.
        lbl.setFont(font)  # Apply the font to the label
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        # Create a QDateEdit for date selection
        date_input = QDateEdit(QDate.fromString(default_value, "yyyy-MM-dd"))
        date_input.setCalendarPopup(True)
        date_input.setDisplayFormat("yyyy-MM-dd") 
        date_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        layout.addWidget(lbl)
        layout.addWidget(date_input)
        
        layout.setStretch(0, 0)  # No additional stretch for label
        layout.setStretch(1, 1)  # Allow input field to expand
        
        container.setLayout(layout)
        container.input_field = date_input
        return container

    def fetch_data(self):
        # Check if symbol, strike_price, and maturity_date fields are filled
        if self.symbol_input.input_field.text() and self.x_input.input_field.text() and self.date_input.input_field.text():
            company = self.symbol_input.input_field.text()
            date = self.date_input.input_field.text()
            strike = float(self.x_input.input_field.text())

            # Initiate thread to fetch stock price
            self.fetch_stock_price(company)

            # Initiate thread to fetch option premiums
            self.update_option_premiums()

            # update t and implied volatility
            today_date = self.today_date.input_field.text()
            maturity_date = self.date_input.input_field.text()
            T = (QDate.fromString(today_date, "yyyy-MM-dd").daysTo(QDate.fromString(maturity_date, "yyyy-MM-dd")))
            self.time_input.input_field.setText(str(T))

            # Update only if data is not 'NA'
            call_premium_text = self.call_premium_input.input_field.text()
            put_premium_text = self.put_premium_input.input_field.text()
            if call_premium_text != 'NA' and put_premium_text != 'NA':
                r = float(self.interest_input.input_field.text())
                sigma = float(self.volatility_input.input_field.text())
                T = T / 365
                stock_price_text = self.stock_price_input.input_field.text()
                if stock_price_text != 'NA':
                    stock = float(stock_price_text)
                    impvC = BlackScholes().blsimpv('c', stock, strike, T, r, float(call_premium_text), sigma)
                    impvP = BlackScholes().blsimpv('p', stock, strike, T, r, float(put_premium_text), sigma)

                    # Update input fields with two decimal places
                    self.impvC_input.input_field.setText("{:.2f}".format(impvC) if impvC is not None else "NA")
                    self.impvP_input.input_field.setText("{:.2f}".format(impvP) if impvP is not None else "NA")

                    # Update call and put price
                    call_price = BlackScholes().blsprice('c', stock, strike, T, r, sigma)
                    put_price = BlackScholes().blsprice('p', stock, strike, T, r, sigma)
                    self.call_price_input.input_field.setText("{:.2f}".format(call_price))
                    self.put_price_input.input_field.setText("{:.2f}".format(put_price))

                    # Update call and put delta
                    call_delta = BlackScholes().blsdelta('c', stock, strike, T, r, sigma)
                    put_delta = BlackScholes().blsdelta('p', stock, strike, T, r, sigma)
                    self.call_delta_input.input_field.setText("{:.2f}".format(call_delta))
                    self.put_delta_input.input_field.setText("{:.2f}".format(put_delta))
            else:
                # Set all outputs to 'NA' if premiums are not available
                self.impvC_input.input_field.setText("NA")
                self.impvP_input.input_field.setText("NA")
                self.call_price_input.input_field.setText("NA")
                self.put_price_input.input_field.setText("NA")
                self.call_delta_input.input_field.setText("NA")
                self.put_delta_input.input_field.setText("NA")

    
    def fetch_stock_price(self, company):
        """Initiates fetching of the stock price for the given company symbol."""
        # Ensure any existing thread is terminated before starting a new one
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

        # Update color based on price_change value
        if price_change and price_change > 0:
            color = "#007560"  # green
        elif price_change and price_change < 0:
            color = "#bd1414"  # red
        else:
            color = "black"

        self.stock_price_input.input_field.setStyleSheet(f"color: {color};")
        self.price_change_input.input_field.setStyleSheet(f"color: {color};")
        self.percent_change_input.input_field.setStyleSheet(f"color: {color};")
        
    def update_option_premiums(self):
        company = self.symbol_input.input_field.text()
        date = self.date_input.input_field.text()
        strike = float(self.x_input.input_field.text())

        # Cancel any existing thread to avoid overlapping requests
        if hasattr(self, 'option_fetch_thread'):
            self.option_fetch_thread.terminate()

        self.option_fetch_thread = FetchOptionThread(company, date, strike)
        self.option_fetch_thread.data_fetched.connect(self.fill_premium_inputs)
        self.option_fetch_thread.start()

    def fill_premium_inputs(self, prices):
        call_premium_str = str(prices[0]) if prices and prices[0] is not None else "NA"
        put_premium_str = str(prices[1]) if prices and prices[1] is not None else "NA"
        
        self.call_premium_input.input_field.setText(call_premium_str)
        self.put_premium_input.input_field.setText(put_premium_str)
        
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