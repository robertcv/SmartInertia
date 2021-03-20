

class Data:
    """Holding incoming data and processing utilities."""
    def __init__(self):
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.current_bar = 0
        self.run_started = False
        self.run_conf = None

    def add_new(self, point: tuple):
        x, y = point
        self.raw_x.append(x)
        self.raw_y.append(y)

    def get_bar_data(self):
        self.bar_h = [10, 25, 100, 120, 130, 125, 120, 130, 50, 20]
        return self.bar_h

    def save_report(self):
        pass

    def show_report(self) -> str:
        pass

    def clear(self):
        self.raw_x = []
        self.raw_y = []

        self.bar_h = []
        self.current_bar = 0
        self.run_started = False
        self.run_conf = None
