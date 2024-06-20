import sys
import pandas as pd
import yfinance as yf
import holidays
import pytz
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGridLayout, QFrame, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
import matplotlib.pyplot as plt
import mplcursors
from sqlalchemy import create_engine, text
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from datetime import datetime

from realPrice.OptionPnl import main, calls_or_puts
from realPrice.realOption import get_realtime_option_price

# Database setup
DATABASE_NAME = '/app/trades.db'
engine = create_engine(f'sqlite:///{DATABASE_NAME}')

# Create tables if they don't exist
with engine.connect() as conn:
    conn.execute(text("""
    CREATE TABLE IF NOT EXISTS trades (
        trade_date TEXT,
        symbol TEXT,
        strike REAL,
        expiration TEXT,
        stock_trade_price REAL,
        effective_delta REAL,
        call_trade_price REAL,
        call_action_type TEXT,
        num_call_contracts INTEGER,
        put_trade_price REAL,
        put_action_type TEXT,
        num_put_contracts INTEGER,
        stock_close_price REAL,
        call_close_price REAL,
        put_close_price REAL,
        daily_pnl REAL,
        change REAL,
        PRIMARY KEY (trade_date, symbol, strike, expiration, call_action_type, put_action_type, num_call_contracts, num_put_contracts)
    )
    """))

stylesheet = """
QWidget {
    font-family: Verdana, Arial, Helvetica, sans-serif;
    font-size: 14px;
    color: #333;
    background-color: #f7f7f7;
}
QComboBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    background: white;
    height: 30px;
    padding: 5px;
    font-size: 14px;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 15px;
    border-left-width: 1px;
    border-left-color: darkgray;
    border-left-style: solid;
    border-top-right-radius: 3px;
    border-bottom-right-radius: 3px;
}
QComboBox QAbstractItemView {
    selection-background-color: #ddd;
}
QLineEdit {
    border: 1px solid #ccc;
    padding: 5px;
    border-radius: 4px;
    background: white;
    font-size: 14px;
}
QLabel {
    font-size: 14px;
}
QPushButton {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 5px 10px;
    background: #eee;
    font-size: 14px;
}
QPushButton:pressed {
    background: #ddd;
}
QPushButton:hover {
    border-color: #bbb;
    background: #e0e0e0;
}
"""

class OptionPNLApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet(stylesheet)
    
    def initUI(self):
        self.setWindowTitle("Option PNL Tracker")
        self.setGeometry(100, 100, 1400, 800)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        
        # Left-side controls
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)

        self.trade_date_input = self.create_input_field("Trade Date", '2024-05-08', control_layout)
        self.symbol_input = self.create_input_field("Symbol", 'MSFT', control_layout)
        self.strike_input = self.create_input_field("Strike Price", '415', control_layout)
        self.expiration_input = self.create_input_field("Expiration Date", '2024-06-21', control_layout)
        self.stock_trade_price_input = self.create_input_field("Stock Trade Price", '412.00', control_layout)
        self.effective_delta_input = self.create_input_field("Effective Delta", '0', control_layout)
        
        self.call_action_type_input = self.create_combo_box("Call Action Type", ["buy", "sell"], control_layout)
        self.put_action_type_input = self.create_combo_box("Put Action Type", ["buy", "sell"], control_layout)
        
        self.num_call_contracts_input = self.create_input_field("NCall Contracts", '1', control_layout)
        self.num_put_contracts_input = self.create_input_field("NPut Contracts", '1', control_layout)
        
        self.put_trade_price_input = self.create_input_field("Put Trade Price", '12', control_layout)
        self.call_trade_price_input = self.create_input_field("Call Trade Price", '11', control_layout)
        
        self.add_trade_button = QPushButton("Add Trade")
        self.add_trade_button.clicked.connect(self.add_trade)
        control_layout.addWidget(self.add_trade_button)

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

    def create_input_field(self, label, default_value, layout, editable=True):
        container = QWidget()
        field_layout = QHBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
        input_field = QLineEdit(default_value)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_field.setReadOnly(not editable)
        
        if editable:
            input_field.returnPressed.connect(self.update_plot)
        
        field_layout.addWidget(lbl)
        field_layout.addWidget(input_field)
        container.setLayout(field_layout)
        layout.addWidget(container)
        container.input_field = input_field
        return container

    def create_combo_box(self, label, options, layout):
        container = QWidget()
        field_layout = QHBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        
        combo_box = QComboBox()
        combo_box.addItems(options)
        combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        combo_box.setEditable(True)
        combo_box.lineEdit().setAlignment(Qt.AlignCenter)
        combo_box.lineEdit().setReadOnly(True)

        field_layout.addWidget(lbl)
        field_layout.addWidget(combo_box)
        container.setLayout(field_layout)
        layout.addWidget(container)
        container.combo_box = combo_box
        return container

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
                change = round(daily_pnl / investment * 100 , 2) 
                params = {
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

                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO trades (
                                trade_date, symbol, strike, expiration, stock_trade_price, effective_delta,
                                call_trade_price, call_action_type, num_call_contracts, put_trade_price,
                                put_action_type, num_put_contracts, stock_close_price, call_close_price,
                                put_close_price, daily_pnl, change
                            ) VALUES (
                                :trade_date, :symbol, :strike, :expiration, :stock_trade_price, :effective_delta,
                                :call_trade_price, :call_action_type, :num_call_contracts, :put_trade_price,
                                :put_action_type, :num_put_contracts, :stock_close_price, :call_close_price,
                                :put_close_price, :daily_pnl, :change
                            )
                            ON CONFLICT (trade_date, symbol, strike, expiration, call_action_type, put_action_type, num_call_contracts, num_put_contracts)
                            DO UPDATE SET
                                stock_close_price = excluded.stock_close_price,
                                call_close_price = excluded.call_close_price,
                                put_close_price = excluded.put_close_price,
                                daily_pnl = excluded.daily_pnl,
                                change = excluded.change
                        """), params)
                except Exception as e:
                    print(f"Failed to insert data for {row['date']}: {e}")

            self.update_plot()
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

        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 
                    trade_date, daily_pnl, stock_close_price, call_close_price, put_close_price, change
                FROM 
                    trades
                WHERE
                    trade_date >= :start_date AND
                    symbol = :symbol AND
                    strike = :strike AND
                    expiration = :expiration AND
                    call_action_type = :call_action_type AND
                    put_action_type = :put_action_type AND
                    num_call_contracts = :num_call_contracts AND
                    num_put_contracts = :num_put_contracts
                GROUP BY trade_date
                ORDER BY trade_date ASC
            """), {
                'start_date': input_date,
                'symbol': symbol,
                'strike': strike,
                'expiration': expiration,
                'call_action_type': call_action_type,
                'put_action_type': put_action_type,
                'num_call_contracts': num_call_contracts,
                'num_put_contracts': num_put_contracts
            })
            data = pd.DataFrame(result.fetchall(), columns=result.keys())

        data['trade_date'] = pd.to_datetime(data['trade_date'])
        data['plot_index'] = range(len(data))
        date_labels = {row['plot_index']: row['trade_date'].strftime('%m-%d') for index, row in data.iterrows()}
        colors = ['#bd1414' if x < 0 else '#007560' for x in data['daily_pnl']]
        hover_texts = []
        for idx, row in data.iterrows():
            hover_text = f"Date: {row['trade_date'].strftime('%Y-%m-%d')}\n" \
                        f"Stock: ${row['stock_close_price']:.2f}\n" \
                        f"Call: ${row['call_close_price']:.2f}\n" \
                        f"Put: ${row['put_close_price']:.2f}\n" \
                        f"Daily PNL: ${row['daily_pnl']:.2f}\n" \
                        f"Change: {row['change']:.2f}%"
            hover_texts.append(hover_text)
        data['hover_text'] = hover_texts

        self.figure.clear()
        fig, ax = plt.subplots(figsize=(12, 9))
        ax = self.figure.add_subplot(111)
        
        scatter = ax.scatter(data['plot_index'], data['daily_pnl'], c=colors, s=100)
        ax.plot(data['plot_index'], data['daily_pnl'], color='black', linewidth=2)

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
        cursor.connect("add", lambda sel: sel.annotation.set_text(data['hover_text'][sel.index]))
        # add sleep to wait for the cursor to be created
        plt.pause(0.1)
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionPNLApp()
    sys.exit(app.exec_())
