import os
from typing import Optional
import pandas as pd
import numpy as np
import re
from tkinter import messagebox
import LaserlogClass
import RawdataSampleClass


def popup_error_message(title, message):
    messagebox.showerror(title=title, message=message)


def popup_info_message(title, message):
    messagebox.showinfo(title=title, message=message)


def popup_yesnocancel_message(title, message):
    messagebox.askyesnocancel(title=title, message=message)


def popup_yesno_message(title, message):
    popup_yes_no = messagebox.askyesno(title=title, message=message)
    return popup_yes_no


def get_dwell_times_from_rawdata(masses: list, dataframe: pd.DataFrame):
    """
    Computes the average dwell time and a total dwell time cycle from a dataframe for the masses supplied
    :param masses: a list of strings that match the mass column in the dataframe
    :param dataframe: a dataframe that contains dwell time data and a column that shows the masses contained in the
    mass list
    :return: A dictionary that contains the dwell times for the supplied masses as well as a total Cycle time. key: mass
    value: dwell time.
    """
    dwell_time_dictionary = {}
    average_of_last_mass = None
    for k, i in enumerate(masses):
        mask = dataframe['Unnamed: 2'].str.contains(i, case=False) & dataframe['Unnamed: 3'].str.contains('Time',
                                                                                                          case=False)
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
            dwell_time_dictionary['Cycle'] = dwelltime_cycle
        else:
            dwelltime = average_value - average_of_last_mass
        dwell_time_dictionary[i] = dwelltime
        average_of_last_mass = average_value
    return dwell_time_dictionary


