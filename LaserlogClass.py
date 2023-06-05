import pandas as pd


class Laserlog:
    def __init__(self, clean_laserlog_dataframe: pd.DataFrame):
        self.clean_laserlog_dataframe = clean_laserlog_dataframe
        self.sampleinlog_objects_dictionary = {}

    def divide_clean_logfile_dataframe_into_samples(self):
        df = self.clean_laserlog_dataframe
        chunks = []

        # Initialize variables
        start_idx = None
        end_idx = None
        pause_flag = False

        # Iterate over DataFrame rows
        for idx, row in df.iterrows():
            marker = row['Name']

            # Check if marker value is not NaN
            if pd.notnull(marker):
                marker = str(marker)

                # Check for start condition
                if 'start' in marker:
                    # Check if previous chunk is already in progress
                    if start_idx is not None:
                        # Add previous chunk to the list
                        chunk = df.iloc[start_idx:end_idx + 1]
                        chunks.append(chunk)

                    # Set start index for new chunk
                    start_idx = idx
                    end_idx = None
                    pause_flag = False

                # Check for end condition
                if 'end' in marker:
                    # Set end index for the current chunk
                    end_idx = idx

                    # Add the current row to the chunk
                    chunk = df.iloc[start_idx:end_idx + 1]
                    chunks.append(chunk)

                    # Reset start and end indices
                    start_idx = None
                    end_idx = None
                    pause_flag = False

                # Check for pause condition
                if 'pause' in marker:
                    # Set pause flag to True
                    pause_flag = True

                # Check if pause flag is True and next row has 'start' condition
                if pause_flag and 'start' in marker:
                    # Add previous chunk to the list
                    chunk = df.iloc[start_idx:end_idx + 1]
                    chunks.append(chunk)

                    # Set start index for new chunk
                    start_idx = idx
                    end_idx = None
                    pause_flag = False

        # Add the last chunk if it hasn't been added yet
        if start_idx is not None and end_idx is None:
            chunk = df.iloc[start_idx:]
            chunks.append(chunk)

        # chunks list now contains separate DataFrames representing the chunks of the original DataFrame

        return chunks

    def build_sampleinlog_objects(self):
        pass

    def get_log_information_of_rawdata_sample(self, sample_name: str):
        pass