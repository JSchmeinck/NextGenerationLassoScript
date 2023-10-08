import numpy as np
from typing import Optional
import RawdataMassClass
import SampleinlogClass


class RawdataSample:
    def __init__(self, experiment, rawdata_dictionary, dwelltime_dictionary, name, sample_number, fill_value, column_names):
        self.experiment = experiment
        self.name = name
        self.sample_number = sample_number
        self.dwelltime_dictionary: dict = dwelltime_dictionary
        self.rawdata_dictionary: dict = rawdata_dictionary
        self.rectangular_rawdata_dictionary: dict = {}
        self.RawdataMass_objects_dictionary: dict = {}
        self.max_length_dictionary: dict = {}
        self.sample_in_log: SampleinlogClass.Sampleinlog
        self.amount_of_lines = 0
        self.fill_value = fill_value
        self.sample_in_log: Optional[SampleinlogClass.Sampleinlog] = None
        self.list_of_column_names: list = column_names

    def build_rawdatamass_objects(self):
        k = 0
        for mass, rawdata_line_dictionary in self.rawdata_dictionary.items():
            rawdatamass = RawdataMassClass.RawdataMass(rawdata_line_dictionary=rawdata_line_dictionary,
                                                       mass=mass,
                                                       dwelltime=self.dwelltime_dictionary[mass],
                                                       sample=self,
                                                       fill_value=self.fill_value,
                                                       column_names=self.list_of_column_names)
            self.RawdataMass_objects_dictionary[mass] = rawdatamass
            if k == 0:
                self.amount_of_lines = len(rawdata_line_dictionary)
            k += 1

    def build_true_rawdata_lines(self):
        true_line_dictionary = self.sample_in_log.get_true_line_information_dictionary()
        outer_dimensions_dictionary = self.sample_in_log.get_outer_dimensions_dictionary()
        scan_speed = self.sample_in_log.get_scan_speed()
        for mass, mass_object in self.RawdataMass_objects_dictionary.items():
            dictionary, max_length = mass_object.build_true_rawdata_lines(true_line_dictionary,
                                                                          outer_dimensions_dictionary,
                                                                          scan_speed)
            self.rectangular_rawdata_dictionary[mass] = dictionary
            self.max_length_dictionary[mass] = max_length

    def get_dwelltime_cycle(self):
        return self.dwelltime_dictionary['Cycle']

    def set_sample_in_log(self, sample_in_log):
        self.sample_in_log = sample_in_log

    def get_amount_of_lines(self):
        return self.amount_of_lines

    def send_error_message(self, title, message):
        self.experiment.send_error_message(title=title, message=message)

    def get_rectangular_rawdata_dictionary(self):
        return self.rectangular_rawdata_dictionary

    def get_max_length(self, mass):
        return self.max_length_dictionary[mass]

    def build_dwelltime_array(self, mass):
        max_length = self.max_length_dictionary[mass]
        cycle_time = self.dwelltime_dictionary['Cycle']
        dwelltime = self.dwelltime_dictionary[mass]
        for i in range(max_length):
            if i == 0:
                array = np.full(fill_value=dwelltime, shape=1)
            else:
                timepoint = dwelltime + cycle_time * i
                timepoint = np.full(fill_value=timepoint, shape=1)
                array = np.concatenate((array, timepoint))

        return array
