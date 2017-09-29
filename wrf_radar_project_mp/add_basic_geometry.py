#coding=utf-8

"""This script calculate shape-metric those are NOT relavent to the coordinates of the eye"""

import os
import sys
import utils
import arcpy


def calc_field(feature, fields_dict, slient=False):
    F = [p.name for p in arcpy.ListFields(feature)]   
    for k, v in fields_dict.iteritems():
        if not k in F:
            arcpy.AddField_management(feature, k, "DOUBLE")
        arcpy.CalculateField_management(feature, k, v, "PYTHON")
        if not slient:
            print "Calculate %s = %s in %s" % (k, v, feature)

    
def rename_field(feature, old_field, new_field):    
    calc_field(feature, {new_field: '!%s!' % old_field})
    arcpy.DeleteField_management(feature, old_field)


def add_metric_to_polygon_with_equation(polygon, shape_metric, suffix=""):
    """Calculate basic shape metrics"""
    S = shape_metric
    s = {}
    for k,v in S.iteritems():
        field_name = k if k.find("%s") == -1 else k % suffix
        field_name = field_name[:10]
        s[field_name] = v
    calc_field(polygon, s)
    return s.keys()


def add_basic_geometry_attr(polygon, suffix=""):
    arcpy.AddGeometryAttributes_management(polygon, "AREA;PERIMETER_LENGTH;CENTROID", Length_Unit="KILOMETERS", Area_Unit="SQUARE_KILOMETERS")
    rename_field(polygon, "POLY_AREA", "AREA%s" % suffix)
    rename_field(polygon, "PERIMETER", "PERIM%s" % suffix)
    rename_field(polygon, "CENTROID_X", "CNTRX%s" % suffix)
    rename_field(polygon, "CENTROID_Y", "CNTRY%s" % suffix)
    return ["AREA%s" % suffix, "PERIM%s" % suffix, "CNTRX%s" % suffix, "CNTRY%s" % suffix]

    
def preprocess(polygon, out):
    arcpy.Copy_management(polygon, out)
    pass


def execute(input_feat, output_feat):
    try:
        # Multiprocess fix
        arcpy.env.overwriteOutput = True
        arcpy.env.workspace = "in_memory"

        # Smooth polygons
        preprocess(input_feat, output_feat)
        
        # Add shape metrics
        add_basic_geometry_attr(output_feat)
            
        # Create unique name in memory workspace
        box_shp = arcpy.CreateUniqueName("box")
        cvx_shp = arcpy.CreateUniqueName("convexhull")

        # Then calculate elongation
        arcpy.MinimumBoundingGeometry_management(output_feat,  box_shp, "RECTANGLE_BY_AREA", mbg_fields_option="MBG_FIELDS")
        # This is an in-memory feature, so not limited to 10-letters filed name
        arcpy.JoinField_management(output_feat, "FID",  box_shp, "ORIG_FID", fields=["MBG_Width", "MBG_Length", "MBG_Orientation"])
        calc_field(output_feat, {"Elongation": "!MBG_Width!/!MBG_Length!"})
        # Then we need change name of the MBG_WIDTH and MBG_LENGTH to avoid future conflict
        rename_field(output_feat, "MBG_Width", "BOX_WIDTH")
        rename_field(output_feat, "MBG_Length", "BOX_LENGTH")
        rename_field(output_feat, "MBG_Orient", "BOX_ORIENT")
        
        # Then calculate convex hull for the polygon
        arcpy.MinimumBoundingGeometry_management(output_feat, cvx_shp, "CONVEX_HULL", mbg_fields_option="NO_MBG_FIELDS")
        cvx_fields = add_basic_geometry_attr(cvx_shp, suffix="_CVX")
        arcpy.JoinField_management(output_feat, "FID", cvx_shp, "ORIG_FID", fields=cvx_fields)

        # Related to convex hull, moved from dispersiveness
        calc_field(output_feat, {"SOLIDITY": "!AREA!/!AREA_CVX!", "CONVEXITY": "!PERIM_CVX!/!PERIM!", "COMPACT": "(!AREA! ** 0.5)/(0.282 * !PERIM!)"})
                           
        # Calculate statistics, join back.
        stats_table = arcpy.CreateUniqueName("temp_statistic", "in_memory")
        arcpy.Statistics_analysis(output_feat, out_table=stats_table, statistics_fields="AREA SUM", case_field="dbZ")
        arcpy.JoinField_management(output_feat, "dBZ", stats_table, "dBZ", fields=["SUM_AREA"])
        arcpy.Delete_management(stats_table)
                                         
        print "OK"
    except Exception, ex:
        print >> sys.stderr, ex.message
        return input_feat


def main(workspace=None):

    pwd = utils.work_base_folder
    cnt_polygon_folder = os.path.join(pwd, utils.cnt_polygon_folder)
    stage1_folder = os.path.join(pwd, utils.stage1_folder)
    arcpy.env.workspace = "in_memory"
    arcpy.env.overwriteOutput = True        
    
    utils.create_dirs([stage1_folder, arcpy.env.workspace])   
    
    targets = utils.list_folder_sorted_ext(os.path.join(pwd, cnt_polygon_folder), ".shp")
    for j in targets:
        
        # We need give a full path, otherwise ArcGIS will look for it in workspace.
        orig = os.path.join(pwd, cnt_polygon_folder, j)
        q = utils.relocate(orig, stage1_folder)
        
        # Main geoprocessing routine
        execute(orig, q, arcpy.env.workspace)
        
        print "OK"
        
    
    


