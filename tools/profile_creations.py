from PyQt5.QtWidgets import (QApplication, QMainWindow, QSlider, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
                             QGridLayout, QFrame, QSizePolicy)  # Added QSizePolicy here
from PyQt5.QtCore import (Qt, QThread, pyqtSignal)

def create_slider(label, min_val, max_val, precision, default_val):
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
    layout.addWidget(lbl)
    layout.addWidget(slider)
    container.setLayout(layout)
    container.slider = slider  # Store the slider in the container for access
    return container


def create_input_field(label, default_value, editable=True):
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
    
    layout.addWidget(lbl)
    layout.addWidget(input_field)
    container.setLayout(layout)
    container.input_field = input_field
    return container
