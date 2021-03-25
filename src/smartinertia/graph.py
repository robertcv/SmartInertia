import logging

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QRectF

from smartinertia.data import COUNTED_RUNS, START_RUNS

log = logging.getLogger(__name__)

gray_brush = pg.mkBrush(pg.mkColor(150, 150, 150))
orange_brush = pg.mkBrush(pg.mkColor(255, 77, 6))

MAX_H = 500
MAX_X = START_RUNS + COUNTED_RUNS + 1


class BarPlotWidget(pg.PlotWidget):
    def __init__(self, data):
        super().__init__()
        self._init_plot()
        self.data = data
        log.info("Initialized bar plot.")

    def _init_plot(self):
        # add bar plot item
        self.bar_plot = pg.BarGraphItem(x=[], height=[], width=0.8)
        self.plotItem.vb.addItem(self.bar_plot)

        # set plot setting
        self.setMouseEnabled(False, False)  # disable moving plot with mouse
        self.setMenuEnabled(False)  # disable right click menu
        self.hideButtons()  # hide "A" button in bottom left corner
        self.setRange(QRectF(0.4, 0, MAX_X + 0.2, MAX_H * 1.05), padding=0)

    def update_graph(self):
        """Get updated bar plot data and redraw the bars."""
        h = self.data.get_bar_data()
        if not h:
            return

        x = list(range(1, len(h) + 1))
        brushes = np.array([gray_brush for _ in range(len(h))])
        brushes[START_RUNS:COUNTED_RUNS + START_RUNS] = orange_brush
        self.bar_plot.setOpts(x=x, height=h, brushes=brushes)

        max_h = max(max(h), MAX_H) * 1.05
        max_x = max(max(x), MAX_X) + 0.2
        self.setRange(QRectF(0.4, 0, max_x, max_h), padding=0)

    def clear_graph(self):
        self.bar_plot.setOpts(x=[], height=[], brushes=[])
        log.info("Cleared bar plot.")
