import sys
import os
curr = os.getcwd()
curr = os.path.dirname(curr)
sys.path.append(curr)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSlider, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                             QGridLayout, QFrame, QSizePolicy)  # Added QSizePolicy here
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

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
        self.option_fetch_threads = []


    def initUI(self):
        
        self.setWindowTitle("Butterfly")
        self.setGeometry(100, 100, 1357, 768)  # Set to the image width and height

        # Central widget and layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        # Left-side controls
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)

        # Adjustments for control panel layout and dimensions
        control_panel.setMaximumWidth(400)  # Adjust this value to make the control panel narrower

        # Trade Type Combo Box
        self.butterfly_type_combo = QComboBox(control_panel)
        self.butterfly_type_combo.addItems(['Call', 'Put'])
        control_layout.addWidget(self.butterfly_type_combo)

        # Sliders
        self.delta1= self.create_input_field('Delta1', '0')  
        control_layout.addWidget(self.delta1)

        self.delta2 = self.create_input_field('Delta2',  '0')
        control_layout.addWidget(self.delta2)

        self.delta3 = self.create_input_field('Delta3', '0') 
        control_layout.addWidget(self.delta3)

        # Input Fields
        # Adjust the layout for the input fields to be in lines
        input_layout_1 = QHBoxLayout()
        self.symbol_input = self.create_input_field('Symbol', 'AAPL')  # Default symbol
        input_layout_1.addWidget(self.symbol_input)
        control_layout.addLayout(input_layout_1)
        
        input_layout_2 = QHBoxLayout()
        self.date_input = self.create_input_field('Maturity_Date', '2024-05-17')  # Default date
        input_layout_2.addWidget(self.date_input)
        control_layout.addLayout(input_layout_2)    
           
        self.x_inputs = []
        self.call_premium_inputs = []
        self.put_premium_inputs = []
        for i in range(3):  
            input_layout = QHBoxLayout()

            x_input = self.create_input_field(f'X{i+1}', '150')  
            call_input = self.create_input_field(f'C{i+1}', '9.8', editable=False)  
            put_input = self.create_input_field(f'P{i+1}', '14.5', editable=False)  

            input_layout.addWidget(x_input)
            input_layout.addWidget(call_input)
            input_layout.addWidget(put_input)

            # Add the input fields to the respective lists for later access
            self.x_inputs.append(x_input)
            self.call_premium_inputs.append(call_input)
            self.put_premium_inputs.append(put_input)

            # Add the layout to the main control layout
            control_layout.addLayout(input_layout)
       
        self.fetch_data_button = QPushButton('Fetch Data / Refresh', control_panel)
        self.fetch_data_button.clicked.connect(self.fetch_data)  # Connect button click to the fetch_data method
        self.fetch_data_button.clicked.connect(self.update_plot)
        control_layout.addWidget(self.fetch_data_button)

        input_layout_6 = QHBoxLayout()
        self.stock_price_input = self.create_input_field('SPrice', '150', False)
        self.price_change_input = self.create_input_field('Real', '0', False)
        self.percent_change_input = self.create_input_field('Pct', '0', False)
        input_layout_6.addWidget(self.stock_price_input)
        input_layout_6.addWidget(self.price_change_input)
        input_layout_6.addWidget(self.percent_change_input)
        control_layout.addLayout(input_layout_6)

        input_layout_7 = QHBoxLayout()
        self.stock_range_input = self.create_input_field('SRange', '0.25')
        self.y_min_input = self.create_input_field('Y_Min', '-1000')
        self.y_max_input = self.create_input_field('Y_Max', '1000')
        input_layout_7.addWidget(self.stock_range_input)
        input_layout_7.addWidget(self.y_min_input)
        input_layout_7.addWidget(self.y_max_input)    
        control_layout.addLayout(input_layout_7)

        # Add control panel to grid
        grid_layout.addWidget(control_panel, 0, 0)

        # Right-side plot
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumWidth(800)  # Increase this value to make the plot area wider
        grid_layout.addWidget(self.canvas, 0, 1)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 1, 1)  # Place it under the canvas or wherever you see fit

        # Adjust the column stretch factors to change the proportions
        grid_layout.setColumnStretch(0, 35)  # Less stretch for controls column
        grid_layout.setColumnStretch(1, 65)  # More stretch for plot column

        # Connect signals to update method
        self.delta1.input_field.returnPressed.connect(self.update_plot)  
        self.delta2.input_field.returnPressed.connect(self.update_plot)
        self.delta3.input_field.returnPressed.connect(self.update_plot)
        
        # Connecting signals for x_inputs
        for x_input in self.x_inputs:
            x_input.input_field.returnPressed.connect(self.update_plot)

        # Connecting signals for call_premium_inputs
        for call_input in self.call_premium_inputs:
            call_input.input_field.returnPressed.connect(self.update_plot)

        # Connecting signals for put_premium_inputs
        for put_input in self.put_premium_inputs:
            put_input.input_field.returnPressed.connect(self.update_plot)

        # Connect signals for stock price and range inputs
        self.stock_price_input.input_field.textChanged.connect(self.update_plot)
        
        self.stock_range_input.input_field.returnPressed.connect(self.update_plot)
        self.y_min_input.input_field.returnPressed.connect(self.update_plot)
        self.y_max_input.input_field.returnPressed.connect(self.update_plot)
        self.butterfly_type_combo.currentIndexChanged.connect(self.update_plot)
        self.fetch_data_button.clicked.connect(self.update_plot)
        
        self.x_inputs[0].input_field.returnPressed.connect(self.update_plot)
        self.x_inputs[1].input_field.returnPressed.connect(self.update_plot)
        self.x_inputs[2].input_field.returnPressed.connect(self.update_plot)
        
        self.call_premium_inputs[0].input_field.textChanged.connect(self.update_plot)
        self.put_premium_inputs[0].input_field.textChanged.connect(self.update_plot)
        self.call_premium_inputs[1].input_field.textChanged.connect(self.update_plot)
        self.put_premium_inputs[1].input_field.textChanged.connect(self.update_plot)
        self.call_premium_inputs[2].input_field.textChanged.connect(self.update_plot)
        self.put_premium_inputs[2].input_field.textChanged.connect(self.update_plot)
        
        self.date_input.input_field.returnPressed.connect(self.fetch_data)
        self.symbol_input.input_field.returnPressed.connect(self.fetch_data)
        
        # Show the window
        self.show()

    def create_slider(self, label, min_val, max_val, precision, default_val=1):
        # Use a QWidget to hold the layout
        container = QWidget()
        layout = QHBoxLayout()
        lbl = QLabel(f'{label}: {default_val}')
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(int(min_val / precision))
        slider.setMaximum(int(max_val / precision))
        # Set default value, adjusted by precision
        slider.setValue(int(default_val / precision))
        slider.valueChanged.connect(lambda value: lbl.setText(f'{label}: {value * precision}'))
        slider.valueChanged.connect(self.update_plot)  # Connect the slider to the update_plot method
        layout.addWidget(lbl)
        layout.addWidget(slider)
        container.setLayout(layout)
        container.slider = slider  # Store the slider in the container for access
        return container


    def create_input_field(self, label, default_value, editable=True):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        input_field = QLineEdit(default_value)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure input field can expand
        input_field.setReadOnly(not editable)
        
        input_field.returnPressed.connect(self.update_plot)
        
        layout.addWidget(lbl)
        layout.addWidget(input_field)
        container.setLayout(layout)
        container.input_field = input_field
        return container

    def update_plot(self):
        
        if 'NA' in [self.stock_price_input.input_field.text(), self.call_premium_inputs[0].input_field.text(), self.put_premium_inputs[0].input_field.text(), 
                    self.call_premium_inputs[1].input_field.text(), self.put_premium_inputs[1].input_field.text(), 
                    self.call_premium_inputs[2].input_field.text(), self.put_premium_inputs[2].input_field.text()]:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Options does not exist. Please input valid parameters', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return
            
        try: 
            stock_price = float(self.stock_price_input.input_field.text())
            stock_range = float(self.stock_range_input.input_field.text())
            X = [float(x_input.input_field.text()) for x_input in self.x_inputs]
            C = [float(call_input.input_field.text()) for call_input in self.call_premium_inputs]
            P = [float(put_input.input_field.text()) for put_input in self.put_premium_inputs]
            Delta = [float(self.delta1.input_field.text()) , float(self.delta2.input_field.text()) , float(self.delta3.input_field.text()) ]
            
            S_min = np.floor(stock_price * (1 - stock_range))
            S_max = np.ceil(stock_price * (1 + stock_range))
            S_grid = np.arange(S_min, S_max + 1, 0.1)
            Y_min = float(self.y_min_input.input_field.text())
            Y_max = float(self.y_max_input.input_field.text())
        except ValueError:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Invalid input. Please enter valid numbers.', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return
        
        # Calculate at-maturity values for calls and puts
        C_at_maturity = [np.maximum(S_grid - strike, 0) for strike in X]
        P_at_maturity = [np.maximum(strike - S_grid, 0) for strike in X]

        # Determine option strategy based on user input
        butterfly_type = self.butterfly_type_combo.currentText()
        if butterfly_type == 'Call':
            y_option_1 = C_at_maturity[0] - C[0]
            y_option_2 = C[1] - C_at_maturity[1]
            y_option_3 = C_at_maturity[2] - C[2]
            Effective_Delta = 2 * Delta[1] - Delta[0] - Delta[2]
        elif butterfly_type == 'Put':
            y_option_1 = P_at_maturity[0] - P[0]
            y_option_2 = P[1] - P_at_maturity[1]
            y_option_3 = P_at_maturity[2] - P[2]
            Effective_Delta = -2 * Delta[1] + Delta[0] + Delta[2]
        else:
            # Handle unexpected cases
            pass

        y_stock = Effective_Delta * (S_grid - stock_price)
        y = 100 * (y_option_1 + 2 * y_option_2 + y_option_3 + y_stock)

        yp = np.clip(y, 0, None)
        y_neg = np.where(yp == 0)[0]  
        y_pos = np.where(yp > 0)[0]   

        if y_neg.size > 0 and y_pos.size > 0:
            if S_grid[y_neg[0]] > S_min and S_grid[y_neg[-1]] < S_max:
                pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
            else:
                pos_range = S_grid[y_pos]
                if y_pos[0] == 0:
                    pos_str = f'(0, {np.ceil(pos_range[-1])})'
                else:
                    pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
        elif y_neg.size == 0:
            pos_str = "(0,∞)"
        else:
            pos_str = "∞"

        # Plot logic adapted from the MATLAB function plot_profile
        with plt.style.context('ggplot'):
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Plotting the strategy's profit/loss line
            ax.plot(S_grid, y, 'blue', linewidth=1.5, label='Strategy Profit/Loss')

            # Adding fill between profit and loss
            ax.fill_between(S_grid, y, where=(y > 0), color='#007560', alpha=0.8, label='Profit')
            ax.fill_between(S_grid, y, where=(y <= 0), color='#bd1414', alpha=0.8, label='Loss')

            # Enhancing title, labels, and gridlines for better readability
            title_str = [
                f"100Δ_effective = {round(100*Effective_Delta)}. Make money if S ∈ {pos_str}.\n" 
                f"Δ1 = {Delta[0]:.2f}, Δ2 = {Delta[1]:.2f}, Δ3 = {Delta[2]:.2f},\n"
                f"Effective Δ = {Effective_Delta:.2f}"
            ]
            ax.set_title("\n".join(title_str), fontsize=16, fontweight='bold')
            ax.set_xlabel('Stock Price', fontsize=14)
            ax.set_ylabel('Pay-off at Maturity', fontsize=14)
            ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='black')

            # Highlighting the zero line for reference
            ax.axhline(0, color='k', linewidth=1.5)

            # Setting the plot limits based on input
            ax.set_ylim([Y_min, Y_max])
            ax.set_xlim([S_min, S_max])

            # Adjusting the transparency for the fill_between sections to enhance visual appeal
            for collection in ax.collections:
                collection.set_alpha(0.8)

            # Adding a legend to help identify plot elements
            ax.legend()

            # Redrawing the canvas to reflect the updated plot
            self.canvas.draw()

    def fetch_data(self):
        # Check if the symbol and maturity date fields are filled
        if self.symbol_input.input_field.text() and self.date_input.input_field.text():
            company = self.symbol_input.input_field.text()
            date = self.date_input.input_field.text()

            # Ensure all strike price inputs are filled
            strikes_filled = all(x_input.input_field.text() for x_input in self.x_inputs)
            if not strikes_filled:
                print("Please ensure all strike prices are filled.")
                return

            # Convert strike price inputs to floats
            strikes = [float(x_input.input_field.text()) for x_input in self.x_inputs]

            # Initiate thread to fetch stock price
            self.fetch_stock_price(company)

            # Initiate threads to fetch option premiums for each strike price
            self.update_option_premiums()
        else:
            print("Please ensure all required fields (symbol and maturity date) are filled.")

        
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
        self.stock_price_input.input_field.setText(price)
        self.price_change_input.input_field.setText(price_change)
        self.percent_change_input.input_field.setText(percent_change)

        try:
            # Convert price_change to float for comparison
            price_change_float = float(price_change)
            # Update color based on the value of price_change
            if price_change_float > 0:
                color = "#007560"  # green
            elif price_change_float < 0:
                color = "#bd1414"  # red
            else:
                color = "black"
        except ValueError:
            color = "black"

        # Apply the color to text fields
        self.stock_price_input.input_field.setStyleSheet(f"color: {color};")
        self.price_change_input.input_field.setStyleSheet(f"color: {color};")
        self.percent_change_input.input_field.setStyleSheet(f"color: {color};")

            
    def start_option_fetch_thread(self, company, date, strike, index):
        thread = FetchOptionThread(company, date, strike)
        thread.data_fetched.connect(lambda prices: self.fill_premium_inputs(prices, index))
        thread.finished.connect(lambda: self.option_fetch_threads.remove(thread))  # Ensure the thread is removed from the list once finished
        thread.start()
        self.option_fetch_threads.append(thread)  # Keep track of the thread
   
    def update_option_premiums(self):
        company = self.symbol_input.input_field.text()
        date = self.date_input.input_field.text()
        for i, x_input in enumerate(self.x_inputs):
            strike = float(x_input.input_field.text())
            self.start_option_fetch_thread(company, date, strike, i)

    def fill_premium_inputs(self, prices, index):
        if prices and len(prices) >= 2:
            call_price = str(prices[0]) if prices[0] is not None else 'NA'
            put_price = str(prices[1]) if prices[1] is not None else 'NA'
        else:
            call_price = 'NA'
            put_price = 'NA'

        self.call_premium_inputs[index].input_field.setText(call_price)
        self.put_premium_inputs[index].input_field.setText(put_price)



    def terminate_threads(self):
        if hasattr(self, 'stock_fetch_thread') and self.stock_fetch_thread.isRunning():
            self.stock_fetch_thread.quit()
            self.stock_fetch_thread.wait()
            
        if hasattr(self, 'option_fetch_threads'):
            for thread in self.option_fetch_threads:
                if thread.isRunning():
                    thread.quit()
                    thread.wait()

           
if __name__ == '__main__':  
    app = QApplication(sys.argv)
    ex = OptionStrategyVisualizer()
    app.aboutToQuit.connect(ex.terminate_threads)
    sys.exit(app.exec_())
    ex.initUI()
    ex.fetch_data()
    