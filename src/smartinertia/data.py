import logging
from collections import namedtuple
from typing import Optional

import numpy as np
from scipy.signal import butter, lfilter

from smartinertia.dialogs import RunConf

MIN_FREQ = 1
N_BEFORE = 10
SAMPLING_FREQ = 1000
RADIUS = 0.015

log = logging.getLogger(__name__)

DataSet = namedtuple('DataSet', ['x', 'y'])


def derivative_gradient(data: DataSet) -> DataSet:
    """Calculate the numerical gradient."""
    x = np.array(data.x)
    y = np.array(data.y)
    return DataSet(x=x, y=np.gradient(y, x))


def interpolation(data: DataSet) -> DataSet:
    """Interpolate data to get equal sized spacings between points."""
    space = 1 / SAMPLING_FREQ
    xp = np.array(data.x)
    yp = np.array(data.y)
    x = np.arange(xp[0], xp[-1] + space, space)
    y = np.interp(x, xp, yp)
    return DataSet(x=x, y=y)


def butter_lowpass_filter(data: DataSet, cutoff: float) -> DataSet:
    """Apply lowpass filter with cutoff frequency."""
    x = np.array(data.x)
    y = np.array(data.y)
    b, a = butter(5, cutoff, btype='lowpass', output='ba', fs=SAMPLING_FREQ)
    y = lfilter(b, a, y)
    return DataSet(x=x, y=y)


class Data:
    """Holding incoming data and processing utilities."""
    def __init__(self):
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.new_bar_pos = []
        self.descending_freq = False
        self.run_started = False
        self.run_conf = None  # type: Optional[RunConf]

    def set_run_conf(self, conf: RunConf):
        self.run_conf = conf

    def add_new(self, point: tuple):
        x, y = point

        if not self.run_started:
            if y > MIN_FREQ:
                # log.debug(f"Run started!")
                self.bar_h.append(0)
                self.new_bar_pos.append(0)
                self.run_started = True
            else:
                # log.debug(f"Waiting for y to raise! Currently, y={y:.3f}")
                return

        self.raw_x.append(x)
        self.raw_y.append(y)

        if len(self.raw_y) > N_BEFORE:
            # log.debug(f"We have more than {N_BEFORE} samples.")
            min_before = min(self.raw_y[-N_BEFORE:-1])
            # log.debug(f"min_before={min_before:.3f}, y={y:.3f}")

            if self.descending_freq and y > min_before:
                self.bar_h.append(0)
                self.new_bar_pos.append(x)
                self.descending_freq = False
                # log.debug(f"self.descending_freq = False")

            if not self.descending_freq and min_before > y:
                self.descending_freq = True
                # log.debug(f"self.descending_freq = True")

            power = self.calc_recent_power()
            self.bar_h[-1] = max(self.bar_h[-1], power)
            # log.debug(f"Bar values {self.bar_h}")

    def calc_recent_power(self):
        """Calculate power using recent samples."""
        filtered_data = butter_lowpass_filter(
            interpolation(DataSet(x=self.raw_x[-N_BEFORE:], y=self.raw_y[-N_BEFORE:])),
            cutoff=200
        )

        frequency = filtered_data.y
        angular_velocity = frequency * 2 * np.pi
        linear_velocity = angular_velocity * RADIUS

        angular_acceleration = derivative_gradient(DataSet(x=filtered_data.x,
                                                           y=angular_velocity)).y
        # linear_acceleration = derivative_gradient(DataSet(x=filtered_data.x,
        #                                                   y=linear_velocity)).y

        force = np.abs(angular_acceleration * (self.run_conf.load / RADIUS))
        force = force + (9.81 * self.run_conf.weight)

        power = force * linear_velocity
        return power[-1]

    def get_bar_data(self):
        return self.bar_h

    def save_report(self):
        pass

    def show_report(self) -> str:
        pass

    def clear(self):
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.new_bar_pos = []
        self.descending_freq = False
        self.run_started = False
