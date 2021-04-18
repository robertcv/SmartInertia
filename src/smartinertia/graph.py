import logging
from typing import Optional

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import QRectF, Qt

from smartinertia.data import COUNTED_RUNS, START_RUNS

log = logging.getLogger(__name__)

gray_brush = pg.mkBrush(pg.mkColor(150, 150, 150))
orange_brush = pg.mkBrush(pg.mkColor(255, 77, 6))

MAX_H = 525
MAX_X = START_RUNS + COUNTED_RUNS + 1


class BarPlotWidget(pg.PlotWidget):
    def __init__(self, data):
        super().__init__()
        self.max_h = MAX_H
        self._init_plot()
        self.data = data
        self.target_line = None  # type: Optional[pg.InfiniteLine]
        log.info("Initialized bar plot.")

    def _init_plot(self):
        # add bar plot item
        self.bar_plot = pg.BarGraphItem(x=[], height=[], width=0.8)
        self.plotItem.vb.addItem(self.bar_plot)

        # set plot setting
        self.setMouseEnabled(False, False)  # disable moving plot with mouse
        self.setMenuEnabled(False)  # disable right click menu
        self.hideButtons()  # hide "A" button in bottom left corner
        self.setRange(QRectF(0.4, 0, MAX_X + 0.2, self.max_h), padding=0)

    def add_target_line(self, target):
        """Add a target line to the specified value."""
        log.info(f"Add horizontal line on {target}.")
        self.target_line = pg.InfiniteLine(pos=target, angle=0,
                                           pen=pg.mkPen(color="k", style=Qt.DashLine))
        self.plotItem.vb.addItem(self.target_line)

        # add margin on the line
        current_rect = self.viewRect()
        current_rect.setHeight(current_rect.height() * 1.3)
        self.max_h = current_rect.height()
        self.setRange(current_rect)

    def update_graph(self):
        """Get updated bar plot data and redraw the bars."""
        h = self.data.get_bar_data()
        if not h:
            return

        x = list(range(1, len(h) + 1))
        brushes = np.array([gray_brush for _ in range(len(h))])
        brushes[START_RUNS:COUNTED_RUNS + START_RUNS] = orange_brush
        self.bar_plot.setOpts(x=x, height=h, brushes=brushes)

        self.max_h = max(max(h) * 1.05, self.max_h)
        max_x = max(max(x), MAX_X) + 0.2
        self.setRange(QRectF(0.4, 0, max_x, self.max_h), padding=0)

    def clear_graph(self):
        self.bar_plot.setOpts(x=[], height=[], brushes=[])
        self.max_h = MAX_H
        self.setRange(QRectF(0.4, 0, MAX_X + 0.2, self.max_h), padding=0)
        if self.target_line is not None:
            self.plotItem.vb.removeItem(self.target_line)
            self.target_line = None
        log.info("Cleared bar plot.")
