import pandas as pd


class Sampleinlog:
    def __init__(self, logfile_slice: pd.DataFrame):
        self.logfile_slice = logfile_slice

        self.line_information_dictionary: dict = {}
        self.x_min: float = 0.0
        self.x_max: float = 0.0
        self.y_min: float = 0.0
        self.y_max: float = 0.0

    def find_outer_dimensions_of_sample(self):
        pass

    def build_line_information_dictionary(self):
        pass

    def supply_line_information_dictionary(self):
        return self.line_information_dictionary
