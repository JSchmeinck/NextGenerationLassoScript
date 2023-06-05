import LineClass


class RawdataMass:
    def __init__(self, rawdata_line_dictionary, dwelltime, mass):
        self.mass = mass
        self.dwelltime: dict = dwelltime
        self.rawdata_line_dictionary: dict = rawdata_line_dictionary
        self.line_dictionary = None

    def build_line_objects(self):
        for line, line_data in self.rawdata_line_dictionary.items():
            line_instance = LineClass.Line(line_data_array=line_data,
                                           line=line)
            self.line_dictionary[line] = line_instance

    def build_true_rawdata_lines(self, true_line_dictionary, outer_dimensions_dictionary):
        pass


