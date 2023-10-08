from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import LaserlogClass

import pandas as pd
from math import isclose


class Sampleinlog:
    def __init__(self, log: LaserlogClass.Laserlog, sample, logfile_slice: pd.DataFrame):
        self.log = log
        self.logfile_slice = logfile_slice
        self.sample_number = sample

        self.x_min: float = 0.0
        self.x_max: float = 0.0
        self.y_min: float = 0.0
        self.y_max: float = 0.0

        self.scan_speed = 0

    def find_outer_dimensions_of_sample(self):
        self.x_min = self.logfile_slice['X(um)'].min()
        self.x_max = self.logfile_slice['X(um)'].max()
        self.y_min = self.logfile_slice['Y(um)'].min()
        self.y_max = self.logfile_slice['Y(um)'].max()

    def find_scan_speed_of_sample(self):
        self.scan_speed = self.logfile_slice['Scan Speed(Î¼m/sec)'].mean()
        if not isclose(self.scan_speed, int(self.scan_speed)):
            self.send_error_message(title='Laserlog Error', message=f'Inconsistent scan speed in {self.sample_number}!')

    def get_series_of_duplicate_lines(self):
        duplicated_indices = self.logfile_slice.groupby('Y(um)').apply(lambda x: [idx for idx in x.index if idx % 2 == 0])
        duplicated_indices = duplicated_indices[duplicated_indices.apply(lambda x: len(x) > 1)]
        return duplicated_indices

    def build_true_line_information_dictionary(self, line_pattern_sheet):
        # Find outer dimensions of sample by looking for the maximum and minimum values of x and y
        self.find_outer_dimensions_of_sample()
        # Get the scan speed of the sample by looking at the corresponding column in the logfile
        self.find_scan_speed_of_sample()
        # Discern between the rectangular data and the pattern duration sheet calculation. If the pattern duration sheet
        # is asked for, no search for dublicated y values is necessary, as all lines should be treated separately.
        # In the case of the rectangular data calculation a seach for lines at the same y value is cnducted.
        # These line are stored in a series at their respective y values
        if line_pattern_sheet is False:
            duplicated_indices_series = self.get_series_of_duplicate_lines()
        else:
            duplicated_indices_series = pd.Series([])
        # A dictionary for the final data about the y_value, x start and x end and the line number is started
        true_line_information_dictionary = {}
        # defining, that the first line of the sample is line number 1
        line = 1
        # Iterating over all the rows in the logfile that have been designated to this sample.
        # Each ablation line has two rows in the logfile
        for idx, row in self.logfile_slice.iloc[::2].iterrows():
            # The line counter is the index of each row in the logfile.
            # 2 is added to account for the fact that the lines of the sample should start at 1 and not 0
            line_counter = idx + 2
            # The three possible cases are now checked

            # 1. Case: The current row has no other row at the same y value
            if row['Y(um)'] not in duplicated_indices_series.index:
                # First, a new line is added to the dictionary as the current line is a new true line since
                # it is the only one at this y value
                true_line_information_dictionary[f'line_{str(line)}'] = {}
                # The current line is the only one that should be included in this true line,
                # so only this line is added to the included lines
                true_line_information_dictionary[f'line_{str(line)}'][
                    'lines included'] = [f'line_{str(int(line_counter/2))}']
                # The start value of x of the line is added
                true_line_information_dictionary[f'line_{str(line)}'][
                    f'line_{str(int(line_counter / 2))}_x_start'] = row['X(um)']
                # The end value of x of the line is added by looking at the x value of the next row in the logfile
                true_line_information_dictionary[f'line_{str(line)}'][
                    f'line_{str(int(line))}_x_end'] = self.logfile_slice.loc[idx + 1, 'X(um)']
                # The y value of the line is added
                true_line_information_dictionary[f'line_{str(line)}']['y_value'] = row['Y(um)']

            # 2. Case: The current row has other rows at the same y value,
            # but this line is not the first one of these, that has been processed
            elif row['Y(um)'] in duplicated_indices_series.index and idx != duplicated_indices_series[row['Y(um)']][0]:
                continue
            # 3. Case: The current row has other rows at the same y value
            # and this is the first line of these that is processed
            elif row['Y(um)'] in duplicated_indices_series.index and idx == duplicated_indices_series[row['Y(um)']][0]:
                # First, a new line is added to the dictionary to
                # act as the true line ofr the later rectangular data
                true_line_information_dictionary[f'line_{str(line)}'] = {}
                # All line at this y value, that are in the dublicated series are stored for this true line
                true_line_information_dictionary[f'line_{str(line)}'][
                    f'lines included'] = [f'line_{str(int((i+2)/2))}'for i in duplicated_indices_series[row['Y(um)']] if i % 2 == 0]
                # The y value of the line is added
                true_line_information_dictionary[f'line_{str(line)}']['y_value'] = row['Y(um)']
                # Now all the lines at this y value are iterated through to get their start and end values
                for index in duplicated_indices_series[row['Y(um)']]:
                    # The start value of x of the line is added by looking at the x value of the row that was saved
                    # in the dublicated series
                    true_line_information_dictionary[f'line_{str(line)}'][
                        f'line_{str(int((index+2)/2))}_x_start'] = self.logfile_slice.loc[index, 'X(um)']
                    # The end value of x of the line is added by looking at the x value of the row that was saved
                    # in the dublicated series
                    true_line_information_dictionary[f'line_{str(line)}'][
                        f'line_{str(int((index+2)/2))}_x_end'] = self.logfile_slice.loc[index+1, 'X(um)']
            else:
                return False
            line += 1

        return true_line_information_dictionary

    def get_true_line_information_dictionary(self, line_pattern_sheet=False):
        true_line_information_dictionary = self.build_true_line_information_dictionary(line_pattern_sheet)
        return true_line_information_dictionary

    def get_raw_line_information_dictionary(self):
        raw_line_information_dictionary = self.build_raw_line_information_dictionary()
        return raw_line_information_dictionary

    def get_outer_dimensions_dictionary(self):
        outer_dimensions_dictionary = {}
        outer_dimensions_dictionary['x_min'] = self.x_min
        outer_dimensions_dictionary['x_max'] = self.x_max
        outer_dimensions_dictionary['y_min'] = self.y_min
        outer_dimensions_dictionary['y_max'] = self.y_max
        return outer_dimensions_dictionary

    def get_scan_speed(self):
        self.find_scan_speed_of_sample()
        return self.scan_speed

    def send_error_message(self, title, message):
        self.log.send_error_message(title=title, message=message)

    def get_amount_of_lines(self):
        return len(self.logfile_slice. index)/2

    def build_raw_line_information_dictionary(self):
        true_line_information_dictionary = {}
        for idx, row in self.logfile_slice.iterrows():
            line_counter = idx + 2
            if line_counter % 2 == 0:
                true_line_information_dictionary[f'line_{str(int(line_counter / 2))}'][
                    f'line_{str(int(line_counter / 2))}_x_start'] = row['X(um)']
                legacy_counter = line_counter
            else:
                true_line_information_dictionary[f'line_{str(int(legacy_counter / 2))}'][
                    f'line_{str(int(legacy_counter / 2))}_x_end'] = row['X(um)']
        return true_line_information_dictionary
