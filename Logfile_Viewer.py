

class LogfileViewer:

    def __init__(self, gui, master_window):
        self.gui = gui

        self.rectangles_dictionary = {}

        self.imzml_logfile_dictionary = {}

    def show_logfile(self):

        selected = self.gui.widgets.laser_type.get()
        if selected and selected in self.gui.modules:
            print(f"Running {selected}")
            logfile_dataframe = self.gui.modules[selected].run(self.gui.logfile_filepath)
        else:

            print("No module selected or module missing")
            return None

        self.gui.logfile = logfile_dataframe

        self.buid_rectangles(logfile=logfile_dataframe)



    def buid_rectangles(self, logfile):
        self.rectangles_dictionary = {}
        sample_number = 0
        self.imzml_logfile_dictionary = {}
        line_number = 0
        y_values = []
        names = []
        for idx, row in logfile.iloc[::2].iterrows():
            if line_number == 0:
                self.imzml_logfile_dictionary['Sample'] = {}
                self.imzml_logfile_dictionary['Sample']['time_per_pixel'] = int(row['Spotsize']) / int(row['Scan Speed(Î¼m/sec)'])
                #self.imzml_logfile_dictionary['Sample']['time_per_pixel'] = 20 / row['Scan Speed(Î¼m/sec)']
            line_number = line_number + 1
            if 'start' in row['Name']:
                sample_number += 1
            x_start = row['X(um)']/1000
            y_start = row['Y(um)']/1000
            width = (logfile.loc[idx + 1, 'X(um)'] - row['X(um)'])/1000
            height = int(row['Spotsize'])/1000

            if idx == 0:
                xmin = x_start
                xmax = x_start + width
                ymin = y_start
                ymax = y_start + height
            if x_start < xmin:
                xmin = x_start
            if (x_start + width) > xmax:
                xmax = (x_start + width)
            if y_start < ymin:
                ymin = y_start
            if (y_start + height) > ymax:
                ymax = (y_start + height)

            self.imzml_logfile_dictionary[row['Name']] = {}

            if row['Y(um)']/1000 in y_values:
                line_number = line_number - 1
                index = y_values.index(row['Y(um)']/1000)
                name = names[index]
                self.imzml_logfile_dictionary[row['Name']]['line_number'] = self.imzml_logfile_dictionary[name]['line_number']
            else:
                y_values.append(row['Y(um)'] / 1000)
                names.append(row['Name'])
                self.imzml_logfile_dictionary[row['Name']]['line_number'] = line_number


            self.imzml_logfile_dictionary[row['Name']]['x_start'] = x_start
            self.imzml_logfile_dictionary[row['Name']]['pixel_number'] = round(width/height)
            #self.imzml_logfile_dictionary[row['Name']]['pixel_number'] = round(width / 0.02)


        self.imzml_logfile_dictionary['Sample']['x_min'] = xmin
        self.imzml_logfile_dictionary['Sample']['spotsize'] = height
        #self.imzml_logfile_dictionary['Sample']['spotsize'] = 0.02




