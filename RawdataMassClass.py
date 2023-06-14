from __future__ import annotations
from typing import TYPE_CHECKING
import numpy as np
if TYPE_CHECKING:
    import RawdataSampleClass

import LineClass
import re


class RawdataMass:
    def __init__(self, sample: RawdataSampleClass.RawdataSample, rawdata_line_dictionary, dwelltime, mass, fill_value):
        self.sample: RawdataSampleClass.RawdataSample = sample
        self.mass: str = mass
        self.dwelltime: dict = dwelltime
        self.rawdata_line_dictionary: dict = rawdata_line_dictionary
        self.line_dictionary: dict = {}
        self.true_rawdata_dictionary: dict = {}
        self.maximum_line_length: int = 0
        self.fill_value = fill_value

    def build_line_objects(self):
        for line, line_data in self.rawdata_line_dictionary.items():
            line_instance = LineClass.Line(line_data_array=line_data,
                                           line=line)
            self.line_dictionary[line] = line_instance

    def build_true_rawdata_lines(self, true_line_dictionary, outer_dimensions_dictionary, scan_speed):
        dwelltime_cycle: float = self.sample.get_dwelltime_cycle()
        space_per_datapoint: float = (scan_speed*dwelltime_cycle)
        for true_line, line_info in true_line_dictionary.items():
            if len(line_info['lines included']) == 1:
                line_number = re.findall(r'\d+', line_info["lines included"][0])  # Find all numeric substrings
                integer_value = int(line_number[0])

                number_of_data_points_before = int((line_info[f'{line_info["lines included"][0]}_x_start'] - outer_dimensions_dictionary['x_min'])/space_per_datapoint)
                zeros_array_before = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_before)

                number_of_data_points_inside = int((line_info[f'{line_info["lines included"][0]}_x_end'] -
                                                    line_info[f'{line_info["lines included"][0]}_x_start'])/space_per_datapoint)
                sample_data = self.rawdata_line_dictionary[f'Sample {integer_value}'][0:number_of_data_points_inside]

                number_of_data_points_after = int((outer_dimensions_dictionary['x_max'] - line_info[f'{line_info["lines included"][0]}_x_end'])/space_per_datapoint)
                zeros_array_after = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_after)
                combined_true_line_array = np.concatenate((zeros_array_before, sample_data, zeros_array_after))
                line_length = combined_true_line_array.size
                if line_length > self.maximum_line_length:
                    self.maximum_line_length = line_length
                self.true_rawdata_dictionary[f'Sample {integer_value}'] = combined_true_line_array
                continue
            if len(line_info['lines included']) > 1:
                combined_true_line_array, sample_value = self.line_stitcher(line_info=line_info,
                                                              outer_dimensions_dictionary=outer_dimensions_dictionary,
                                                              space_per_datapoint= space_per_datapoint)
                line_length = combined_true_line_array.size
                if line_length > self.maximum_line_length:
                    self.maximum_line_length = line_length
                self.true_rawdata_dictionary[f'Sample {sample_value}'] = combined_true_line_array
                continue
            if len(line_info['lines included']) < 1:
                self.send_error_message(title='Sample Log Error', message='Sample line without connected logged line found!')

        return self.true_rawdata_dictionary, self.maximum_line_length
    def send_error_message(self, title, message):
        self.sample.send_error_message(title=title, message=message)

    def line_stitcher(self, line_info, outer_dimensions_dictionary,space_per_datapoint):
        amount_of_lines = len(line_info['lines included'])
        for k, i in enumerate(line_info['lines included']):
            line_number = re.findall(r'\d+', line_info["lines included"][k])  # Find all numeric substrings
            integer_value = int(line_number[0])
            if k == 0:
                sample_value = integer_value
                number_of_data_points_before = int((line_info[f'{line_info["lines included"][k]}_x_start'] -
                                                    outer_dimensions_dictionary['x_min']) / space_per_datapoint)
                combined_array = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_before)
                number_of_data_points_inside = int((line_info[f'{line_info["lines included"][k]}_x_end'] -
                                                    line_info[
                                                        f'{line_info["lines included"][k]}_x_start']) / space_per_datapoint)
                sample_data = self.rawdata_line_dictionary[f'Sample {integer_value}'][0:number_of_data_points_inside]
                number_of_data_points_after = int((line_info[f'{line_info["lines included"][k+1]}_x_start'] -
                                                   line_info[f'{line_info["lines included"][k]}_x_end']) / space_per_datapoint)
                zeros_array_after = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_after)
                combined_array = np.concatenate((combined_array, sample_data, zeros_array_after))
            if 0 < k < amount_of_lines-1:
                number_of_data_points_inside = int((line_info[f'{line_info["lines included"][k]}_x_end'] -
                                                    line_info[
                                                        f'{line_info["lines included"][k]}_x_start']) / space_per_datapoint)
                sample_data = self.rawdata_line_dictionary[f'Sample {integer_value}'][0:number_of_data_points_inside]

                number_of_data_points_after = int((line_info[f'{line_info["lines included"][k + 1]}_x_start'] -
                                                   line_info[
                                                       f'{line_info["lines included"][k]}_x_end']) / space_per_datapoint)
                zeros_array_after = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_after)
                combined_array = np.concatenate((combined_array, sample_data, zeros_array_after))
            if k == amount_of_lines-1:
                number_of_data_points_inside = int((line_info[f'{line_info["lines included"][k]}_x_end'] -
                                                    line_info[
                                                        f'{line_info["lines included"][k]}_x_start']) / space_per_datapoint)
                sample_data = self.rawdata_line_dictionary[f'Sample {integer_value}'][0:number_of_data_points_inside]
                number_of_data_points_after = int((outer_dimensions_dictionary['x_max'] - line_info[
                    f'{line_info["lines included"][k]}_x_end']) / space_per_datapoint)
                zeros_array_after = np.full(fill_value=str(self.fill_value), shape=number_of_data_points_after)
                combined_array = np.concatenate((combined_array, sample_data, zeros_array_after))
        return combined_array, sample_value
