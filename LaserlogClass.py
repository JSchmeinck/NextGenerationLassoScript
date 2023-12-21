import pandas as pd
import math
from tkinter import filedialog
import numpy as np
import SampleinlogClass


class Laserlog:
    def __init__(self, experiment, clean_laserlog_dataframe: pd.DataFrame, name: str):
        self.experiment = experiment
        self.clean_laserlog_dataframe = clean_laserlog_dataframe
        self.sampleinlog_objects_dictionary = {}
        self.name = name

    def divide_clean_logfile_dataframe_into_samples(self):
        df = self.clean_laserlog_dataframe
        sample_chunks_dictionary: dict = {}

        if self.experiment.synchronized and self.experiment.gui.widgets.multiple_samples.get() is False:
            if self.experiment.gui.widgets.first_line_synchronization.get():
                df = df.drop([0, 1])
                df = df.reset_index(drop=True)
            sample_chunks_dictionary[f'Sample_1'] = df
            return sample_chunks_dictionary

        # Initialize variables
        start_idx = None
        chunk_counter = 1

        # Iterate over DataFrame rows
        for idx, row in df.iterrows():
            marker = row['Name']

            # Check if marker value is not NaN
            if pd.notnull(marker):
                marker = str(marker)

                # Check for start condition
                if 'start' in marker:
                    if start_idx is not None:
                        return False

                    # Set start index for new chunk
                    start_idx = idx

                # Check for end condition
                if 'end' in marker:
                    # Set end index for the current chunk
                    end_idx = idx

                    # Add the current row to the chunk
                    sample_chunk = df.iloc[start_idx:end_idx + 2]
                    sample_chunk = sample_chunk.reset_index(drop=True)
                    sample_chunks_dictionary[f'Sample_{chunk_counter}'] = sample_chunk
                    chunk_counter += 1

                    # Reset start and end indices
                    start_idx = None

        return sample_chunks_dictionary

    def build_sampleinlog_objects(self):
        sample_chunks_dictionary = self.divide_clean_logfile_dataframe_into_samples()
        if sample_chunks_dictionary is False:
            return False
        for sample_number, logfile in sample_chunks_dictionary.items():
            sampleinlog = SampleinlogClass.Sampleinlog(sample=sample_number,
                                                       logfile_slice=logfile,
                                                       log=self)

            self.sampleinlog_objects_dictionary[sample_number] = sampleinlog
        return True

    def get_log_information_of_rawdata_sample(self, sample_number: str):
        return self.sampleinlog_objects_dictionary[sample_number].get_true_line_information_dictionary(), self.sampleinlog_objects_dictionary[sample_number].get_outer_dimensions_dictionary(), self.sampleinlog_objects_dictionary[sample_number].get_scan_speed()

    def send_error_message(self, title, message):
        self.experiment.send_error_message(title=title, message=message)

    def build_lengh_of_sample_dictionary(self):
        length_of_sample_dictionary = {}
        for i in self.sampleinlog_objects_dictionary.values():
            length_of_sample = i.get_amount_of_lines()
            length_of_sample_dictionary[i] = length_of_sample
        return length_of_sample_dictionary

    def build_laser_pattern_duration_sheet(self):
        sample_line_lengh_dictionary = {}
        for sample, instance in self.sampleinlog_objects_dictionary.items():
            line_name_array = np.full(fill_value='Line Name', shape=1)
            line_duration_array = np.full(fill_value='Line Duration', shape=1)
            sample_line_lengh_dictionary[sample] = {}
            scan_speed = instance.get_scan_speed()
            raw_line_dictionary = instance.get_true_line_information_dictionary(line_pattern_sheet=True)
            if raw_line_dictionary is False:
                self.experiment.gui.notifications.notification_error(header='LogFile Error', body='Not able to match row in the laser logfile'
                                                                       ' to an ablation line')
            for line, line_info in raw_line_dictionary.items():

                sample_line_lenghts_um = int((line_info[f'{line_info["lines included"][0]}_x_end'] -
                                                    line_info[
                                                        f'{line_info["lines included"][0]}_x_start']))
                duration_of_line = math.ceil(sample_line_lenghts_um/scan_speed)
                duration = np.full(fill_value=duration_of_line, shape=1)
                name = np.full(fill_value=line, shape=1)

                line_name_array = np.concatenate((line_name_array, name))
                line_duration_array = np.concatenate((line_duration_array, duration))

            sample_line_lengh_dictionary[sample]['Line Number'] = line_name_array
            sample_line_lengh_dictionary[sample]['Duration in seconds'] = line_duration_array

        state = self.export(sample_line_lengh_dictionary)
        if state is False:
            return False
        return True


    def export(self, dictionary):
        return self.experiment.export_pattern_duration_data(dictionary=dictionary, name=self.name)

    def get_sampleinlog_objects_dictionary(self):
        return self.sampleinlog_objects_dictionary


