import sys
import seaborn as sns
import matplotlib.pyplot as plt
import mplcursors
from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class SeabornPlotWithHover(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Seaborn Plot with Hover Effects in PyQt')
        self.setGeometry(100, 100, 800, 600)

        # Create a canvas
        canvas = FigureCanvas(plt.figure())
        layout = QVBoxLayout()
        widget = QWidget()
        widget.setLayout(layout)
        layout.addWidget(canvas)
        self.setCentralWidget(widget)

        # Create a seaborn plot
        data = sns.load_dataset("tips")
        ax = sns.scatterplot(x="total_bill", y="tip", data=data, ax=canvas.figure.add_subplot(111))

        # Add hover effect
        cursor = mplcursors.cursor(ax, hover=True)
        cursor.connect("add", lambda sel: sel.annotation.set_text(f'Bill: {sel.target[0]}, Tip: {sel.target[1]}'))

        # Draw the canvas
        canvas.draw()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = SeabornPlotWithHover()
    ex.show()
    sys.exit(app.exec_())
