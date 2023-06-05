import pandas as pd
import numpy as pd

import RawdataMassClass


class RawdataSample:
    def __init__(self, rawdata_dictionary, dwelltime_dictionary, name):
        self.name = name
        self.dwelltime_dictionary: dict = dwelltime_dictionary
        self.rawdata_dictionary: dict = rawdata_dictionary
        self.RawdataMass_objects_dictionary = None

    def build_rawdatamass_objects(self):
        for mass, rawdata_line_dictionary in self.rawdata_dictionary:
            rawdatamass = RawdataMassClass.RawdataMass(rawdata_line_dictionary=rawdata_line_dictionary,
                                                       mass=mass,
                                                       dwelltime=self.dwelltime_dictionary[mass])
            self.RawdataMass_objects_dictionary[mass] = rawdatamass