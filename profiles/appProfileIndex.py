import sys
import os
curr = os.getcwd()
curr = os.path.dirname(curr)
sys.path.append(curr)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QSlider, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                             QGridLayout, QFrame, QSizePolicy)
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np


from realPrice.realOptionIndex import get_option_chain
from tools.stylesheet import stylesheet
from tools.APIFetch import FetchStockThread, FetchOptionThread
from tools.profile_creations import create_input_field, create_slider

class OptionStrategyVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setStyleSheet(stylesheet)

    def initUI(self):
        
        self.setWindowTitle("Option Strategy Visualizer(Index)")
        self.setGeometry(100, 100, 1357, 768)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)
        control_panel.setMaximumWidth(400)

        self.trade_type_combo = QComboBox(control_panel)
        self.trade_type_combo.addItems(['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])
        control_layout.addWidget(self.trade_type_combo)

        self.nCall_slider = create_slider('NCalls', 0, 5, 1, 1) 
        control_layout.addWidget(self.nCall_slider)

        self.nPut_slider = create_slider('NPuts', 0, 5, 1, 1)
        control_layout.addWidget(self.nPut_slider)

        self.deltaCall = create_input_field('DeltaCall', '0') 
        control_layout.addWidget(self.deltaCall)

        self.deltaPut = create_input_field('DeltaPut', '0')
        control_layout.addWidget(self.deltaPut)

        input_layout_1 = QHBoxLayout()
        self.symbol_input = create_input_field('Symbol', '^SPX')
        input_layout_1.addWidget(self.symbol_input)
        
        input_layout_2 = QHBoxLayout()
        self.date_input = create_input_field('Maturity_Date', '2024-08-16')
        input_layout_2.addWidget(self.date_input)
        
        input_layout_3 = QHBoxLayout()
        self.x_input = create_input_field('Strike_Price', '4500')
        input_layout_3.addWidget(self.x_input)

        self.fetch_data_button = QPushButton('Fetch Data / Refresh', control_panel)
        self.fetch_data_button.clicked.connect(self.fetch_data)
        self.fetch_data_button.clicked.connect(self.update_plot)

        input_layout_4 = QHBoxLayout()
        self.call_premium_input = create_input_field('C', '9.8', False)
        self.call_open_interest_input = create_input_field('C_OI', '0', False)
        self.call_volume_input = create_input_field('C_Vol', '0', False)
        input_layout_4.addWidget(self.call_premium_input)
        input_layout_4.addWidget(self.call_open_interest_input)
        input_layout_4.addWidget(self.call_volume_input)

        input_layout_5 = QHBoxLayout()
        self.put_premium_input = create_input_field('P', '14.5', False)
        self.put_open_interest_input = create_input_field('P_OI', '0', False)
        self.put_volume_input = create_input_field('P_Vol', '0', False)    
        input_layout_5.addWidget(self.put_premium_input)
        input_layout_5.addWidget(self.put_open_interest_input)
        input_layout_5.addWidget(self.put_volume_input)
        
        input_layout_6 = QHBoxLayout()
        self.stock_price_input = create_input_field('SPrice', '150', False)
        self.price_change_input = create_input_field('Real', '0', False)
        self.percent_change_input = create_input_field('Pct', '0', False)
        input_layout_6.addWidget(self.stock_price_input)
        input_layout_6.addWidget(self.price_change_input)
        input_layout_6.addWidget(self.percent_change_input)

        input_layout_7 = QHBoxLayout()
        self.y_min_input = create_input_field('Y_Min', '-1000')
        self.y_max_input = create_input_field('Y_Max', '1000')
        self.stock_range_input = create_input_field('SRange', '0.25')
        input_layout_7.addWidget(self.y_min_input)
        input_layout_7.addWidget(self.y_max_input)
        input_layout_7.addWidget(self.stock_range_input)
        
        input_layout_8 = QHBoxLayout()
        self.option_chain_input = create_input_field('Option Chain', 'SPW', False)
        input_layout_8.addWidget(self.option_chain_input)
        
        control_layout.addLayout(input_layout_1)
        control_layout.addLayout(input_layout_2)
        control_layout.addLayout(input_layout_3)
        control_layout.addWidget(self.fetch_data_button)
        control_layout.addLayout(input_layout_4)
        control_layout.addLayout(input_layout_5)
        control_layout.addLayout(input_layout_6)
        control_layout.addLayout(input_layout_7)
        control_layout.addLayout(input_layout_8)

        grid_layout.addWidget(control_panel, 0, 0)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumWidth(800)
        grid_layout.addWidget(self.canvas, 0, 1)
        
        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 1, 1)

        grid_layout.setColumnStretch(0, 35)
        grid_layout.setColumnStretch(1, 65)

        self.nCall_slider.slider.valueChanged.connect(self.update_plot)
        self.nPut_slider.slider.valueChanged.connect(self.update_plot)
        self.deltaCall.input_field.returnPressed.connect(self.update_plot)
        self.deltaPut.input_field.returnPressed.connect(self.update_plot)
        
        self.symbol_input.input_field.returnPressed.connect(self.update_plot)
        self.date_input.input_field.returnPressed.connect(self.update_plot)
        self.x_input.input_field.returnPressed.connect(self.update_plot)
        
        self.call_premium_input.input_field.textChanged.connect(self.update_plot)
        self.put_premium_input.input_field.textChanged.connect(self.update_plot)
        self.stock_price_input.input_field.textChanged.connect(self.update_plot)
        
        self.stock_range_input.input_field.returnPressed.connect(self.update_plot)
        self.y_min_input.input_field.returnPressed.connect(self.update_plot)
        self.y_max_input.input_field.returnPressed.connect(self.update_plot)
        self.trade_type_combo.currentIndexChanged.connect(self.update_plot)
        self.show()

    def update_plot(self):
        if 'NA' in [self.stock_price_input.input_field.text(), self.call_premium_input.input_field.text(), 
                    self.put_premium_input.input_field.text()]:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Invalid data. Please input valid parameters.', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return  

        try:
            n_call = self.nCall_slider.slider.value()
            n_put = self.nPut_slider.slider.value()
            delta_call = float(self.deltaCall.input_field.text()) 
            delta_put = - abs(float(self.deltaPut.input_field.text())) 
            stock_price = float(self.stock_price_input.input_field.text())
            X = float(self.x_input.input_field.text())
            call_premium = float(self.call_premium_input.input_field.text())
            put_premium = float(self.put_premium_input.input_field.text())
            stock_range = float(self.stock_range_input.input_field.text())
            Y_min = float(self.y_min_input.input_field.text())
            Y_max = float(self.y_max_input.input_field.text())
        except ValueError:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Invalid data. Please input valid parameters.', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return
            
        S_min = np.floor(stock_price * (1 - stock_range))
        S_max = np.ceil(stock_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max + 1, 0.1)
        call_at_maturity = np.maximum(S_grid - X, 0)
        put_at_maturity = np.maximum(X - S_grid, 0)

        trade_type = self.trade_type_combo.currentText()
        if trade_type == 'Buy Call-Buy Put':
            y_option = n_call * (call_at_maturity - call_premium) + n_put * (put_at_maturity - put_premium)
            y_stock  = n_call * delta_call * (stock_price - S_grid) + n_put * delta_put * (stock_price - S_grid)
            effective_delta = -n_call * delta_call - n_put * delta_put
        if trade_type == 'Buy Call-Sell Put':
            y_option = n_call * (call_at_maturity - call_premium) + n_put * (put_premium - put_at_maturity)
            effective_delta = -n_call * delta_call + n_put * delta_put
        if trade_type == 'Sell Call-Buy Put':
            y_option = n_call * (call_premium - call_at_maturity) + n_put * (put_at_maturity - put_premium)
            y_stock  = n_call * delta_call * (S_grid - stock_price) + n_put * delta_put * (stock_price - S_grid)
            effective_delta = n_call * delta_call - n_put * delta_put
        if trade_type == 'Sell Call-Sell Put': 
            y_option = n_call * (call_premium - call_at_maturity) + n_put * (put_premium - put_at_maturity)
            y_stock  = n_call * delta_call * (S_grid - stock_price) + n_put * delta_put * (S_grid - stock_price)
            effective_delta = n_call * delta_call + n_put * delta_put

        y = 100 * (y_option + y_stock)
        yp = np.maximum(y, 0)
        y_neg = np.where(yp == 0)[0]
        y_pos = np.where(yp > 0)[0]

        if y_neg.size != 0 and y_pos.size != 0:
            if y_neg[0] > 0 and y_neg[-1] < len(S_grid) - 1:
                pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
            else:
                pos_range = S_grid[y_pos]
                if y_pos[0] == 0:
                    pos_str = f'(0, {np.ceil(pos_range[-1])})'
                else:
                    pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
        elif y_neg.size == 0:
            pos_str = '(0, ∞)'
        else:
            pos_str = '∞'

        title_str = [f'100Δ_effective = {round(100 * effective_delta)}. Make money if S ∈ {pos_str}',
                     f'n_call = {n_call}, n_put = {n_put}, Δ_call = {delta_call:.2f}, Δ_put = {delta_put:.2f}']

        with plt.style.context('ggplot'):
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.plot(S_grid, y, 'blue', linewidth=1.5, label='Strategy Profit/Loss')
            ax.fill_between(S_grid, y, where=(y > 0), color='#007560', alpha=0.8, label='Profit')
            ax.fill_between(S_grid, y, where=(y <= 0), color='#bd1414', alpha=0.8, label='Loss')
            ax.set_title("\n".join(title_str), fontsize=16, fontweight='bold')
            ax.set_xlabel('Stock Price', fontsize=14)
            ax.set_ylabel('Pay-off at Maturity', fontsize=14)
            ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='black')
            ax.legend()
            ax.axhline(0, color='k', linewidth=1.5)
            ax.set_ylim([Y_min, Y_max])
            ax.set_xlim([S_min, S_max])
            ax.collections[0].set_alpha(0.8)
            self.canvas.draw()
    
    def fetch_data(self):
        if self.symbol_input.input_field.text() and self.x_input.input_field.text() and self.date_input.input_field.text():
            company = self.symbol_input.input_field.text()
            date = self.date_input.input_field.text()
            strike = float(self.x_input.input_field.text())

            self.fetch_stock_price(company)
            self.update_option_premiums()
            self.update_option_chain_symbol(company, date, strike)
        else:
            self.set_all_fields_to_na()
            self.display_invalid_data_message()

    def fetch_stock_price(self, company):
        if hasattr(self, 'stock_fetch_thread'):
            self.stock_fetch_thread.quit()
            self.stock_fetch_thread.wait()

        self.stock_fetch_thread = FetchStockThread(company)
        self.stock_fetch_thread.data_fetched.connect(self.update_stock_price_input)
        self.stock_fetch_thread.start()

    def update_stock_price_input(self, price, price_change, percent_change):
        if price == 'NA':
            self.set_all_fields_to_na()
            self.display_invalid_data_message()
        else:
            price_str = f"{price:.2f}" if isinstance(price, float) else "NA"
            price_change_str = f"${price_change:.2f}" if isinstance(price_change, float) else "NA"
            percent_change_str = f"{percent_change:.2f}%" if isinstance(percent_change, float) else "NA"

            self.stock_price_input.input_field.setText(price_str)
            self.price_change_input.input_field.setText(price_change_str)
            self.percent_change_input.input_field.setText(percent_change_str)
            self.update_color_based_on_change(price_change)
    
    def update_color_based_on_change(self, price_change):
        if price_change == 'NA' or not isinstance(price_change, (str, float, int)):
            color = "black"
        else:
            try:
                if isinstance(price_change, str):
                    price_change_val = float(price_change.strip('$%'))
                else:
                    price_change_val = price_change

                if price_change_val > 0:
                    color = "#007560"
                elif price_change_val < 0:
                    color = "#bd1414"
                else:
                    color = "black"
            except ValueError:
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

    def fill_premium_inputs(self, prices, open_interests, volumes):
        if prices[0] == 'NA':
            self.set_all_fields_to_na()
            self.display_invalid_data_message()
        else:
            call_premium_str = str(prices[0]) if prices[0] is not None else "NA"
            put_premium_str = str(prices[1]) if prices[1] is not None else "NA"
            call_open_interest_str = str(open_interests[0]) if open_interests and open_interests[0] is not None else "NA"
            put_open_interest_str = str(open_interests[1]) if open_interests and open_interests[1] is not None else "NA"
            call_volume_str = str(volumes[0]) if volumes and volumes[0] is not None else "NA"
            put_volume_str = str(volumes[1]) if volumes and volumes[1] is not None else "NA"

            self.call_premium_input.input_field.setText(call_premium_str)
            self.put_premium_input.input_field.setText(put_premium_str)
            self.call_open_interest_input.input_field.setText(call_open_interest_str)
            self.put_open_interest_input.input_field.setText(put_open_interest_str)
            self.call_volume_input.input_field.setText(call_volume_str)
            self.put_volume_input.input_field.setText(put_volume_str)

    def update_option_chain_symbol(self, company, date, strike):
        try:
            option_chain_symbol = get_option_chain(company, date, strike)
            self.option_chain_input.input_field.setText(option_chain_symbol)
        except Exception:
            self.option_chain_input.input_field.setText("NA")

    def set_all_fields_to_na(self):
        fields = [
            self.stock_price_input, self.price_change_input, self.percent_change_input,
            self.call_premium_input, self.put_premium_input,
            self.call_open_interest_input, self.put_open_interest_input,
            self.call_volume_input, self.put_volume_input,
            self.option_chain_input
        ]
        for field in fields:
            field.input_field.setText("NA")

    def display_invalid_data_message(self):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.text(0.5, 0.5, 'Invalid data. Please input valid parameters.', fontsize=16, fontweight='bold', ha='center', va='center')
        self.canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionStrategyVisualizer()
    sys.exit(app.exec_())
