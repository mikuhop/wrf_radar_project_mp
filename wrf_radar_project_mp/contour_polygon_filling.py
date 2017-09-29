__author__ = 'jtang8756'

import os

import utils
from add_basic_geometry import calc_field

import arcpy


def execute(in_feature, out_feature, contour_level=None):

    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"
    workspace = "in_memory"

    # Maintain a list so we can easily merge them back
    fn_list = []
    temp_file = []
        
    cntr = os.path.basename(in_feature)

    if contour_level is None:
        levels = range(15,50,5)
    else:
        levels = contour_level

    for value in levels:
        
        try:
            out1 = arcpy.CreateUniqueName(arcpy.ValidateTableName(cntr.replace(".shp", "_%d" % value)), workspace)
            arcpy.Select_analysis(in_feature, out1, where_clause="CONTOUR=%d" % value)
            print "Select into %s where contour=%d" % (out1, value)   
            temp_file.append(out1)
                
            out2_0 = arcpy.CreateUniqueName(out1, workspace)
            arcpy.FeatureToPolygon_management(out1, out2_0)
            out2_1 = arcpy.CreateUniqueName(out2_0, workspace)
            arcpy.Union_analysis([out2_0], out2_1, join_attributes="ONLY_FID", gaps="NO_GAPS")
            out2 = arcpy.CreateUniqueName(out2_1, workspace)
            arcpy.Dissolve_management(out2_1, out2, multi_part="SINGLE_PART")
            temp_file.append(out2_0)
            temp_file.append(out2_1)
            temp_file.append(out2)
            
            out3 = arcpy.CreateUniqueName(out2, workspace)
            # Remove some points
            arcpy.Generalize_edit(out2, "200 Meters")
            # Then do a smooth
            out3 = arcpy.CreateUniqueName(out2, workspace)
            arcpy.SmoothPolygon_cartography(out2, out3, "PAEK", "7000 Meters", "NO_FIXED")
            print "Copy and smooth %s -> %s" % (out2, out3)              
            calc_field(out3, {"AREA1":  "!shape.area!", "dbZ": "%d" % value }, True)
            temp_file.append(out3)
            
            out4 = arcpy.CreateUniqueName(out3, workspace)
            arcpy.Select_analysis(out3, out4, where_clause="AREA1>30000000")
            temp_file.append(out4)
            
            fn_list.append(out4)
    
        except Exception, ex:
            print ex.message
            continue
            
        # End of loop
        
    print fn_list, "->", out_feature
    if fn_list:
        arcpy.Merge_management(fn_list, out_feature)  
        map(arcpy.Delete_management, temp_file)
        print "OK"
    else:
        print "EMPTY"



