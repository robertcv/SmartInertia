import logging

from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QGridLayout, QLabel, QLineEdit, QPushButton,
                             QVBoxLayout)

from smartinertia.connection import get_ports

LOADS = ["0.025", "0.05", "0.075", "0.1",
         "0.125", "0.15", "0.175", "0.2",
         "0.225", "0.25"]

log = logging.getLogger(__name__)


class RunDialog(QDialog):
    """Configure run state."""
    def __init__(self, master):
        super().__init__()
        self.setWindowTitle("Run")
        self.m_settings = master.settings  # type: QSettings
        self.data = None

        self.name_label = QLineEdit()
        self.name_label.setText(self.m_settings.value('run/name', type=str))

        self.weight_label = QLineEdit()
        self.weight_label.setValidator(QDoubleValidator(0., 500., 1))
        self.weight_label.setText(self.m_settings.value('run/weight', type=str))

        self.load_combo_box = QComboBox()
        self.load_combo_box.addItems(LOADS)
        self.load_combo_box.setCurrentText(self.m_settings.value('run/load', type=str))

        self.pulley_checkbox = QCheckBox()
        self.pulley_checkbox.setChecked(self.m_settings.value('run/pulley', type=bool))

        grid = QGridLayout()
        grid.addWidget(QLabel("Name: "), 0, 0)
        grid.addWidget(self.name_label, 0, 1)

        grid.addWidget(QLabel("Weight: "), 1, 0)
        grid.addWidget(self.weight_label, 1, 1)

        grid.addWidget(QLabel("Load: "), 2, 0)
        grid.addWidget(self.load_combo_box, 2, 1)

        grid.addWidget(QLabel("Uses pulley: "), 3, 0)
        grid.addWidget(self.pulley_checkbox, 3, 1)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok |
                                      QDialogButtonBox.Cancel)

        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.close)

        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
        log.info("Opened run dialog.")

    def accept(self):
        log.info("run dialog accepted.")
        self.data = {
            "name": self.name_label.text(),
            "weight": self.weight_label.text(),
            "load": self.load_combo_box.currentText(),
            "pulley": self.pulley_checkbox.isChecked(),
        }
        self.m_settings.setValue('run/name', self.data["name"])
        self.m_settings.setValue('run/weight', self.data["weight"])
        self.m_settings.setValue('run/load', self.data["load"])
        self.m_settings.setValue('run/pulley', self.data["pulley"])
        self.m_settings.sync()
        self.close()


class ConnectionDialog(QDialog):
    """Configure connection to flywheel."""
    def __init__(self, master):
        super().__init__()
        self.setWindowTitle("Connection")
        self.m_settings = master.settings  # type: QSettings
        self.data = None

        current_ports = get_ports()
        self.port_comboBox = QComboBox()
        self.port_comboBox.addItems(current_ports)

        saved_port = self.m_settings.value('connection/port', type=str)
        if saved_port in current_ports:
            self.port_comboBox.setCurrentText(saved_port)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh)

        grid = QGridLayout()
        grid.addWidget(QLabel("Port: "), 0, 0)
        grid.addWidget(self.port_comboBox, 0, 1)
        grid.addWidget(self.refresh_button, 0, 2)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)

        main_layout = QVBoxLayout()
        main_layout.addLayout(grid)
        main_layout.addWidget(button_box)
        self.setLayout(main_layout)
        log.info("Opened connection dialog.")

    def refresh(self):
        log.info("Connection dialog refresh ports.")
        self.port_comboBox.clear()
        self.port_comboBox.addItems(get_ports())

    def accept(self):
        log.info("Connection dialog accepted.")
        self.data = {
            "port": self.port_comboBox.currentText(),
        }
        log.info(f"Port {self.data['port']} was selected.")
        self.m_settings.setValue('connection/port', self.data["port"])
        self.m_settings.sync()
        self.close()


class ReportDialog(QDialog):
    """Display the report of the exercises."""
    def __init__(self, report):
        super().__init__()
        self.setWindowTitle("Report")
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel(report))
        self.setLayout(main_layout)
        log.info("Opened report dialog.")
