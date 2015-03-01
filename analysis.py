''' Module for analyzing results retrieved from Gamry

Author: Rich Winslow
Principal Investigators: Prof. Paul Wright, Prof. James Evans
University: University of California, Berkeley
'''

import matplotlib
# matplotlib.use('SVG')

import matplotlib.pyplot as plt
import numpy

font = {'family': 'Arial', 'size': 16}
matplotlib.rc('font', **font)


class EIS:

    ''' Analyzes data from Gamry EIS

    Pulls data from .dta file for plotting and analysis. Can look at the
    Nyquist plot and determine the DC resistance for ionic conductivity.

    '''

    def __init__(self, filename=None, thickness=0.001, area=1):
        ''' Opens file and retrieves data.

        Retrieves time, frequency, real impedance, imaginary impedance,
        magnitude, and phase. Assumes that the first part of the file is an
        OCV test and that the header for the table consists of two lines.

        Unit requirements:
            R_solution [ohm]
            Thickness [cm]
            Area [cm^2]
        '''

        self.time = []
        self.freq = []
        self.real = []
        self.imag = []
        self.phaz = []
        self.magn = []

        self.r_solution = None
        self.conductivity = None

        self.filename = filename
        self.thickness = thickness
        self.area = area

        with open(filename, errors='replace') as f:
            rows = f.readlines()

            switch = False
            for index, row in enumerate(rows):
                row = row.split()
                try:
                    if row:
                        if row[0] == 'ZCURVE':
                            switch = index + 2

                        if (self.is_num(row[0]) and switch and index > switch):
                            self.time.append(float(row[1]))
                            self.freq.append(float(row[2]))
                            self.real.append(float(row[3]))
                            self.imag.append(float(row[4]))
                            self.magn.append(float(row[6]))
                            self.phaz.append(float(row[7]))
                except Exception:
                    raise

            try:
                self.calculate_conductivity()
            except Exception:
                raise

    def calculate_conductivity(self):
        try:
            max_imag_index = self.imag.index(max(self.imag))
            self.r_solution = self.real[max_imag_index]
            self.conductivity = (
                (self.thickness * 1000) / (self.area * self.r_solution))
        except Exception:
            raise

    def list_metrics(self):
        print('File: ' + self.filename)
        print('R_solution: ' + str(self.r_solution) + ' ohm')
        print('Thickness: ' + str(self.thickness) + ' cm')
        print('Area: ' + str(self.area) + ' cm^2')
        print('Conductivity: ' + str(self.conductivity) + ' mS/cm')
        print('--')

    def plot_nyquist(self, log_plot=False, ylim=None, save_svg=False):
        ''' Plots real impedance vs negative imaginary impedance '''

        self.calculate_conductivity()
        conductivity_string = "{0:.3f}".format(self.conductivity)

        if log_plot:
            plt.loglog(self.real, [-1 * v for v in self.imag],
                       marker='.', markersize=15)
        else:
            plt.plot(self.real, [-1 * v for v in self.imag],
                     marker='.', markersize=15)

        if ylim:
            plt.ylim(ylim[0], ylim[1])

        plt.xlabel('Z_real (ohm)')
        plt.ylabel('(-) Z_imag (ohm)')

        if save_svg:
            plt.savefig(self.filename + '.svg')
        else:
            plt.title('Nyquist Plot - ' +
                      conductivity_string + ' mS/cm - ' + self.filename)
            plt.show()

    def is_num(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False


class CV:

    ''' Analyzes data from Gamry cyclic voltammetry data

    Pulls data from .dta file for plotting and analysis.

    '''

    def __init__(self, filename=None):
        ''' Opens file and retrieves data. '''

    # Pt  T     Vf    Im  Vu  Sig Ach IERange Over
    # s   V vs. Ref.  A   V   V   V   #       bits

        self.cycles = {}

        with open(filename, errors='replace') as f:
            rows = f.readlines()

            switch = False
            current_cycle_time = []
            current_cycle_voltage = []
            current_cycle_current = []

            for index, row in enumerate(rows):
                row = row.split()
                try:
                    if row:
                        if row[0][0:5] == 'CURVE':
                            curve_number = int(row[0][5::])
                            switch = index + 2
                            if current_cycle_time:
                                self.cycles[curve_number-1] = {
                                    'time': current_cycle_time,
                                    'voltage': current_cycle_voltage,
                                    'current': current_cycle_current,
                                }
                                current_cycle_time = []
                                current_cycle_voltage = []
                                current_cycle_current = []

                        if (self.is_num(row[0]) and switch and index > switch):
                            # Save data and convert current to mA
                            current_cycle_time.append(float(row[1]))
                            current_cycle_voltage.append(float(row[2]))
                            current_cycle_current.append(float(row[3]) * 1000)

                except Exception:
                    raise

            # Save data and convert current to mA
            self.cycles[curve_number] = {
                'time': current_cycle_time,
                'voltage': current_cycle_voltage,
                'current': current_cycle_current * 1000,
            }

    def plot_current_voltage(self, cycle_index=0, title=None):
        ''' Plots current vs voltage for one or all cycles '''

        if cycle_index:
            plt.plot(self.cycles[cycle_index]['voltage'],
                     self.cycles[cycle_index]['current'],
                     marker='.', markersize=12)
        else:
            for i in range(1,len(self.cycles)):
                plt.plot(self.cycles[i]['voltage'],
                         self.cycles[i]['current'],
                         marker='.', markersize=12)

        plt.xlabel('Potential (V)')
        plt.ylabel('Current (mA)')

        plt.title('CV ' + str(title))
        plt.show()

    def is_num(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False
