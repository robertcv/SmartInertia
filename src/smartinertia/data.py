import logging
from collections import namedtuple
from typing import Optional

import numpy as np
from PyQt5.QtWidgets import QMessageBox
from scipy.signal import argrelmax, butter, filtfilt

from smartinertia.dialogs import ReportDialog, RunConf
from smartinertia.save import save_data, save_run

START_RUNS = 3
COUNTED_RUNS = 6

MIN_FREQ_START = 2
SAMPLES_FOR_FILTER = 30

SAMPLING_FREQ = 1000
CUTOFF_FREQ = 5
RADIUS = 0.015

log = logging.getLogger(__name__)

DataSet = namedtuple('DataSet', ['x', 'y'])
RunData = namedtuple("RunData", [
    "v_con_max", "v_ecc_max", "v_con_mean", "v_ecc_mean",
    "f_con_max", "f_ecc_max", "f_con_mean", "f_ecc_mean",
    "p_con_max", "p_ecc_max", "p_con_mean", "p_ecc_mean",
])


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
    y = filtfilt(b, a, y)
    return DataSet(x=x, y=y)


def find_second_peak(segment: np.ndarray) -> int:
    """Find maximum with inequality on both sides or normal max."""
    global_max = segment.max()
    potential_max = segment.max()
    potential_maxes = sorted(argrelmax(segment, order=1)[0])
    if potential_maxes:
        potential_max = segment[potential_maxes[-1]]
        if len(potential_maxes) > 1 and potential_max == global_max:
            potential_max = segment[potential_maxes[-2]]
        if potential_max / global_max < 0.9:
            potential_max = global_max
    return potential_max


