import pandas as pd
import numpy as pd

import RawdataMassClass


class RawdataSample:
    def __init__(self, experiment, rawdata_dictionary, dwelltime_dictionary, name, sample_number):
        self.experiment = experiment
        self.name = name
        self.sample_number = sample_number
        self.dwelltime_dictionary: dict = dwelltime_dictionary
        self.rawdata_dictionary: dict = rawdata_dictionary
        self.RawdataMass_objects_dictionary = None

    def build_rawdatamass_objects(self):
        for mass, rawdata_line_dictionary in self.rawdata_dictionary:
            rawdatamass = RawdataMassClass.RawdataMass(rawdata_line_dictionary=rawdata_line_dictionary,
                                                       mass=mass,
                                                       dwelltime=self.dwelltime_dictionary[mass])
            self.RawdataMass_objects_dictionary[mass] = rawdatamass

    def build_true_rawdata_lines(self):
        true_line_dictionary, outer_dimensions_dictionary = self.experiment.pass_sample_logfile_information(self.sample_number)
        for mass_object in self.RawdataMass_objects_dictionary:
            mass_object.build_true_rawdata_lines(true_line_dictionary, outer_dimensions_dictionary)