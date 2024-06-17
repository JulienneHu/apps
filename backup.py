import sys
import pandas as pd
import holidays
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QGridLayout, QFrame, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt
from sqlalchemy import create_engine, text
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt

from realPrice.OptionPnl import main  # Ensure this import path is correct

# Database setup
DATABASE_NAME = 'trades.db'
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
        self.setGeometry(100, 100, 1200, 800)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        
        # Left-side controls
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)

        self.trade_date_input = self.create_input_field("Trade Date", '2024-05-13', control_layout)
        self.symbol_input = self.create_input_field("Symbol", 'AMD', control_layout)
        self.strike_input = self.create_input_field("Strike Price", '185', control_layout)
        self.expiration_input = self.create_input_field("Expiration Date", '2024-06-21', control_layout)
        self.stock_trade_price_input = self.create_input_field("Stock Trade Price", '181.00', control_layout)
        self.effective_delta_input = self.create_input_field("Effective Delta", '-0.15', control_layout)
        
        self.call_action_type_input = self.create_combo_box("Call Action Type", ["buy", "sell"], control_layout)
        self.put_action_type_input = self.create_combo_box("Put Action Type", ["buy", "sell"], control_layout)
        
        self.num_call_contracts_input = self.create_input_field("NCall Contracts", '2', control_layout)
        self.num_put_contracts_input = self.create_input_field("NPut Contracts", '3', control_layout)
        
        self.put_trade_price_input = self.create_input_field("Put Trade Price", '14.55', control_layout)
        self.call_trade_price_input = self.create_input_field("Call Trade Price", '12.65', control_layout)
        
        self.add_trade_button = QPushButton("Add Trade")
        self.add_trade_button.clicked.connect(self.add_trade)
        control_layout.addWidget(self.add_trade_button)

        control_panel.setLayout(control_layout)
        control_panel.setMaximumWidth(400)
        grid_layout.addWidget(control_panel, 0, 0)

        # Right-side plot
        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 1, 1)
        grid_layout.addWidget(self.canvas, 0, 1)
        
        self.show()

    def create_input_field(self, label, default_value, layout, editable=True):
        container = QWidget()
        field_layout = QHBoxLayout()
        field_layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        field_layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        input_field = QLineEdit(default_value)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure input field can expand
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
        field_layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        field_layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        combo_box = QComboBox()
        combo_box.addItems(options)
        combo_box.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure combo box can expand
        
        field_layout.addWidget(lbl)
        field_layout.addWidget(combo_box)
        container.setLayout(field_layout)
        layout.addWidget(container)
        container.combo_box = combo_box
        return container


    def add_trade(self):
        # Collect input values
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

        # Get historical data from main function
        option_data = main(symbol, expiration, strike, trade_date)

        if option_data is not None and not option_data.empty:
            for _, row in option_data.iterrows():
                
                call_action, put_action = self.call_action_type_input.combo_box.currentText(), self.put_action_type_input.combo_box.currentText()   
                if call_action == 'buy' and put_action == 'buy':
                    daily_pnl = abs(effective_delta) * (stock_trade_price - row['stock_close_price']) + \
                                num_call_contracts * (call_trade_price - row['call_close_price']) + \
                                num_put_contracts * (put_trade_price - row['put_close_price'])
                                
                daily_pnl = round(daily_pnl, 2)
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
                    'daily_pnl': daily_pnl
                }

                try:
                    with engine.connect() as conn:
                        conn.execute(text("""
                            INSERT INTO trades (
                                trade_date, symbol, strike, expiration, stock_trade_price, effective_delta, 
                                call_trade_price, call_action_type, num_call_contracts, put_trade_price, 
                                put_action_type, num_put_contracts, stock_close_price, call_close_price, 
                                put_close_price, daily_pnl
                            ) VALUES (
                                :trade_date, :symbol, :strike, :expiration, :stock_trade_price, :effective_delta, 
                                :call_trade_price, :call_action_type, :num_call_contracts, :put_trade_price, 
                                :put_action_type, :num_put_contracts, :stock_close_price, :call_close_price, 
                                :put_close_price, :daily_pnl
                            )
                        """), params)
                except Exception as e:
                    print(f"Failed to insert data for {row['date']}: {e}")

            self.update_plot()  # Update your plot if necessary
        else:
            print("No data found or unable to retrieve data.")


    def update_plot(self):
        self.ax.clear()  # Clear existing data on the plot
        with engine.connect() as conn:
            result = conn.execute(text("SELECT trade_date, daily_pnl, call_close_price, put_close_price, stock_close_price FROM trades"))
            data = pd.DataFrame(result.fetchall(), columns=result.keys())

        dates = pd.to_datetime(data['trade_date'])
        dates = dates.dt.strftime('%m-%d')
        self.ax.plot(dates, data['daily_pnl'], 'o-', color='blue', linewidth=2, markerfacecolor='red', markersize=8, picker=5)

        annot = self.ax.annotate("", xy=(0,0), xytext=(10,10), textcoords="offset points",
                                bbox=dict(boxstyle="round", fc="lightblue", ec="black"),
                                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=.5", color='black'))
        annot.set_visible(False)

        self.ax.set_title('Daily PNL')
        self.ax.set_xlabel('Trade Date')
        self.ax.set_ylabel('Daily PNL')
        self.ax.grid(True)
        
        def onpick(event):
            artist = event.artist
            ind = event.ind[0]  # index of the point
            x, y = artist.get_data()
            annot.xy = (x[ind], y[ind])
            text = f"Stock: ${data.iloc[ind]['stock_close_price']:.2f} \nCall: ${data.iloc[ind]['call_close_price']:.2f} \nPut: ${data.iloc[ind]['put_close_price']:.2f} \nPNL: ${data.iloc[ind]['daily_pnl']:.2f}"
            annot.set_text(text)
            annot.get_bbox_patch().set_facecolor('lightgreen')
            annot.set_visible(True)
            self.figure.canvas.draw_idle()

        self.figure.canvas.mpl_connect('pick_event', onpick)
        self.canvas.draw()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionPNLApp()
    sys.exit(app.exec_())