class Data:
    """Holding incoming data and processing utilities."""
    def __init__(self, master):
        self.master = master
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.new_bar_time = []
        self.descending_freq = False
        self.run_started = False
        self.run_conf = None  # type: Optional[RunConf]
        self.run_saved = False

    def set_run_conf(self, conf: RunConf):
        self.run_conf = conf

    def add_new(self, point: tuple):
        x, y = point
        log.debug(f"point: {point}")

        if not self.run_started:
            if y > MIN_FREQ_START:
                log.debug(f"Run started!")
                self.bar_h.append(0)
                self.new_bar_time.append(0)
                self.run_started = True
            else:
                log.debug(f"Waiting for y to raise! Currently, y={y:.3f}")
                return

        self.raw_x.append(x)
        self.raw_y.append(y)

        if not self.descending_freq and y < 0.9:
            self.descending_freq = True
            log.debug(f"t={x} self.descending_freq = True")

        if self.descending_freq and y > 1:
            self.bar_h.append(0)
            self.new_bar_time.append(x)
            self.descending_freq = False
            log.debug(f"t={x} self.descending_freq = False")

        power = self.calc_recent_power()
        self.bar_h[-1] = max(self.bar_h[-1], power)
        log.debug(f"Bar values {self.bar_h}")

    def calc_recent_power(self) -> float:
        """Calculate power using recent samples."""
        if len(self.raw_x) < SAMPLES_FOR_FILTER or (self.raw_x[-1] - self.raw_x[0]) < 0.2:
            return 0

        inter_data = interpolation(DataSet(x=self.raw_x[-SAMPLES_FOR_FILTER:],
                                           y=self.raw_y[-SAMPLES_FOR_FILTER:]))
        try:
            filtered_data = butter_lowpass_filter(inter_data, cutoff=CUTOFF_FREQ)
        except Exception:
            self.master._close_connection()
            QMessageBox.warning(self.master, "Unrecoverable failure!",
                                "The program encounter and invalid measurement.")
            exit()

        frequency = filtered_data.y
        angular_velocity = frequency * 2 * np.pi
        linear_velocity = angular_velocity * RADIUS

        angular_acceleration = derivative_gradient(DataSet(x=filtered_data.x,
                                                           y=angular_velocity)).y

        force = np.abs(angular_acceleration * (self.run_conf.load / RADIUS))
        force = force + (self.run_conf.weight * 9.8)

        power = force * linear_velocity
        # take middle value to negate side effect of processing appearing on edges
        return power[len(power) // 2]

    def calc_stats(self) -> RunData:
        """Calculate all the stats for the current run."""
        raw_dataset = DataSet(x=self.raw_x, y=self.raw_y)
        # save raw measurements for potential analysis
        save_data(raw_dataset)

        # interpolate points as they are not equally spaced
        filtered_data = butter_lowpass_filter(
            interpolation(raw_dataset),
            cutoff=CUTOFF_FREQ
        )

        # calculate all the statistics, involves heavy physics
        frequency = filtered_data.y
        angular_velocity = frequency * 2 * np.pi
        linear_velocity = angular_velocity * RADIUS
        angular_acceleration = derivative_gradient(DataSet(x=filtered_data.x,
                                                           y=angular_velocity)).y
        force = np.abs(angular_acceleration * (self.run_conf.load / RADIUS))
        force = force + (self.run_conf.weight * 9.8)
        power = force * linear_velocity

        # transform time of new bar to the closest position
        new_bar_pos = [np.abs(filtered_data.x - new_pos).argmin() for new_pos in self.new_bar_time]
        new_bar_pos.append(len(filtered_data.x) - 1)

        # in segments find min to exactly cut segments
        exact_new_segment = [0]
        for i, j in zip(new_bar_pos[:-1], new_bar_pos[1:]):
            # only look at the second half
            middle = i + int((j - i) / 2)
            s_min = filtered_data.y[middle:j].argmin()
            exact_new_segment.append(middle + s_min)

        # remove first START_RUNS and more than COUNTED_RUNS
        exact_new_segment = exact_new_segment[START_RUNS:START_RUNS + COUNTED_RUNS + 1]
        log.info(f"number of segments: {len(exact_new_segment) - 1}, cut x: {filtered_data.x[exact_new_segment]}")

        results = []
        for i, j in zip(exact_new_segment[:-1], exact_new_segment[1:]):
            # calculate all statistics for each repetition
            m = filtered_data.y[i:j].argmax() + i
            results.append(RunData(
                v_con_max=find_second_peak(linear_velocity[i:m]),
                v_ecc_max=find_second_peak(linear_velocity[m:j]),
                v_con_mean=linear_velocity[i:m].mean(),
                v_ecc_mean=linear_velocity[m:j].mean(),
                f_con_max=force[i:m].max(),
                f_ecc_max=force[m:j].max(),
                f_con_mean=force[i:m].mean(),
                f_ecc_mean=force[m:j].mean(),
                p_con_max=power[i:m].max(),
                p_ecc_max=power[m:j].max(),
                p_con_mean=power[i:m].mean(),
                p_ecc_mean=power[m:j].mean(),
            ))

        # the end result statistics are the mean over all repetitions
        end_result = RunData(
            v_con_max=round(np.mean([r.v_con_max for r in results]), 2),
            v_ecc_max=round(np.mean([r.v_ecc_max for r in results]), 2),
            v_con_mean=round(np.mean([r.v_con_mean for r in results]), 2),
            v_ecc_mean=round(np.mean([r.v_ecc_mean for r in results]), 2),
            f_con_max=round(np.mean([r.f_con_max for r in results]), 0),
            f_ecc_max=round(np.mean([r.f_ecc_max for r in results]), 0),
            f_con_mean=round(np.mean([r.f_con_mean for r in results]), 0),
            f_ecc_mean=round(np.mean([r.f_ecc_mean for r in results]), 0),
            p_con_max=round(np.mean([r.p_con_max for r in results]), 0),
            p_ecc_max=round(np.mean([r.p_ecc_max for r in results]), 0),
            p_con_mean=round(np.mean([r.p_con_mean for r in results]), 0),
            p_ecc_mean=round(np.mean([r.p_ecc_mean for r in results]), 0),
        )

        return end_result

    def get_bar_data(self) -> list:
        return self.bar_h

    def report(self):
        if len(self.bar_h) < START_RUNS + 1:
            QMessageBox.warning(self.master, "Invalid measurement!",
                                "Measurement must have at least 1 valid repetition!\n"
                                "Metrics could not be calculated!")
            return
        elif len(self.bar_h) < START_RUNS + COUNTED_RUNS + 1:
            QMessageBox.warning(self.master, "Insufficient measurement!",
                                f"To ensure measurements accuracy {START_RUNS + COUNTED_RUNS + 1} repetitions are advised!\n"
                                "Calculated metrics may be inaccurate!")
        run_data = self.calc_stats()
        if not self.run_saved:
            save_run(run_data, self.run_conf)
            self.run_saved = True
        self.show_report(run_data)

    @staticmethod
    def show_report(run_data: RunData):
        # I am definitely not gonna teach HTML/CSS to anyone in the near future
        report_html = f"""
        <style>
          table, tr, td {{
            border: none;
            border-collapse: collapse;
          }}
          td {{
            padding: 0.6em;
            font-size: 25pt;
            text-align: center;
          }}
          tr.header td {{
            padding: 0.2em 0.1em;
          }}
          td.value_type {{
            text-align: right;
            padding: 0.6em 0.1em;
          }}
          .odd {{
            background-color: silver;
          }}
        </style>
        <table style="width:100%;">
        <tbody>
          <tr class="header"><td></td><td colspan="2">max</td><td colspan="2">mean</td></tr>
          <tr class="header"><td></td><td>con</td><td>ecc</td><td>con</td><td>ecc</td></tr>
          <tr class="odd">
            <td class="value_type">Velocity:</td>
            <td>{run_data.v_con_max:.2f}</td>
            <td>{run_data.v_ecc_max:.2f}</td>
            <td>{run_data.v_con_mean:.2f}</td>
            <td>{run_data.v_ecc_mean:.2f}</td>
          </tr>
          <tr>
            <td class="value_type">Force:</td>
            <td>{run_data.f_con_max:.0f}</td>
            <td>{run_data.f_ecc_max:.0f}</td>
            <td>{run_data.f_con_mean:.0f}</td>
            <td>{run_data.f_ecc_mean:.0f}</td>
          </tr>
          <tr class="odd">
            <td class="value_type">Power:</td>
            <td>{run_data.p_con_max:.0f}</td>
            <td>{run_data.p_ecc_max:.0f}</td>
            <td>{run_data.p_con_mean:.0f}</td>
            <td>{run_data.p_ecc_mean:.0f}</td>
          </tr>
        </tbody>
        </table>
        """
        report_dialog = ReportDialog(report_html)
        report_dialog.exec_()

    def clear(self):
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.new_bar_time = []
        self.descending_freq = False
        self.run_started = False
        self.run_saved = False
        log.info("Data cleared.")


if __name__ == '__main__':
    from PyQt5.QtWidgets import QApplication

    data = RunData(
        v_con_max=1.33, v_ecc_max=1.33, v_con_mean=0.88, v_ecc_mean=1.00,
        f_con_max=2474, f_ecc_max=1915, f_con_mean=1654, f_ecc_mean=1143,
        p_con_max=1876, p_ecc_max=1374, p_con_mean=1292, p_ecc_mean=1030,
    )

    app = QApplication([])
    Data.show_report(run_data=data)
    app.exec_()
