import sys
import pandas as pd
import yfinance as yf
import holidays
import pytz
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGridLayout, QFrame, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QMovie
import matplotlib.pyplot as plt
import mplcursors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from datetime import datetime

from realPrice.OptionPnl import main, calls_or_puts
from realPrice.realOption import get_realtime_option_price

from tools.stylesheet import stylesheet
from tools.pnl_creations import pnl_create_input_field as create_input_field, create_combo_box


# Dummy DataFrame to hold trade data
trades_df = pd.DataFrame(columns=[
    'trade_date', 'symbol', 'strike', 'expiration', 'stock_trade_price', 'effective_delta',
    'call_trade_price', 'call_action_type', 'num_call_contracts', 'put_trade_price',
    'put_action_type', 'num_put_contracts', 'stock_close_price', 'call_close_price',
    'put_close_price', 'daily_pnl', 'change'
])


class OptionPNLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet(stylesheet)
        self.trades = trades_df.copy()
    
    def initUI(self):
        self.setWindowTitle("Option PNL Tracker")
        self.setGeometry(100, 100, 1400, 800)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        
        # Left-side controls
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)

        self.trade_date_input = create_input_field("Trade Date", '2024-05-08', control_layout)
        self.symbol_input = create_input_field("Symbol", 'MSFT', control_layout)
        self.strike_input = create_input_field("Strike Price", '415', control_layout)
        self.expiration_input = create_input_field("Expiration Date", '2024-07-19', control_layout)
        self.stock_trade_price_input = create_input_field("Stock Trade Price", '412.00', control_layout)
        self.effective_delta_input = create_input_field("Effective Delta", '0', control_layout)
        
        self.call_action_type_input = create_combo_box("Call Action Type", ["buy", "sell"], control_layout)
        self.put_action_type_input = create_combo_box("Put Action Type", ["buy", "sell"], control_layout)
        
        self.num_call_contracts_input = create_input_field("NCall Contracts", '1', control_layout)
        self.num_put_contracts_input = create_input_field("NPut Contracts", '1', control_layout)
        
        self.put_trade_price_input = create_input_field("Put Trade Price", '12', control_layout)
        self.call_trade_price_input = create_input_field("Call Trade Price", '11', control_layout)
        
        # for all input fields, after return pressed, add_trade will be called
        for input_field in [self.trade_date_input.input_field, self.symbol_input.input_field, self.strike_input.input_field, self.expiration_input.input_field,
                            self.stock_trade_price_input.input_field, self.effective_delta_input.input_field, self.num_call_contracts_input.input_field,
                            self.num_put_contracts_input.input_field, self.put_trade_price_input.input_field, self.call_trade_price_input.input_field]:
            input_field.returnPressed.connect(self.add_trade)
        
        self.add_trade_button = QPushButton("Add Trade")
        self.add_trade_button.clicked.connect(self.add_trade)
        control_layout.addWidget(self.add_trade_button)
        
        # Add status label
        self.status_label = QLabel("")
        control_layout.addWidget(self.status_label)

        # Add loading spinner
        self.loading_spinner = QLabel()
        self.loading_spinner.setAlignment(Qt.AlignCenter)
        movie = QMovie('./tools/loading.gif')
        movie.setScaledSize(QSize(50, 50))   
        self.loading_spinner.setMovie(movie)
        movie.start()
        control_layout.addWidget(self.loading_spinner)
        self.loading_spinner.hide()

        control_panel.setLayout(control_layout)
        control_panel.setMaximumWidth(400)
        grid_layout.addWidget(control_panel, 0, 0)

        # Right-side plot
        self.figure = plt.Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumSize(800, 600)
        grid_layout.addWidget(self.canvas, 0, 1)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 1, 1)

        self.show()


    def calculate_pnl(self, call_action, put_action, NC, C_0, C_t, NP, P_0, P_t, effectice_delta, trade_price, current_price):
        if call_action == "sell" and put_action == "sell":
            return (NC * (C_0 - C_t) + NP * (P_0 - P_t) + effectice_delta * (current_price - trade_price)) * 100
        elif call_action == "sell" and put_action == "buy":
            return (NC * (C_0 - C_t) + NP * (P_t - P_0) + effectice_delta * (current_price - trade_price)) * 100
        elif call_action == "buy" and put_action == "sell":
            return (NC * (C_t - C_0) + NP * (P_0 - P_t) + effectice_delta * (current_price - trade_price)) * 100
        elif call_action == "buy" and put_action == "buy":
            return (NC * (C_t - C_0) + NP * (P_t - P_0) + effectice_delta * (current_price - trade_price)) * 100
        else:
            return 0  

    def market_open(self):
        today = datetime.now()  
        eastern = pytz.timezone('US/Eastern')
        current_time_et = datetime.now(eastern).time()
        market_open = datetime.strptime("09:30", "%H:%M").time()
        market_close = datetime.strptime("16:00", "%H:%M").time()
        return market_open <= current_time_et <= market_close and today.weekday() < 5 and today not in holidays.US() 
    
    def add_trade(self):
        # Show the loading spinner
        self.loading_spinner.show()
        self.status_label.setText("Adding trade...")
        
        # Get input values
        trade_date = self.trade_date_input.input_field.text()
        symbol = self.symbol_input.input_field.text()
        strike = float(self.strike_input.input_field.text())
        expiration = self.expiration_input.input_field.text()
        stock_trade_price = float(self.stock_trade_price_input.input_field.text())
        call_trade_price = float(self.call_trade_price_input.input_field.text())
        put_trade_price = float(self.put_trade_price_input.input_field.text())
        effective_delta = float(self.effective_delta_input.input_field.text())
        num_call_contracts = int(self.num_call_contracts_input.input_field.text())
        num_put_contracts = int(self.num_put_contracts_input.input_field.text())
        call_action_type = self.call_action_type_input.combo_box.currentText()
        put_action_type = self.put_action_type_input.combo_box.currentText()

        # Fetch historical data
        option_data = main(symbol, expiration, strike, trade_date)

        if option_data is None or option_data.empty:
            print("No data found or unable to retrieve data.")
            return

        # Fetch real-time data if market is open
        if self.market_open():
            options = calls_or_puts(symbol, expiration, strike)
            if options and len(options) == 2:
                call_close_price, call_ask_price, call_bid_price = get_realtime_option_price(options[0])
                put_close_price, put_ask_price, put_bid_price = get_realtime_option_price(options[1])
                option_data.at[option_data.index[-1], 'call_close_price'] = call_ask_price if call_action_type == "sell" else call_bid_price
                option_data.at[option_data.index[-1], 'put_close_price'] = put_ask_price if put_action_type == "sell" else put_bid_price

        # Proceed with updating trades and calculating PNL
        if option_data is not None and not option_data.empty:
            for _, row in option_data.iterrows():
                daily_pnl = self.calculate_pnl(call_action_type, put_action_type,
                                            num_call_contracts, call_trade_price, row['call_close_price'],
                                            num_put_contracts, put_trade_price, row['put_close_price'],
                                            effective_delta, stock_trade_price, row['stock_close_price'])
                daily_pnl = round(daily_pnl, 2)
                investment = ((num_call_contracts * call_trade_price) + (num_put_contracts * put_trade_price)) * 100
                change = round(daily_pnl / investment * 100, 2)
                new_trade = {
                    'trade_date': row['date'].strftime('%Y-%m-%d'),
                    'symbol': symbol,
                    'strike': strike,
                    'expiration': expiration,
                    'stock_trade_price': stock_trade_price,
                    'effective_delta': effective_delta,
                    'call_trade_price': row['call_close_price'],
                    'call_action_type': call_action_type,
                    'num_call_contracts': num_call_contracts,
                    'put_trade_price': row['put_close_price'],
                    'put_action_type': put_action_type,
                    'num_put_contracts': num_put_contracts,
                    'stock_close_price': round(row['stock_close_price'], 2),
                    'call_close_price': row['call_close_price'],
                    'put_close_price': row['put_close_price'],
                    'daily_pnl': daily_pnl,
                    'change': change
                }

                # Check if the trade already exists in the DataFrame
                exists = self.trades[
                    (self.trades['trade_date'] == new_trade['trade_date']) &
                    (self.trades['symbol'] == new_trade['symbol']) &
                    (self.trades['strike'] == new_trade['strike']) &
                    (self.trades['expiration'] == new_trade['expiration']) &
                    (self.trades['stock_trade_price'] == new_trade['stock_trade_price']) &
                    (self.trades['effective_delta'] == new_trade['effective_delta']) &
                    (self.trades['call_trade_price'] == new_trade['call_trade_price']) &
                    (self.trades['call_action_type'] == new_trade['call_action_type']) &
                    (self.trades['num_call_contracts'] == new_trade['num_call_contracts']) &
                    (self.trades['put_trade_price'] == new_trade['put_trade_price']) &
                    (self.trades['put_action_type'] == new_trade['put_action_type']) &
                    (self.trades['num_put_contracts'] == new_trade['num_put_contracts']) 
                    # (self.trades['stock_close_price'] == new_trade['stock_close_price']) &
                    # (self.trades['call_close_price'] == new_trade['call_close_price']) &
                    # (self.trades['put_close_price'] == new_trade['put_close_price']) &
                    # (self.trades['daily_pnl'] == new_trade['daily_pnl']) &
                    # (self.trades['change'] == new_trade['change'])
                ]
                
                
                if not exists.empty:     
                    self.trades = self.trades.drop(exists.index)
                    print("Trade already exists. Skipping duplicate entry.")
                    continue

                # Add the new trade to the DataFrame
                new_df = pd.DataFrame([new_trade])
                self.trades = pd.concat([self.trades, new_df], ignore_index=True)

            
            self.update_plot()
            self.status_label.setText("Trade added successfully!")
            self.loading_spinner.hide()
        else:
            print("No data found or unable to retrieve data.")

    def update_plot(self):
        input_date = self.trade_date_input.input_field.text()
        symbol = self.symbol_input.input_field.text()
        strike = float(self.strike_input.input_field.text())
        expiration = self.expiration_input.input_field.text()
        call_action_type = self.call_action_type_input.combo_box.currentText()
        put_action_type = self.put_action_type_input.combo_box.currentText()
        num_call_contracts = int(self.num_call_contracts_input.input_field.text())
        num_put_contracts = int(self.num_put_contracts_input.input_field.text())
        trade_price = float(self.stock_trade_price_input.input_field.text())
        effective_delta = float(self.effective_delta_input.input_field.text())

        filtered_data = self.trades[
            (self.trades['symbol'] == symbol) &
            (self.trades['strike'] == strike) &
            (self.trades['expiration'] == expiration) &
            (self.trades['trade_date'] >= input_date) &
            (self.trades['call_action_type'] == call_action_type) &
            (self.trades['put_action_type'] == put_action_type) &
            (self.trades['num_call_contracts'] == num_call_contracts) &
            (self.trades['num_put_contracts'] == num_put_contracts) &
            (self.trades['stock_trade_price'] == trade_price) &
            (self.trades['effective_delta'] == effective_delta)     
        ]
        

        if not filtered_data.empty:
            filtered_data = filtered_data.sort_values(by='trade_date')
            filtered_data['trade_date'] = pd.to_datetime(filtered_data['trade_date'])
            filtered_data['plot_index'] = range(len(filtered_data))
            date_labels = {row['plot_index']: row['trade_date'].strftime('%m-%d') for index, row in filtered_data.iterrows()}
            colors = ['#bd1414' if x < 0 else '#007560' for x in filtered_data['daily_pnl']]
            hover_texts = []
            for idx, row in filtered_data.iterrows():
                hover_text = f"Date: {row['trade_date'].strftime('%Y-%m-%d')}\n" \
                            f"Stock: ${row['stock_close_price']:.2f}\n" \
                            f"Call: ${row['call_close_price']:.2f}\n" \
                            f"Put: ${row['put_close_price']:.2f}\n" \
                            f"Daily PNL: ${row['daily_pnl']:.2f}\n" \
                            f"Change: {row['change']:.2f}%"
                hover_texts.append(hover_text)
            filtered_data['hover_text'] = hover_texts

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            
            scatter = ax.scatter(filtered_data['plot_index'], filtered_data['daily_pnl'], c=colors, s=100)
            ax.plot(filtered_data['plot_index'], filtered_data['daily_pnl'], color='black', linewidth=2)

            subtitle = f'{call_action_type.capitalize()} {num_call_contracts} Call(s) & {put_action_type.capitalize()} {num_put_contracts} Put(s)'

            ax.set_title(f"Profit & Loss\n{subtitle}", fontsize=14)
            ax.set_xlabel('Date', fontdict={'fontsize': 14})
            ax.set_ylabel('Π', fontdict={'fontsize': 14})
            ax.axhline(y=0, color='black', linestyle='--', linewidth=2)
            ax.grid(True)

            ax.set_xticks(list(date_labels.keys()))
            ax.set_xticklabels(list(date_labels.values()), rotation=45, ha='right')
            
            ax.tick_params(axis='x', labelsize=10)
            ax.tick_params(axis='y', labelsize=10)

            cursor = mplcursors.cursor(scatter, hover=True)
            cursor.connect("add", lambda sel: sel.annotation.set_text(filtered_data['hover_text'].iloc[sel.index]))
            self.canvas.draw()
        else:
            print("No data to display for selected filters.")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionPNLApp()
    sys.exit(app.exec_())
