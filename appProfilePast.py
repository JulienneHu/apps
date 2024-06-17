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
        self.update_plot() 

    def initUI(self):
        self.setWindowTitle("Option Strategy Visualizer(Past)")
        self.setGeometry(100, 100, 1357, 768)  # Set to the image width and height

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)

        control_panel = QFrame(central_widget)
        control_layout = QVBoxLayout(control_panel)
        control_panel.setMaximumWidth(300)

        self.trade_type_combo = QComboBox(control_panel)
        self.trade_type_combo.addItems(['Buy Call-Buy Put', 'Buy Call-Sell Put', 'Sell Call-Buy Put', 'Sell Call-Sell Put'])
        control_layout.addWidget(self.trade_type_combo)

        self.nCall_slider = self.create_slider('NCalls', 0, 5, 1, 1)
        control_layout.addWidget(self.nCall_slider)
        self.nPut_slider = self.create_slider('NPuts', 0, 5, 1, 1)
        control_layout.addWidget(self.nPut_slider)
        self.deltaCall = self.create_input_field('DeltaCall', '0')
        control_layout.addWidget(self.deltaCall)
        self.deltaPut = self.create_input_field('DeltaPut', '0')
        control_layout.addWidget(self.deltaPut)

        input_layout_1 = QHBoxLayout()
        self.symbol_input = self.create_input_field('Symbol', 'AAPL')
        input_layout_1.addWidget(self.symbol_input)
        input_layout_2 = QHBoxLayout()
        self.date_input = self.create_input_field('Maturity_Date', '2024-04-19')
        input_layout_2.addWidget(self.date_input)
        input_layout_3 = QHBoxLayout()
        self.x_input = self.create_input_field('Strike_Price', '150')
        input_layout_3.addWidget(self.x_input)
        input_layout_4 = QHBoxLayout()
        self.call_premium_input = self.create_input_field('C', '9.8')
        self.put_premium_input = self.create_input_field('P', '14.5')
        input_layout_4.addWidget(self.call_premium_input)
        input_layout_4.addWidget(self.put_premium_input)
        input_layout_5 = QHBoxLayout()
        self.stock_price_input = self.create_input_field('SPrice', '150')
        self.stock_range_input = self.create_input_field('SRange', '0.25')
        input_layout_5.addWidget(self.stock_price_input)
        input_layout_5.addWidget(self.stock_range_input)
        input_layout_6 = QHBoxLayout()
        self.y_min_input = self.create_input_field('Y_Min', '-1000')
        self.y_max_input = self.create_input_field('Y_Max', '1000')
        input_layout_6.addWidget(self.y_min_input)
        input_layout_6.addWidget(self.y_max_input)

        control_layout.addLayout(input_layout_1)
        control_layout.addLayout(input_layout_2)
        control_layout.addLayout(input_layout_3)
        control_layout.addLayout(input_layout_4)
        control_layout.addLayout(input_layout_5)
        control_layout.addLayout(input_layout_6)
        grid_layout.addWidget(control_panel, 0, 0)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        
        self.canvas.setMinimumWidth(950)  # Make plot area adequately wide
        grid_layout.addWidget(self.canvas, 0, 1)

        self.toolbar = NavigationToolbar(self.canvas, self)
        grid_layout.addWidget(self.toolbar, 1, 1)  # Add the navigation toolbar below the canvas

        grid_layout.setColumnStretch(0, 35)  # Less stretch for the controls column
        grid_layout.setColumnStretch(1, 65)  # More stretch for the plot column

        # Connect changes in UI to update the plot
        self.trade_type_combo.currentIndexChanged.connect(self.update_plot)
        self.nCall_slider.slider.valueChanged.connect(self.update_plot)
        self.nPut_slider.slider.valueChanged.connect(self.update_plot)
        self.deltaCall.input_field.returnPressed.connect(self.update_plot)
        self.deltaPut.input_field.returnPressed.connect(self.update_plot)
        self.x_input.input_field.returnPressed.connect(self.update_plot)
        self.call_premium_input.input_field.returnPressed.connect(self.update_plot)
        self.put_premium_input.input_field.returnPressed.connect(self.update_plot)
        self.stock_price_input.input_field.returnPressed.connect(self.update_plot)
        self.stock_range_input.input_field.returnPressed.connect(self.update_plot)
        self.y_min_input.input_field.returnPressed.connect(self.update_plot)
        self.y_max_input.input_field.returnPressed.connect(self.update_plot)

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


    def create_input_field(self, label, default_value):
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)  # Keep margins minimal
        layout.setSpacing(10)
        
        lbl = QLabel(label)
        lbl.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)  # Adjust this line
        
        input_field = QLineEdit(default_value)
        input_field.setAlignment(Qt.AlignCenter)
        input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Ensure input field can expand
        
        input_field.returnPressed.connect(self.update_plot)
        
        layout.addWidget(lbl)
        layout.addWidget(input_field)
        container.setLayout(layout)
        container.input_field = input_field
        return container



    def update_plot(self):
        # Retrieve values from UI components
        n_call = self.nCall_slider.slider.value()
        n_put = self.nPut_slider.slider.value()
        delta_call = float(self.deltaCall.input_field.text()) 
        delta_put = -abs(float(self.deltaPut.input_field.text()))
        stock_price = float(self.stock_price_input.input_field.text())
        X = float(self.x_input.input_field.text())
        call_premium = float(self.call_premium_input.input_field.text())
        put_premium = float(self.put_premium_input.input_field.text())
        stock_range = float(self.stock_range_input.input_field.text())
        Y_min = float(self.y_min_input.input_field.text())
        Y_max = float(self.y_max_input.input_field.text())

        # Calculate values
        S_min = np.floor(stock_price * (1 - stock_range))
        S_max = np.ceil(stock_price * (1 + stock_range))
        S_grid = np.arange(S_min, S_max + 1, 0.1)
        call_at_maturity = np.maximum(S_grid - X, 0)
        put_at_maturity = np.maximum(X - S_grid, 0)

        # Logic for plotting based on trade type
        trade_type = self.trade_type_combo.currentText()
        if trade_type == 'Buy Call-Buy Put':
            y_option = n_call * (call_at_maturity - call_premium) + n_put * (put_at_maturity - put_premium)
            y_stock = n_call * delta_call * (S_grid - stock_price) + n_put * delta_put * (S_grid - stock_price)
            effective_delta = -n_call * delta_call - n_put * delta_put
        if trade_type == 'Buy Call-Sell Put':
            y_option = n_call * (call_at_maturity - call_premium) - n_put * (put_at_maturity - put_premium)
            y_stock = n_call * delta_call * (S_grid - stock_price) - n_put * delta_put * (S_grid - stock_price)
            effective_delta = -n_call * delta_call + n_put * delta_put
        if trade_type == 'Sell Call-Buy Put':
            y_option = -n_call * (call_at_maturity - call_premium) + n_put * (put_at_maturity - put_premium)
            y_stock = -n_call * delta_call * (S_grid - stock_price) + n_put * delta_put * (S_grid - stock_price)
            effective_delta = n_call * delta_call - n_put * delta_put
        if trade_type == 'Sell Call-Sell Put': 
            y_option = -n_call * (call_at_maturity - call_premium) - n_put * (put_at_maturity - put_premium)
            y_stock = -n_call * delta_call * (S_grid - stock_price) - n_put * delta_put * (S_grid - stock_price)
            effective_delta = n_call * delta_call + n_put * delta_put

        # Plotting logic
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

        
        # Inside your update_plot method, before plotting:
        with plt.style.context('ggplot'):
            self.figure.clear()
            ax = self.figure.add_subplot(111)

            # Plot with a thicker line and use a different color for visibility
            ax.plot(S_grid, y, 'blue', linewidth=1.5, label='Strategy Profit/Loss')

            # Add a fill between
            ax.fill_between(S_grid, y, where=(y > 0), color='#bd1414', alpha=0.8, label='Profit')
            ax.fill_between(S_grid, y, where=(y <= 0), color='#007560', alpha=0.8, label='Loss')

            # Improve title and label aesthetics
            ax.set_title("\n".join(title_str), fontsize=16, fontweight='bold')
            ax.set_xlabel('Stock Price', fontsize=14)
            ax.set_ylabel('Pay-off at Maturity', fontsize=14)

            # Add gridlines
            ax.grid(True, which='major', linestyle='--', linewidth='0.5', color='black')

            # Add legend
            ax.legend()

            ax.axhline(0, color='k', linewidth=1.5)
            ax.set_ylim([Y_min, Y_max])
            ax.set_xlim([S_min, S_max])

            # Change the transparency of the fill_between
            ax.collections[0].set_alpha(0.8)

            self.canvas.draw()
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = OptionStrategyVisualizer()
    sys.exit(app.exec_())