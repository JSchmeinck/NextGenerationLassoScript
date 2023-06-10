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

    def build_true_line_information_dictionary(self):
        self.find_outer_dimensions_of_sample()
        self.find_scan_speed_of_sample()
        duplicated_indices_series = self.get_series_of_duplicate_lines()
        true_line_information_dictionary = {}
        line = 1
        for idx, row in self.logfile_slice.iterrows():
            line_counter = idx + 2
            if line_counter % 2 == 0:
                if row['Y(um)'] not in duplicated_indices_series.index:
                    true_line_information_dictionary[f'line_{str(line)}'] = {}
                    true_line_information_dictionary[f'line_{str(line)}']['lines included'] = [f'line_{str(int(line_counter/2))}']
                    true_line_information_dictionary[f'line_{str(line)}'][f'line_{str(int(line_counter / 2))}_x_start'] = row['X(um)']
                    true_line_information_dictionary[f'line_{str(line)}']['y_value'] = row['Y(um)']
                    legacy_counter = line_counter
                if row['Y(um)'] in duplicated_indices_series.index and idx != duplicated_indices_series[row['Y(um)']][0]:
                    continue
                if row['Y(um)'] in duplicated_indices_series.index and idx == duplicated_indices_series[row['Y(um)']][0]:
                    true_line_information_dictionary[f'line_{str(line)}'] = {}
                    true_line_information_dictionary[f'line_{str(line)}'][
                        f'lines included'] = [f'line_{str(int((i+2)/2))}'for i in duplicated_indices_series[row['Y(um)']] if i % 2 == 0]
                    true_line_information_dictionary[f'line_{str(line)}']['y_value'] = row['Y(um)']
                    true_line = int((duplicated_indices_series[row['Y(um)']][0]+2)/2)
                    for index in duplicated_indices_series[row['Y(um)']]:
                        true_line_information_dictionary[f'line_{str(line)}'][
                            f'line_{str(int((index+2)/2))}_x_start'] = self.logfile_slice.loc[index, 'X(um)']
                        true_line_information_dictionary[f'line_{str(line)}'][
                            f'line_{str(int((index+2)/2))}_x_end'] = self.logfile_slice.loc[index+1, 'X(um)']
                    line += 1
            else:
                if row['Y(um)'] not in duplicated_indices_series.index:
                    true_line_information_dictionary[f'line_{str(line)}'][f'line_{str(int(legacy_counter / 2))}_x_end'] = row['X(um)']
                    line += 1
                else:
                    continue

        return true_line_information_dictionary

    def get_true_line_information_dictionary(self):
        true_line_information_dictionary = self.build_true_line_information_dictionary()
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

