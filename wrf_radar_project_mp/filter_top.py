# coding=utf-8
import os
import sys

import utils

import arcpy
import arcpy.da

# Select largest N polygon for given dBZ
def select_top_n(input_feature, output_dir, sort_column='AREA', filter_column='dbZ', values=[], top_count=1):
    
    arcpy.env.workspace = "in_memory"
    arcpy.env.overwriteOutput = True
    
    # if dBZ values not given, choose uniques.
    if not values:
        with arcpy.da.SearchCursor(input_feature, [filter_column]) as cur:
            cur.reset()
            values = list(set([row[0] for row in cur]))
            
    # Iterate each levels, because we always have `AREA`, so can hard code it.
    for value in values:
        sub_level_dir = os.path.join(output_dir, str(value))
        if not os.path.exists(sub_level_dir):
            os.makedirs(sub_level_dir)
        with arcpy.da.SearchCursor(input_feature, [sort_column], where_clause="%s=%s" % (filter_column, str(value))) as cur:
            cur.reset()
            sort_field = list(reversed(sorted([row[0] for row in cur])))
            if not sort_field:
                continue
            if len(sort_field) < top_count:
                threshold = sort_field[-1]
            else:
                threshold = sort_field[top_count - 1]
            
        # Now output it
        output_name = arcpy.ValidateTableName(os.path.basename(input_feature) + "_" + filter_column)
        arcpy.Select_analysis(input_feature, os.path.join(sub_level_dir, output_name), where_clause='%s>=%s AND %s=%s' % (sort_column, str(threshold), filter_column, str(value)))
        print("Select top %d in %s -> %s" % (top_count, input_feature, output_name))


if __name__ == "__main__":
    base_folder = sys.argv[1]
    os.chdir(base_folder)
    source = 'adv_metric'
    output = 'top_1'
    utils.create_dirs([output])
    
    for q in utils.list_folder_sorted_ext(folder="adv_metric", ext='.shp'):
        select_top_n(os.path.join(source, q), output)
        
    