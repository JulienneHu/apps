import sys
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
        plt.style.use('ggplot')

    def initUI(self):
        self.setWindowTitle("Option Strategy Visualizer")
        self.setGeometry(100, 100, 1357, 768)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        self.x_inputs = []
        self.call_premium_inputs = []
        self.put_premium_inputs = []
        self.call_open_interest_inputs = []
        self.put_open_interest_inputs = []
        self.call_volume_inputs = []
        self.put_volume_inputs = []
            
        # Main control panels
        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)
        control_panel.setMaximumWidth(400)
        #Trade Type Combo Box
        self.trade_type_combo = QComboBox(control_panel)
        self.trade_type_combo.addItems(['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])
        control_layout.addWidget(self.trade_type_combo)

        # Sliders
        self.nCall_slider = self.create_slider('N1Calls', 0, 5, 1, 1) 
        control_layout.addWidget(self.nCall_slider)

        self.nPut_slider = self.create_slider('N1Puts', 0, 5, 1, 1)
        control_layout.addWidget(self.nPut_slider)

        self.deltaCall = self.create_input_field('Delta1Call','0') 
        control_layout.addWidget(self.deltaCall)

        self.deltaPut = self.create_input_field('Delta1Put', '0')
        control_layout.addWidget(self.deltaPut)

        # Input Fields 
        input_layout_1 = QHBoxLayout()
        self.x_input = self.create_input_field('Strike_Price', '150')
        self.x_inputs.append(self.x_input)
        input_layout_1.addWidget(self.x_input)
           
        input_layout_2 = QHBoxLayout()
        self.call_premium_input = self.create_input_field('C1', '9.8', False)
        self.call_premium_inputs.append(self.call_premium_input)
        input_layout_2.addWidget(self.call_premium_input)
        
        input_layout_3 = QHBoxLayout()
        self.call_open_interest_input = self.create_input_field('C1_OI', '0', False)
        self.call_open_interest_inputs.append(self.call_open_interest_input)
        input_layout_3.addWidget(self.call_open_interest_input)
        
        input_layout_4 = QHBoxLayout()
        self.call_volume_input = self.create_input_field('C1_Vol', '0', False)
        self.call_volume_inputs.append(self.call_volume_input)
        input_layout_4.addWidget(self.call_volume_input)
        
        input_layout_5 = QHBoxLayout()
        self.put_premium_input = self.create_input_field('P1', '14.5', False)  
        self.put_premium_inputs.append(self.put_premium_input)   
        input_layout_5.addWidget(self.put_premium_input)
        
        input_layout_6 = QHBoxLayout()
        self.put_open_interest_input = self.create_input_field('P1_OI', '0', False)
        self.put_open_interest_inputs.append(self.put_open_interest_input)
        input_layout_6.addWidget(self.put_open_interest_input)
        
        input_layout_7 = QHBoxLayout()
        self.put_volume_input = self.create_input_field('P1_Vol', '0', False) 
        self.put_volume_inputs.append(self.put_volume_input)
        input_layout_7.addWidget(self.put_volume_input)
        
        # Add input layouts to the main control layout
        control_layout.addLayout(input_layout_1)
        control_layout.addLayout(input_layout_2)
        control_layout.addLayout(input_layout_3)
        control_layout.addLayout(input_layout_4)
        control_layout.addLayout(input_layout_5)
        control_layout.addLayout(input_layout_6)
        control_layout.addLayout(input_layout_7)

        grid_layout.addWidget(control_panel, 0, 0)

        right_control_panel = QFrame(central_widget)
        right_control_layout = QVBoxLayout(right_control_panel)
        right_control_panel.setMaximumWidth(400)
        # Right Trade Type Combo Box
        # Right Trade Type Combo Box
        self.right_trade_type_combo = QComboBox(right_control_panel)
        self.right_trade_type_combo.addItems(['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])
        right_control_layout.addWidget(self.right_trade_type_combo)

        # Right Sliders
        # Sliders
        self.n2Call_slider = self.create_slider('N2Calls', 0, 5, 1, 1) 
        right_control_layout.addWidget(self.n2Call_slider)

        self.n2Put_slider = self.create_slider('N2Puts', 0, 5, 1, 1)
        right_control_layout.addWidget(self.n2Put_slider)

        self.delta2Call = self.create_input_field('Delta2Call', '0') 
        right_control_layout.addWidget(self.delta2Call)

        self.delta2Put = self.create_input_field('Delta2Put', '0')
        right_control_layout.addWidget(self.delta2Put)

        # Right Input Fields
        right_input_layout_0 = QHBoxLayout()
        self.x2_input = self.create_input_field('Strike_Price2', '150')
        self.x_inputs.append(self.x2_input)
        right_input_layout_0.addWidget(self.x2_input)
        
        right_input_layout_1 = QHBoxLayout()
        self.call_premium2_input = self.create_input_field('C2', '9.8', False)   
        self.call_premium_inputs.append(self.call_premium2_input)
        right_input_layout_1.addWidget(self.call_premium2_input)
        
        right_input_layout_2 = QHBoxLayout()
        self.call_open_interest2_input = self.create_input_field('C2_OI', '0', False)
        self.call_open_interest_inputs.append(self.call_open_interest2_input)
        right_input_layout_2.addWidget(self.call_open_interest2_input)
        
        right_input_layout_3 = QHBoxLayout()
        self.call_volume2_input = self.create_input_field('C2_Vol', '0', False)
        self.call_volume_inputs.append(self.call_volume2_input)
        right_input_layout_3.addWidget(self.call_volume2_input)
        
        right_input_layout_4 = QHBoxLayout()
        self.put_premium2_input = self.create_input_field('P2', '14.5', False)
        self.put_premium_inputs.append(self.put_premium2_input)    
        right_input_layout_4.addWidget(self.put_premium2_input)
        
        right_input_layout_5 = QHBoxLayout()
        self.put_open_interest2_input = self.create_input_field('P2_OI', '0', False)
        self.put_open_interest_inputs.append(self.put_open_interest2_input)
        right_input_layout_5.addWidget(self.put_open_interest2_input)
        
        right_input_layout_6 = QHBoxLayout()
        self.put_volume2_input = self.create_input_field('P2_Vol', '0', False) 
        self.put_volume_inputs.append(self.put_volume2_input)
        right_input_layout_6.addWidget(self.put_volume2_input)
        
        right_control_layout.addLayout(right_input_layout_0)
        right_control_layout.addLayout(right_input_layout_1)
        right_control_layout.addLayout(right_input_layout_2)
        right_control_layout.addLayout(right_input_layout_3)
        right_control_layout.addLayout(right_input_layout_4)
        right_control_layout.addLayout(right_input_layout_5)
        right_control_layout.addLayout(right_input_layout_6)    
        grid_layout.addWidget(right_control_panel, 0, 1)

        # Common controls across left and right panels
        fetch_layout = QHBoxLayout()
        self.symbol_input = self.create_input_field('Symbol', 'AAPL')
        fetch_layout.addWidget(self.symbol_input)
        self.date_input = self.create_input_field('Maturity_Date', '2024-05-17')
        fetch_layout.addWidget(self.date_input)
        self.fetch_data_button = QPushButton('Fetch Data / Refresh', control_panel)
        self.fetch_data_button.clicked.connect(self.fetch_data)
        self.fetch_data_button.clicked.connect(self.update_plot)
        fetch_layout.addWidget(self.fetch_data_button)
        grid_layout.addLayout(fetch_layout, 1, 0, 1, 2)  # Spans two columns

        stock_info_layout = QHBoxLayout()
        self.stock_price_input = self.create_input_field('SPrice', '150', False)
        self.price_change_input = self.create_input_field('Real', '0', False)
        self.percent_change_input = self.create_input_field('Pct', '0', False)
        stock_info_layout.addWidget(self.stock_price_input)
        stock_info_layout.addWidget(self.price_change_input)
        stock_info_layout.addWidget(self.percent_change_input)
        grid_layout.addLayout(stock_info_layout, 2, 0, 1, 2)  # Spans two columns
        
        # plot size
        plot_size_layout = QHBoxLayout()
        self.y_min_input = self.create_input_field('Y_Min', '-5000')
        self.y_max_input = self.create_input_field('Y_Max', '5000')
        self.stock_range_input = self.create_input_field('SRange', '0.2')
        plot_size_layout.addWidget(self.y_min_input)
        plot_size_layout.addWidget(self.y_max_input)
        plot_size_layout.addWidget(self.stock_range_input)
        grid_layout.addLayout(plot_size_layout, 3, 0, 1, 2)  # Spans two columns
        
        # Adjust column stretch factors
        grid_layout.setColumnStretch(0, 20)
        grid_layout.setColumnStretch(1, 20)
        grid_layout.setColumnStretch(2, 60)  # For the plot area

        # Plotting area
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumWidth(800)
        grid_layout.addWidget(self.canvas, 0, 2, 4, 1)  
        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 4, 2)

        # connect signals to update method
        self.x_input.input_field.returnPressed.connect(self.update_plot)
        self.x2_input.input_field.returnPressed.connect(self.update_plot)
        self.symbol_input.input_field.returnPressed.connect(self.update_plot)
        self.date_input.input_field.returnPressed.connect(self.update_plot)
        
        self.nCall_slider.slider.valueChanged.connect(self.update_plot)
        self.nPut_slider.slider.valueChanged.connect(self.update_plot)
        self.deltaCall.input_field.returnPressed.connect(self.update_plot)
        self.deltaPut.input_field.returnPressed.connect(self.update_plot)
        
        
        self.call_premium_input.input_field.textChanged.connect(self.update_plot)
        self.put_premium_input.input_field.textChanged.connect(self.update_plot)
        self.stock_price_input.input_field.textChanged.connect(self.update_plot)
        
        self.y_min_input.input_field.returnPressed.connect(self.update_plot)
        self.y_max_input.input_field.returnPressed.connect(self.update_plot)
        self.stock_range_input.input_field.returnPressed.connect(self.update_plot)
        
        
        self.call_premium2_input.input_field.textChanged.connect(self.update_plot)
        self.put_premium2_input.input_field.textChanged.connect(self.update_plot)
        
        self.n2Call_slider.slider.valueChanged.connect(self.update_plot)
        self.n2Put_slider.slider.valueChanged.connect(self.update_plot)
        self.delta2Call.input_field.returnPressed.connect(self.update_plot)
        self.delta2Put.input_field.returnPressed.connect(self.update_plot)
        
        self.fetch_data_button.clicked.connect(self.update_plot)
        self.trade_type_combo.currentIndexChanged.connect(self.update_plot)
        self.right_trade_type_combo.currentIndexChanged.connect(self.update_plot)
        
        self.show()


    def create_slider(self, label, min_val, max_val, precision, default_val):
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
        
        if 'NA'in [self.stock_price_input.input_field.text(), self.call_premium_input.input_field.text(), self.put_premium_input.input_field.text(), self.call_premium2_input.input_field.text(), self.put_premium2_input.input_field.text()]:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Options does not exist. Please input valid parameters', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return
        
        try:
            n1_call = self.nCall_slider.slider.value()
            n1_put = self.nPut_slider.slider.value()
            Delta1_call = float(self.deltaCall.input_field.text())
            Delta1_put = -abs(float(self.deltaPut.input_field.text()))
            X1 = float(self.x_input.input_field.text())
            call1_premium = float(self.call_premium_input.input_field.text())
            put1_premium = float(self.put_premium_input.input_field.text())
            
            
            n2_call = self.n2Call_slider.slider.value()
            n2_put = self.n2Put_slider.slider.value()
            Delta2_call = float(self.delta2Call.input_field.text())
            Delta2_put = -abs(float(self.delta2Put.input_field.text()))
            X2 = float(self.x2_input.input_field.text())
            call2_premium = float(self.call_premium2_input.input_field.text())
            put2_premium = float(self.put_premium2_input.input_field.text())
            
            stock_price = float(self.stock_price_input.input_field.text())
            stock_range = float(self.stock_range_input.input_field.text())
            Y_min = float(self.y_min_input.input_field.text())
            Y_max = float(self.y_max_input.input_field.text())
        except ValueError:
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, 'Options does not exist. Please input valid parameters', fontsize=16, fontweight='bold', ha='center', va='center')
            self.canvas.draw()
            return

        # Calculate values
        S_min = np.floor(stock_price * (1 - stock_range))
        S_max = np.ceil(stock_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max + 1, 1)
        call1_at_maturity = np.maximum(S_grid - X1, 0)
        put1_at_maturity = np.maximum(X1 - S_grid, 0)
        call2_at_maturity = np.maximum(S_grid - X2, 0)
        put2_at_maturity = np.maximum(X2 - S_grid, 0)

        # Logic for plotting based on trade type
        trade1_type = self.trade_type_combo.currentText()
        if trade1_type == 'Buy Call-Buy Put':
                    y1_option = n1_call*(call1_at_maturity - call1_premium) + n1_put*(put1_at_maturity - put1_premium);
                    y1_stock  = n1_call*Delta1_call*(stock_price - S_grid) + n1_put*Delta1_put*(stock_price - S_grid);
                    Effective_Delta1 = -n1_call*Delta1_call - n1_put*Delta1_put; 
        elif trade1_type =='Buy Call-Sell Put':
                    y1_option = n1_call*(call1_at_maturity - call1_premium) + n1_put*(put1_premium - put1_at_maturity);
                    y1_stock  = n1_call*Delta1_call*(stock_price - S_grid) + n1_put*Delta1_put*(S_grid - stock_price);
                    Effective_Delta1 = -n1_call*Delta1_call + n1_put*Delta1_put; 
        elif trade1_type == 'Sell Call-Buy Put':
                    y1_option = n1_call*(call1_premium - call1_at_maturity) + n1_put*(put1_at_maturity - put1_premium);
                    y1_stock  = n1_call*Delta1_call*(S_grid - stock_price) + n1_put*Delta1_put*(stock_price - S_grid);
                    Effective_Delta1 = n1_call*Delta1_call - n1_put*Delta1_put;
        elif trade1_type == 'Sell Call-Sell Put':
                    y1_option = n1_call*(call1_premium - call1_at_maturity) + n1_put*(put1_premium - put1_at_maturity);
                    y1_stock  = n1_call*Delta1_call*(S_grid - stock_price) + n1_put*Delta1_put*(S_grid - stock_price);
                    Effective_Delta1 = n1_call*Delta1_call + n1_put*Delta1_put;
        
        trade2_type = self.right_trade_type_combo.currentText()
        if trade2_type == 'Buy Call-Buy Put':
                    y2_option = n2_call*(call2_at_maturity - call2_premium) + n2_put*(put2_at_maturity - put2_premium);
                    y2_stock  = n2_call*Delta2_call*(stock_price - S_grid) + n2_put*Delta2_put*(stock_price - S_grid);
                    Effective_Delta2 = -n2_call*Delta2_call - n2_put*Delta2_put;
        elif trade2_type== 'Buy Call-Sell Put':
                    y2_option = n2_call*(call2_at_maturity - call2_premium) + n2_put*(put2_premium - put2_at_maturity);
                    y2_stock  = n2_call*Delta2_call*(stock_price - S_grid) + n2_put*Delta2_put*(S_grid - stock_price);
                    Effective_Delta2 = -n2_call*Delta2_call + n2_put*Delta2_put;
        elif trade2_type == 'Sell Call-Buy Put':
                    y2_option = n2_call*(call2_premium - call2_at_maturity) + n2_put*(put2_at_maturity - put2_premium);
                    y2_stock  = n2_call*Delta2_call*(S_grid - stock_price) + n2_put*Delta2_put*(stock_price - S_grid);
                    Effective_Delta2 = n2_call*Delta2_call - n2_put*Delta2_put;
        elif trade2_type == 'Sell Call-Sell Put':
                    y2_option = n2_call*(call2_premium - call2_at_maturity) + n2_put*(put2_premium - put2_at_maturity);
                    y2_stock  = n2_call*Delta2_call*(S_grid - stock_price) + n2_put*Delta2_put*(S_grid - stock_price);
                    Effective_Delta2 = n2_call*Delta2_call + n2_put*Delta2_put;
        
        y2 = 100*(y2_option + y2_stock);y1 = 100*(y1_option + y1_stock);

        # Plotting logic
        y = y1 + y2
        Effective_Delta = Effective_Delta1 + Effective_Delta2
        yp = np.maximum(y, 0)
        y_neg = np.where(yp == 0)[0]
        y_pos = np.where(yp > 0)[0]
        if len(y_neg) != 0 and len(y_pos) != 0:
            if y_neg[0] > 0 and y_neg[-1] < len(S_grid) - 1:
                pos_str = f'(0, {np.ceil(S_grid[y_neg[0] - 1])}) and ({np.floor(S_grid[y_neg[-1] + 1])}, ∞)'
            else:
                pos_range = S_grid[y_pos]
                if y_pos[0] == 0:
                    pos_str = f'(0, {np.ceil(pos_range[-1])})'
                else:
                    pos_str = f'({np.floor(pos_range[0])}, {np.ceil(pos_range[-1])})'
        elif len(y_neg) == 0:
            pos_str = '(0, ∞)'
        else:
            pos_str = '∞'

        title_str = [f'100Δ_effective = {round(100 * Effective_Delta)}. Make money if S ∈ {pos_str}',
                     f'n1_call = {n1_call}, n1_put = {n1_put}, n2_call = {n2_call}, n2_put = {n2_put}',
                     f'Δ1_call = {Delta1_call:.2f}, Δ1_put = {Delta1_put:.2f}, Δ2_call = {Delta2_call:.2f}, Δ2_put = {Delta2_put:.2f}']

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(S_grid, y1, 'r-', label='Strategy 1 Outcome', linewidth=2)
        ax.plot(S_grid, y2, 'm-', label='Strategy 2 Outcome', linewidth=2)
        ax.plot(S_grid, y, 'b-', label='Combined Strategy Outcome', linewidth=2)

        ax.set_title("\n".join(title_str), fontsize=16, fontweight='bold')
        ax.set_xlabel('Stock Price', fontsize=14)
        ax.set_ylabel('Pay-off at Maturity', fontsize=14)
        ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='black')
        ax.legend()
        ax.axhline(0, color='k', linewidth=1.5)
        ax.set_ylim([Y_min, Y_max])
        ax.set_xlim([S_min, S_max])
        self.canvas.draw()
    
 
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
        else:
            print("Please ensure all fields (symbol, strike price, and maturity date) are filled.")
        
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
        # Format display strings here and handle 'NA' values
        price_str = f"{price:.2f}" if price != 'NA' else 'NA'
        price_change_str = f"${price_change:.2f}" if price_change != 'NA' else 'NA'
        percent_change_str = f"{percent_change:.2f}%" if percent_change != 'NA' else 'NA'

        self.stock_price_input.input_field.setText(price_str)
        self.price_change_input.input_field.setText(price_change_str)
        self.percent_change_input.input_field.setText(percent_change_str)

        # Pass the formatted string for color update
        self.update_color_based_on_change(price_change_str)


    def update_color_based_on_change(self, price_change):
        # Update text color based on price_change, checking if it's not 'NA'
        try:
            price_change_val = float(price_change.strip('$%'))
            if price_change_val > 0:
                color = "#007560"  # green
            elif price_change_val < 0:
                color = "#bd1414"  # red
            else:
                color = "black"
        except ValueError:
            color = "black"
        
        self.stock_price_input.input_field.setStyleSheet(f"color: {color};")
        self.price_change_input.input_field.setStyleSheet(f"color: {color};")
        self.percent_change_input.input_field.setStyleSheet(f"color: {color};")

    def start_option_fetch_thread(self, company, date, strike, index):
        thread = FetchOptionThread(company, date, strike)
        thread.data_fetched.connect(lambda prices, open_interests, volumes: self.fill_premium_inputs(prices, open_interests, volumes, index))
        thread.finished.connect(lambda: self.option_fetch_threads.remove(thread))  # Ensure the thread is removed from the list once finished
        thread.start()
        self.option_fetch_threads.append(thread) 
                
    def update_option_premiums(self):
        company = self.symbol_input.input_field.text()
        date = self.date_input.input_field.text()
        
        for i, x_input in enumerate(self.x_inputs):
            strike = float(x_input.input_field.text())
            self.start_option_fetch_thread(company, date, strike, i)

    def fill_premium_inputs(self, prices, open_interests, volumes, index):
        if len(prices) > 0:
            self.call_premium_inputs[index].input_field.setText(prices[0] if prices[0] is not None else 'NA')
        else:
            self.call_premium_inputs[index].input_field.setText('NA')

        if len(prices) > 1:
            self.put_premium_inputs[index].input_field.setText(prices[1] if prices[1] is not None else 'NA')
        else:
            self.put_premium_inputs[index].input_field.setText('NA')

        if len(open_interests) > 0:
            self.call_open_interest_inputs[index].input_field.setText(open_interests[0] if open_interests[0] is not None else 'NA')
        else:
            self.call_open_interest_inputs[index].input_field.setText('NA')

        if len(open_interests) > 1:
            self.put_open_interest_inputs[index].input_field.setText(open_interests[1] if open_interests[1] is not None else 'NA')
        else:
            self.put_open_interest_inputs[index].input_field.setText('NA')

        if len(volumes) > 0:
            self.call_volume_inputs[index].input_field.setText(volumes[0] if volumes[0] is not None else 'NA')
        else:
            self.call_volume_inputs[index].input_field.setText('NA')

        if len(volumes) > 1:
            self.put_volume_inputs[index].input_field.setText(volumes[1] if volumes[1] is not None else 'NA')
        else:
            self.put_volume_inputs[index].input_field.setText('NA')


    
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
    sys.exit(app.exec_())