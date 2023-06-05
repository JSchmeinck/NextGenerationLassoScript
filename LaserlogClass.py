import pandas as pd

import SampleinlogClass


class Laserlog:
    def __init__(self, experiment, clean_laserlog_dataframe: pd.DataFrame):
        self.experiment = experiment
        self.clean_laserlog_dataframe = clean_laserlog_dataframe
        self.sampleinlog_objects_dictionary = {}

    def divide_clean_logfile_dataframe_into_samples(self):
        df = self.clean_laserlog_dataframe
        sample_chunks_dictionary: dict = {}

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
                        self.experiment.send_error_message(title='Logfile Error',
                                                           message='Logfile shows new pattern starting without previous '
                                                                   'pattern being completed by end statement')
                        break

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
        for sample, logfile in sample_chunks_dictionary.items():
            sampleinlog = SampleinlogClass.Sampleinlog(sample=sample,
                                                       logfile_slice=logfile)

            self.sampleinlog_objects_dictionary[sample] = sampleinlog

    def get_log_information_of_rawdata_sample(self, sample_number: str):
        return self.sampleinlog_objects_dictionary[sample_number].get_true_line_information_dictionary(), self.sampleinlog_objects_dictionary[sample_number].get_outer_dimensions_dictionary()