class Experiment:
    def __init__(self, gui, raw_laser_logfile_dataframe: pd.DataFrame, sample_rawdata_dictionary: dict, data_type: str,
                 logfile_filepath: str, fill_value):
        self.gui = gui
        self.raw_laser_logfile_dataframe: pd.DataFrame = raw_laser_logfile_dataframe
        self.sample_rawdata_dictionary: dict = sample_rawdata_dictionary
        self.data_type = data_type

        self.laserlog_object: Optional[LaserlogClass.Laserlog] = None
        self.RawdataSample_objects_dictionary: dict = {}
        self.logfile_filepath: str = logfile_filepath
        self.fill_value = fill_value

    def build_laser_log_object(self):

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
        name = os.path.basename(self.logfile_filepath).removesuffix('.csv')
        self.laserlog_object = LaserlogClass.Laserlog(experiment=self,
                                                      clean_laserlog_dataframe=filtered_df,
                                                      name=name)

    def build_rawdatasample_objects(self):
        sample_counter = 1
        if self.data_type == 'iCap TQ (Daisy)':
            for sample_name, sample_rawdata_dataframe in self.sample_rawdata_dictionary.items():
                rawdata_extracted_masses_dictionary = {}
                mass_options: np.ndarray = sample_rawdata_dataframe['Unnamed: 2'].unique()
                mass_options_clean: np.ndarray = np.delete(mass_options, [0])
                mass_options_list: list = list(mass_options_clean)
                # Determine dwell times for each element and the total cycle time for each sample
                dwelltime_dictionary = get_dwell_times_from_rawdata(masses=mass_options_list,
                                                                    dataframe=sample_rawdata_dataframe)

                for k, i in enumerate(mass_options_list):
                    extracted_sample_column_dictionary = {}
                    # Iterate over the columns
                    for col in sample_rawdata_dataframe.columns:
                        if col.startswith('Sample'):
                            sample_col = sample_rawdata_dataframe[col]
                            identifier_col_2 = sample_rawdata_dataframe['Unnamed: 2']
                            identifier_col_3 = sample_rawdata_dataframe['Unnamed: 3']
                            # Find the indices where both identifiers match
                            # indices = np.where((identifier_col_2 == i) & (identifier_col_3 == 'Y'))[0]
                            list1 = np.where((identifier_col_2 == i))[0]
                            list2 = np.where((identifier_col_3 == 'Y'))[0]
                            indices = np.intersect1d(list1, list2)
                            # Extract the corresponding values from the sample column
                            extracted_values = sample_col.iloc[indices]
                            # Filter out non-numeric values (strings, NaNs, etc.)
                            extracted_values = extracted_values.loc[
                                extracted_values.apply(lambda x: pd.to_numeric(x, errors='coerce')).notnull()]
                            # Convert the filtered values to a NumPy array
                            extracted_array = extracted_values.astype(float).to_numpy()
                            # Add the extracted array to the dictionary

                            extracted_sample_column_dictionary[col] = extracted_array
                            extracted_array = 0
                    rawdata_extracted_masses_dictionary[i] = extracted_sample_column_dictionary
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 dwelltime_dictionary=dwelltime_dictionary,
                                                                 sample_number=f'Sample_{sample_counter}',
                                                                 fill_value=self.fill_value)
                sample_counter += 1
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
                    dwelltime_dictionary['Cycle'] = dwelltime_array[-1] - dwelltime_array[-2]
                else:
                    dwelltime_dictionary['Cycle'] = dwelltime_array[0]
                for mass in mass_options_list:
                    rawdata_extracted_masses_dictionary[mass] = {}
                    dwelltime_dictionary[mass] = dwelltime_dictionary['Cycle'] / len(mass_options_list)
                for line, raw_dataframe in sample_rawdata_dataframe.items():
                    for mass in mass_options_list:
                        rawdata_extracted_masses_dictionary[mass][f'Line_{line}'] = raw_dataframe[mass].to_numpy()
                rawdatasample = RawdataSampleClass.RawdataSample(experiment=self,
                                                                 name=sample_name,
                                                                 rawdata_dictionary=rawdata_extracted_masses_dictionary,
                                                                 dwelltime_dictionary=dwelltime_dictionary,
                                                                 sample_number=f'Sample_{sample_counter}',
                                                                 fill_value=self.fill_value)
                sample_counter += 1
                self.RawdataSample_objects_dictionary[sample_name] = rawdatasample

    def pass_sample_logfile_information(self, sample_number: str):
        return self.laserlog_object.get_log_information_of_rawdata_sample(sample_number)

    def build_rectangular_data(self):
        self.build_laser_log_object()
        self.gui.increase_progress(10)
        state_log = self.laserlog_object.build_sampleinlog_objects()
        if state_log is False:
            popup_error_message(title='Logfile Error',
                                message='Logfile shows new pattern starting without previous '
                                        'pattern being completed by end statement')
            self.gui.reset_progress()
            return
        self.gui.increase_progress(30)
        self.build_rawdatasample_objects()
        self.gui.increase_progress(10)
        for i in self.RawdataSample_objects_dictionary.values():
            i.build_rawdatamass_objects()
        self.gui.increase_progress(10)
        state = self.match_log_and_sample()
        if state is False:
            popup_error_message(title='Match Error',
                                message='Unable to match laser logfile and rawdata files!')
            self.gui.reset_progress()
            return
        for i in self.RawdataSample_objects_dictionary.values():
            i.build_true_rawdata_lines()
        self.gui.increase_progress(20)
        state = self.build_new_rawdata_files()
        self.gui.increase_progress(20)
        if state is False:
            popup_error_message(title='Export Path Error',
                                message='No Directory for the export of '
                                        'the new rectangular rawdata files has been chosen!')
            self.gui.reset_progress()
            return
        else:
            popup_info_message(title='File Created',
                               message='The rectangular rawdata Files have been successfully created.')

    def build_laser_ablation_times(self):
        # Step 1
        self.build_laser_log_object()
        # Step 2
        state_log = self.laserlog_object.build_sampleinlog_objects()
        if state_log is False:
            popup_error_message(title='Logfile Error',
                                message='Logfile shows new pattern starting without previous '
                                        'pattern being completed by end statement')
            self.gui.reset_progress()
            return
        # Step 3
        state = self.laserlog_object.build_laser_pattern_duration_sheet()
        if state is False:
            popup_error_message(title='Export Path Error',
                                message='No Directory for the export of the pattern duration file has been chosen!')
            self.gui.reset_progress()
            return

    def match_log_and_sample(self, match_by_line_count=False):
        length_of_sample_dictionary = self.laserlog_object.build_lengh_of_sample_dictionary()
        samples_in_log = self.laserlog_object.get_sampleinlog_objects_dictionary()
        if match_by_line_count is False:
            for k, i in enumerate(self.RawdataSample_objects_dictionary.values()):
                i.set_sample_in_log(samples_in_log[f'Sample_{k + 1}'])
                amount_of_log_lines = length_of_sample_dictionary[samples_in_log[f'Sample_{k + 1}']]
                amount_of_rawdata_lines = i.get_amount_of_lines()
                if amount_of_rawdata_lines == amount_of_log_lines:
                    pass
                else:
                    decider = popup_yesno_message(title='Logfile and and Rawdata match issue',
                                                  message='The amount of ablated lines dont match between the laser '
                                                          'logfile and the predetermined rawdata file.'
                                                          'Do you want to use automatic assignment? '
                                                          'This only works if all of your samples have a unique '
                                                          'amount of ablated lines.')
                    if decider is True:
                        self.match_log_and_sample(match_by_line_count=decider)
                        return True
                    if decider is False:
                        return False

        if match_by_line_count is True:
            for i in self.RawdataSample_objects_dictionary.values():
                for laserlog_object, amount_of_lines in length_of_sample_dictionary.items():
                    amount_of_samples = i.get_amount_of_lines()
                    if amount_of_samples == amount_of_lines:
                        i.set_sample_in_log(laserlog_object)

    def build_new_rawdata_files(self):
        # Get all dicts of mass dicts from the rawdata_sample instances
        for sample_name, instance in self.RawdataSample_objects_dictionary.items():
            full_rectangular_dictionary = {}
            mass_name_array = np.full(fill_value=0, shape=2)
            y_time_array = np.full(fill_value=0, shape=2)
            mainruns_array = np.full(fill_value=0, shape=2)
            iterator_array = np.full(fill_value=0, shape=2)
            # iterate over masses in dictionary
            first_mass = True
            for mass, mass_line_data in instance.get_rectangular_rawdata_dictionary().items():
                # get the length of the longest line per mass
                max_length = instance.get_max_length(mass)
                # Add a line for the mass column
                mass_name_array_part = np.full(fill_value=mass, shape=max_length * 2)
                mass_name_array = np.concatenate((mass_name_array, mass_name_array_part))
                # Build dwelltime_array_for_mass
                dwelltime_array = self.build_dwelltime_array(sample_name, mass)
                # build ytime array for mass
                y_array = np.full(fill_value='Y', shape=max_length)
                time_array = np.full(fill_value='Time', shape=max_length)
                y_time_array = np.concatenate((y_time_array, y_array, time_array))
                # iterate over the lines in the mass_line_dictionary
                for line, line_array in mass_line_data.items():
                    # Find the sample number
                    line_number = re.findall(r'\d+', line)  # Find all numeric substrings
                    sample_value = int(line_number[0])
                    # Bringall lines to the same size
                    extra_zeros = max_length - line_array.size
                    extra_zeros = np.zeros(extra_zeros)
                    build_array = np.concatenate((line_array, extra_zeros))
                    # save the lin data in a dictionary
                    if first_mass is True:
                        sample_name_array = np.full(fill_value=f'Sample {sample_value}', shape=2)
                        build_array = np.concatenate((sample_name_array, build_array, dwelltime_array))
                        full_rectangular_dictionary[line] = build_array
                    # Concatenate to lines if there is already data in the dictionary
                    if first_mass is False:
                        pre_line = full_rectangular_dictionary[line]
                        full_rectangular_dictionary[line] = np.concatenate((pre_line, build_array, dwelltime_array))
                first_mass = False
            mainruns = np.full(fill_value='MainRuns', shape=full_rectangular_dictionary['Sample 1'].size - 2)
            mainruns_array = np.concatenate((mainruns_array, mainruns))
            iterator = np.arange(full_rectangular_dictionary['Sample 1'].size - 2)
            iterator_array = np.concatenate((iterator_array, iterator))
            final_dataframe = pd.DataFrame(full_rectangular_dictionary)
            final_dataframe.insert(loc=0, column='Y_TIME_Array', value=y_time_array)
            final_dataframe.insert(loc=0, column='Mass Name', value=mass_name_array)
            final_dataframe.insert(loc=0, column='Iterator', value=iterator_array)
            final_dataframe.insert(loc=0, column='Mainruns', value=mainruns_array)
            state = self.export_data(final_dataframe, sample_name)
            if state is False:
                return False
        return True

    def build_dwelltime_array(self, sample, mass):
        return self.RawdataSample_objects_dictionary[sample].build_dwelltime_array(mass)

    def export_data(self, final_dataframe, sample):
        sample_name_without_csv = sample.removesuffix('.csv')
        try:
            final_dataframe.to_csv(
                path_or_buf=f'{self.get_export_path()}/{sample_name_without_csv}_rectangular_data.csv',
                index=False,
                sep=self.gui.get_separator_export(),
                header=False)
            return True
        except PermissionError:
            return False

    def export_pattern_duration_data(self, dictionary, name):
        path = self.get_export_path()
        try:
            writer = pd.ExcelWriter(f'{path}/{name}_pattern_duration.xlsx',
                                    engine='xlsxwriter')

            for sample, sample_dict in dictionary.items():
                dataframe = pd.DataFrame(sample_dict)
                dataframe.to_excel(writer, sheet_name=sample, index=False, header=False)

            writer.close()

            popup_info_message(title='File Created',
                               message='The Laser Duration file has been successfully created')
            return True
        except PermissionError:
            return False

    def get_export_path(self):
        return self.gui.get_export_path()

    def get_separator_export(self):
        return self.gui.get_separator_export()
