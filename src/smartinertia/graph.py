import pyqtgraph as pg


class BarPlotWidget(pg.PlotWidget):

    def __init__(self, data):
        super().__init__()
        self.data = data

    def update_graph(self):
        pass

    def clear(self):
        pass

