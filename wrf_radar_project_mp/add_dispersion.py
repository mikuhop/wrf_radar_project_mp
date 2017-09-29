#coding=utf-8
"""This script add dispersion field to existed TC cases"""

import os
import datetime
import time
import cPickle
import math

import utils
from add_calc_geometry import calc_field

import numpy

import arcpy
import arcpy.da
arcpy.env.workspace = r"in_memory"
arcpy.env.overwriteOutput = True

pwd = utils.work_base_folder
stage2 = os.path.join(pwd, utils.stage2_folder)
track_dict = cPickle.load(open(utils.track_pickle))

def generate_dispersiveness(polygon):
    dispersiveness = -999
    # Index:                                 0          1            2         3           4           5              6             7
    with arcpy.da.UpdateCursor(polygon, ["AREA_", "TO_EYE"]) as cur:
        areas = numpy.array([[row[0], row[1]] for row in cur])
        total_areas = numpy.sum(areas[:,0])
        area_frac = areas[:,0] / total_areas
        dist_weight = areas[:,1] / 600000.0      
        dispersiveness = numpy.sum(area_frac * dist_weight)
        print "Dispersiveness=%f" % dispersiveness
        
    return dispersiveness

def main():

    error_list = []
    
    output_file = open(os.path.join(utils.work_base_folder, "dispersiveness.csv"), "w")
    output_file.write("date_string,dispersiveness\n")
    
    for q in utils.list_folder_sorted_ext(folder=stage2, ext=".shp"):
        try:
            f = os.path.join(stage2, q)

            # Get dispersiveness
            dispersive = generate_dispersiveness(f)              
            output_file.write("%s,%f\n" % (q, dispersive))
            
        except Exception, ex:
            print ex.message
            error_list.append(q)
    
    output_file.close()        
    print "Done"
    print "Error:", error_list

if __name__ == "__main__":
    main()