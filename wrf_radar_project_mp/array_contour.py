__author__ = 'jtang8756'

import os
import sys
import utils
from utils import create_dirs, relocate

import arcpy

def execute(input_raster, output_feat, contour_levels=[15,20,25,30,35,40], mask=None):
    arcpy.env.workspace = "in_memory" 
    arcpy.env.overwriteOutput = True    
    arcpy.env.outputCoordinateSystem=utils.spatialRef
    d = arcpy.Raster(input_raster)
    # Apply mask if provided.
    if mask is not None:
        d1 = arcpy.sa.ExtractByMask(d, mask)
        d2 = arcpy.sa.Con(d1, d1, 0, 'VALUE >= 10')
    else:    
        d2 = arcpy.sa.Con(d, d, 0, 'VALUE >= 10')
    d21 = arcpy.sa.Con(arcpy.sa.IsNull(d2), 0, d2)
    d21.save(r"E:\scratch\T1.img")
    arcpy.sa.ContourList(d21, output_feat, contour_levels)

