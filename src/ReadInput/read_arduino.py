import serial
import threading
import json
import math
import os
import sys
toplevel_dir = os.path.join(os.path.dirname(__file__),
    os.path.pardir,
    os.path.pardir)

filename = os.path.join(toplevel_dir, "data", "data.txt")

running = True

referenceMv = 5000
interval = 250  # mV
distance_list = [150, 140, 130, 100, 60, 50, 40, 35, 30, 25, 20, 15]  # distance in cm for each 250 mV

class StopEvent:

    def __init__(self):
        self.is_set = False

    def set(self):
        self.is_set = True

def to_millivolts(val):
    return int(val * referenceMv / 1023)

def calibration(mV):
    """
    >>> calibration(0)
    150.0
    >>> calibration(240)
    140.4
    >>> calibration(3500)
    15
    >>> calibration(260)
    139.6
    """
    index = mV / interval
    if index >= len(distance_list) - 1:
        centimeters = distance_list[-1]
    else:
        frac = (mV % interval) / float(interval)
        centimeters = distance_list[index] - ((distance_list[index] - distance_list[index + 1]) * frac)

    return centimeters

def to_inches(cent):

    return cent / 2.54

def get_angles(indices, anglemin, anglemax, steps):
    angle = anglemin + (float(indices) / steps) * (anglemax - anglemin)
    return angle

def read_arduino(distances, ser, stop_event):
    # read the arduino until the user tells it to stop
    while not stop_event.is_set:
        try:

            line = ser.readline()
            # split it into a list of ints
            vals = [int(s.strip()) for s in line.split(', ')]

            # convert the distance to inches
            vals[0] = to_inches(calibration(to_millivolts(vals[0])))
            print "Adding " + str(vals) + "..."

            # this checks for funky input.
            if len(vals) == 3:
                distances.append(vals)
            else:
                raise ValueError()

        except ValueError:
            del distances[:]
            print "Invalid input received. Clearing data."
        except SerialException, OSError:
            pass
            # Just keep chuggin.

def save_data(distances, fn):

    # If the filename's parent folder doesn't exist, create it
    if not os.path.isdir(os.path.dirname(fn)):
        os.makedirs(os.path.dirname(fn))

    # save the data to the file!
    with open(fn, 'w') as outfile:

        json.dump(distances, outfile)

def main():

    # initialize the data and stop event
    distances =[]
    stop_event = StopEvent()

    # ask the user to start the program
    s = ''
    while s.lower() != 's':
        s = raw_input('Press s to start! --> ')

    # start reading in data off the arduino
    ser = serial.Serial('/dev/ttyACM0', 9600)
    t = threading.Thread(target=read_arduino,
                        args=(distances, ser, stop_event))
    t.start()

    # allow the user to stop at any time0
    q = ''
    while q.lower() != 'q':
        q = raw_input('Press q to quit! --> ')
    stop_event.set()

    # after we've stopped, save the data to a file.
    save_data(distances, filename)


if __name__ == '__main__':
    main()



