#coding=utf-8

import os
import csv
import cPickle

import datetime
import time
from pprint import pprint as pp

import numpy
from scipy.interpolate import interp1d

import pyproj
projStr = "+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"
projFunc = pyproj.Proj(projStr)


def date_to_timestamp(row):
    year = int(float(row['yyyy']))
    month = int(float(row['mm']))
    day = int(float(row['dd']))
    hour = int(float(row['hh']))
    minutes = int(float(row['MM']))
    row_date = datetime.datetime(year, month, day, hour, minutes, 0)
    return time.mktime(row_date.timetuple())

def main(input_csv_path, output_folder, date_format="refl_3_5km_%Y_%m_%d_%H_%M"):
    """Interpolate track from given csv file and pickle it to disk"""
    csvfile = open(input_csv_path) 
    reader = csv.DictReader(csvfile)
    interp_track_dict = {}
    for row in reader:
        try:
            ctime = date_to_timestamp(row)
            interp_track_dict[ctime] = projFunc(float(row['finalLon']), float(row['finalLat']))
        except:
            pass
    csvfile.close()
    pp(interp_track_dict)

    with open(os.path.join(output_folder, "Isabel.pickle"), "w") as track_dump:
        cPickle.dump(interp_track_dict, track_dump)

# Main
if __name__ == "__main__":
    pwd = os.path.abspath(".")
    main(os.path.join(os.path.dirname(pwd), "newtrack_d03_30min.csv"), pwd)

    raw_input("Done")








