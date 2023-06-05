import pandas as pd


class Sampleinlog:
    def __init__(self, sample, logfile_slice: pd.DataFrame):
        self.logfile_slice = logfile_slice
        self.sample_number = sample

        self.x_min: float = 0.0
        self.x_max: float = 0.0
        self.y_min: float = 0.0
        self.y_max: float = 0.0

    def find_outer_dimensions_of_sample(self):
        self.x_min = self.logfile_slice['X(um)'].min()
        self.x_max = self.logfile_slice['X(um)'].max()
        self.y_min = self.logfile_slice['Y(um)'].min()
        self.y_max = self.logfile_slice['Y(um)'].max()

    def get_series_of_duplicate_lines(self):
        duplicated_indices = self.logfile_slice.groupby('Y(um)').apply(lambda x: x.index.tolist())
        return duplicated_indices

    def build_true_line_information_dictionary(self):
        self.find_outer_dimensions_of_sample()
        duplicated_indices_series = self.get_series_of_duplicate_lines()
        true_line_information_dictionary = {}
        for idx, row in self.logfile_slice.iterrows():
            line_counter = idx + 2
            if line_counter % 2 == 0:
                true_line_information_dictionary[f'line_{str(line_counter/2)}'] = {}
                if row['Y(um)'] not in duplicated_indices_series.index():
                    true_line_information_dictionary[f'line_{str(line_counter/2)}']['lines included'] = list(f'line_{str(line_counter/2)}')
                    true_line_information_dictionary[f'line_{str(line_counter / 2)}'][f'line_{str(line_counter / 2)}_x_start'] = row['X(um)']
                    true_line_information_dictionary[f'line_{str(line_counter / 2)}'][f'y_value'] = row['Y(um)']
                if row['Y(um)'] in duplicated_indices_series.index() and idx != duplicated_indices_series[row['Y(um)']][0]:
                    continue
                else:
                    true_line_information_dictionary[f'line_{str(line_counter / 2)}'][
                        f'lines included'] = [f'line_{str((i+2)/2)}'for i in duplicated_indices_series[row['Y(um)']] if i % 2 == 0]
                    true_line_information_dictionary[f'line_{str(line_counter / 2)}']['y_value'] = row['Y(um)']
                    for index in duplicated_indices_series[row['Y(um)']]:
                        if index % 2 == 0:
                            true_line_information_dictionary[f'line_{str(line_counter / 2)}'][
                                f'line_{str(index+2 / 2)}_x_start'] = self.logfile_slice.loc[index, 'X(um)']
                        else:
                            true_line_information_dictionary[f'line_{str(line_counter / 2)}'][
                                f'line_{str(index+2 / 2)}_x_end'] = self.logfile_slice.loc[index, 'X(um)']
            else:
                if row['Y(um)'] not in duplicated_indices_series.index():
                    true_line_information_dictionary[f'line_{str(line_counter / 2)}'][f'line_{str(line_counter / 2)}_length'] = row['X(um)']
                else:
                    continue

        return true_line_information_dictionary

    def get_true_line_information_dictionary(self):
        true_line_information_dictionary = self.build_true_line_information_dictionary()
        return true_line_information_dictionary

    def get_outer_dimensions_of_sample(self):
        outer_dimensions_dictionary = {}
        outer_dimensions_dictionary['x_min'] = self.x_min
        outer_dimensions_dictionary['x_max'] = self.x_max
        outer_dimensions_dictionary['y_min'] = self.y_min
        outer_dimensions_dictionary['y_max'] = self.y_max
        return outer_dimensions_dictionary
