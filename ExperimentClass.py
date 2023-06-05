import pandas as pd
import numpy as np
import os

# Static Functions
import LaserlogClass
import RawdataSampleClass


def get_dwelltimes_from_rawdata(masses: list, dataframe: pd.DataFrame):
    dwelltime_dictionary = {}
    average_of_last_mass = None
    for k, i in masses:
        mask = dataframe['Unnamed: 2'].str.contains(i, case=False) & dataframe['Unnamed: 3'].str.contains('Time', case=False)
        # Apply the mask to the DataFrame to filter the rows
        filtered_df = dataframe[mask]
        # Get the first row from the filtered DataFrame
        first_row = filtered_df.head(1)
        first_row = first_row.iloc[:, 4:]
        average_value = first_row.mean().values[0]
        if k == 0:
            second_row = filtered_df.iloc[1]
            second_row = second_row.iloc[4:]
            numeric_values = pd.to_numeric(second_row, errors='coerce')
            filtered_second_row = numeric_values.dropna()

            # Calculate the average value of the remaining numeric values in the second row
            average_value_second_row = filtered_second_row.mean()
            dwelltime = average_value
            dwelltime_cycle = average_value_second_row - average_value
            dwelltime_dictionary['Cycle'] = dwelltime_cycle
        else:
            dwelltime = average_value - average_of_last_mass
        dwelltime_dictionary[i] = dwelltime
        average_of_last_mass = average_value
    return dwelltime_dictionary


class Experiment:
    def __init__(self, gui, raw_laser_logfile_dataframe: pd.DataFrame, sample_rawdata_dictionary: dict, data_type: str):
        self.gui = gui
        self.raw_laser_logfile_dataframe: pd.DataFrame = raw_laser_logfile_dataframe
        self.sample_rawdata_dictionary: dict = sample_rawdata_dictionary
        self.data_type = data_type

        self.laserlog_object: LaserlogClass.Laserlog = None
        self.RawdataSample_objects_dictionary: dict = {}

    def build_Laserlog_object(self):

        # Keywords for each column
        keywords_for_filtering = {
            'Type': ['Lasso'],
            'Run Queue Order': [-1],
            'X(um)': [np.nan],
            'Y(um)': [np.nan]
        }
        # Filter rows
        filtered_df = self.raw_laser_logfile_dataframe
        for col, key_list in keywords_for_filtering.items():
            filtered_df = filtered_df[~filtered_df[col].isin(key_list)]
        filtered_df = filtered_df.reset_index(drop=True)
        self.laserlog_object = LaserlogClass.Laserlog(experiment=self, clean_laserlog_dataframe=filtered_df)

    def build_rawdatasample_objects(self):
        sample_counter = 1
        if self.data_type == 'iCap TQ (Daisy)':
            rawdata_extracted_masses_dictionary = {}
            for sample_name, sample_rawdata_dataframe in self.sample_rawdata_dictionary.items():
                mass_options: np.ndarray = sample_rawdata_dataframe['Unnamed: 2'].unique()
                mass_options_clean: np.ndarray = np.delete(mass_options, [0])
                mass_options_list: list = list(mass_options_clean)
                # Determine dwell times for each element and the total cycle time for each sample
                dwelltime_dictionary = get_dwelltimes_from_rawdata(masses=mass_options_list,
                                                                   dataframe=sample_rawdata_dataframe)
                extracted_sample_column_dictionary = {}
                for k, i in enumerate(mass_options_list):
                    # Iterate over the columns
                    for col in sample_rawdata_dataframe.columns:
                        if col.startswith('Sample'):
                            sample_col = sample_rawdata_dataframe[col]
                            identifier_col_2 = sample_rawdata_dataframe['Unnamed: 2']
                            identifier_col_3 = sample_rawdata_dataframe['Unnamed: 3']
                            # Find the indices where both identifiers match
                            indices = np.where((identifier_col_2 == i) & (identifier_col_3 == 'Y'))[0]
                            # Extract the corresponding values from the sample column
                            extracted_values = sample_col.iloc[indices]
                            # Filter out non-numeric values (strings, NaNs, etc.)
                            extracted_values = extracted_values.loc[
                                extracted_values.apply(lambda x: pd.to_numeric(x, errors='coerce')).notnull()]
                            # Convert the filtered values to a NumPy array
                            extracted_array = extracted_values.astype(float).to_numpy()
                            # Add the extracted array to the dictionary
                            extracted_sample_column_dictionary[col] = extracted_array
                    rawdata_extracted_masses_dictionary[i] = extracted_sample_column_dictionary
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 dwelltime_dictionary=dwelltime_dictionary,
                                                                 sample_number=sample_counter)
                sample_counter +=1
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

        if self.data_type == 'Agilent 7900':
            rawdata_extracted_masses_dictionary = {}
            for sample_name, sample_rawdata_dictionary in self.sample_rawdata_dictionary.items():
                dwelltime_dictionary = {}
                sample_dataframe = sample_rawdata_dictionary['Line_1']
                header_list = list(sample_dataframe.columns())
                mass_options_list = header_list[1:]
                dwelltime_array = sample_dataframe[[sample_dataframe.columns[0]]].to_numpy()
                if dwelltime_array.size > 1:
                    dwelltime_dictionary['Cycle'] = dwelltime_array[-1]-dwelltime_array[-2]
                else:
                    dwelltime_dictionary['Cycle'] = dwelltime_array[0]
                for mass in mass_options_list:
                    rawdata_extracted_masses_dictionary[mass] = {}
                    dwelltime_dictionary[mass] = dwelltime_dictionary['Cycle']/len(mass_options_list)
                for line, raw_dataframe in sample_rawdata_dataframe.items():
                    for mass in mass_options_list:
                        rawdata_extracted_masses_dictionary[mass][f'Line_{line}'] = raw_dataframe[mass].to_numpy()
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 dwelltime_dictionary=dwelltime_dictionary,
                                                                 sample_number=sample_counter)
                sample_counter += 1
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample




    def pass_sample_logfile_information(self, sample_number: str):
        return self.laserlog_object.get_log_information_of_rawdata_sample(sample_number)

    def build_rectangular_data(self):
        self.build_Laserlog_object()
        self.laserlog_object.build_sampleinlog_objects()
        self.build_rawdatasample_objects()

    def send_error_message(self, title, message):
        self.gui.popup_error_message(title, message)