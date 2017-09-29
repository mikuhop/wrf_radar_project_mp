__author__ = 'jtang8756'

# Prepareation
import numpy
import os
import utils

import netCDF4
import pyproj
import arcpy

# region helper functions
from utils import create_dirs, relocate


# endregion

def execute(in_netcdf, out_feat, levels=[20, 25, 30, 35, 40, 45], mask=None):
    # This is a very stupid fix for multiprocessing
    # But I am sure why arcpy.CheckoutExtension works
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"
    workspace = "in_memory"

    # Set all filenames
    temp_dir = os.path.dirname(os.path.abspath(in_netcdf))  # Emm, csv and img must be saved with .nc

    # UnComment this to skip existed results
    # if os.path.exists(relocate(fn_csv, cnt_dir, ".shp")):
    #    print("%s existed. Skip!" % relocate(fn_csv, cnt_dir, ".shp"))
    #    continue

    # ds = netCDF4.Dataset(in_netcdf)
    # # Level 7 == 3.5km
    # refl_l = numpy.ravel(ds.variables["REFL_10CM"])
    # lon_l = numpy.ravel(ds.variables["lon"])
    # lat_l = numpy.ravel(ds.variables["lat"])
    #
    # lon_l, lat_l = utils.projFunc(lon_l, lat_l)

    # fn_csv = relocate(in_netcdf, temp_dir, ".csv")
    # print fn_csv
    # if not os.path.exists(fn_csv):
    #     f_csv = open(fn_csv, "w")
    #     f_csv.write("Id,X,Y,Reflect\n")
    #
    #     for i in range(refl_l.shape[0]):
    #         if not refl_l[i] >= 10:
    #             continue
    #         refl = refl_l[i]
    #         lat = lat_l[i]
    #         lon = lon_l[i]
    #         f_csv.write("%d,%f,%f,%f\n" % (i, lon, lat, refl))
    #
    #     f_csv.close()
    #     print "NC to CSV:", fn_csv
    # else:
    #     print "Have CSV:", fn_csv

    #reflect = arcpy.CreateUniqueName(arcpy.ValidateTableName("reflect.shp"), workspace);
    #arcpy.MakeXYEventLayer_management(fn_csv, 'X', 'Y', reflect, utils.spatialRef, "Reflect")
    #layer1 = relocate(in_netcdf, temp_dir, ".img")
    #arcpy.PointToRaster_conversion(reflect, "Reflect", layer1, cellsize=utils.resolution)
    #arcpy.DefineProjection_management(layer1, utils.spatialRef)
    #print "CSV to Rsater:", layer1

    # Apply mask on if provided
    #if mask is not None:
    #    l2 = arcpy.sa.ExtractByMask(in_netcdf, mask)
    #    l21 = arcpy.sa.Con(l2, l2, 0, "VALUE >= 10")
    #else:
    layer1 = in_netcdf
    l21 = arcpy.sa.Con(layer1, layer1, 0, "VALUE >= 10")
    l22 = arcpy.sa.Con(arcpy.sa.IsNull(l21), 0, l21)
    arcpy.sa.ContourList(l22, out_feat, levels)
    print "Raster to Contour:", out_feat


if __name__ == "__main__":
    print "Do not run this directly"
    exit(0)
