# coding=utf-8


import os
import datetime
import time
import cPickle
import math
import sys
import logging

import utils
from add_basic_geometry import calc_field

import numpy

import arcpy
import arcpy.da

from pprint import pprint


def calc_closure(geom, x0, y0):
    parts = geom.getPart()
    closure = {}
    for part in parts:
        rad = numpy.array([math.atan2(y0 - point.Y, x0 - point.X) for point in part if point is not None])
        rad[rad < 0] += 2 * numpy.pi
        deg = ((rad * 180.0 / numpy.pi).astype('int32')).tolist()
        closure.update(dict(zip(deg, [True] * len(deg))))
    return closure


def line_dist(pt1, pt2):
    return ((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2) ** 0.5


def generate_dispersiveness(polygon, levels, workspace="in_memory"):
    arcpy.env.workspace = workspace
    dispersiveness = ""
    closure_str = ""
    fragmentation = ""
    roundness = ""
    adv_elongation = ""
    for l in levels:

        with arcpy.da.SearchCursor(polygon,
                                   ["AREA", "TO_EYE", "SHAPE@",
                                    "EYE_X", "EYE_Y", "AREA_CVX",
                                    "PERIM", "SUM_AREA"],
                                   where_clause="dBZ=%d AND TO_EYE<=600000" % l) as cur:
            cur.reset()
            # list for dispersiveness
            dlist = []
            # list for fragmentation
            flist = []
            # list for roundness
            rlist = []
            # list to collect areas
            _areas_list = []
            # dict for closure
            closure = dict(zip(range(360), [False]*360))

            for row in cur:
                # Dispersiveness
                dlist.append([row[0], row[1]])
                # For closure, we need exclude polygon in 50km buffer closed to the eye
                if row[1] >= 50000:
                    geom, x0, y0 = row[2:5]
                    cl = calc_closure(geom, x0, y0)
                    closure.update(cl)
                # Fragment
                flist.append([row[0], row[5]])
                # Roundness
                rlist.append([row[0], row[6], row[7]])
                # Area list
                _areas_list.append(row[0])

            # Calculate dispersiveness
            areas = numpy.array(dlist)
            if areas.shape != (0,):
                total_areas = numpy.sum(areas[:, 0])
                area_frac = areas[:, 0] / total_areas
                dist_weight = areas[:, 1] / 600000.0
                dispersiveness += "%f," % numpy.sum(area_frac * dist_weight)
            else:
                dispersiveness += ","

            # Calculate closure
            # Actually we don't need the closure dict in each level, we just need a final number.
            total_deg = sum(closure.values())
            if total_deg:
                closure_str += "%f," % (total_deg / 360.0)
            else:
                closure_str += ","

            # Calculate fragementation.
            fareas = numpy.array(flist)
            if fareas.shape != (0,):
                total_cvx_areas = numpy.sum(fareas[:, 1])
                solidity = total_areas / total_cvx_areas
                # Connectivity
                sareas = fareas.shape[0]
                conn = 1 - ((sareas - 1) / (math.log10(total_areas) + sareas))
                fragmentation += "%f," % (1 - solidity * conn)
            else:
                fragmentation += ","

            # Assymetry/Roundness
            # I think, it should be OK for each polygon, but I think it hurt nothing to calculate it here.
            rareas = numpy.array(rlist)
            if fareas.shape != (0,):
                max_rareas = rareas[numpy.argmax(rareas, 0)]
                # R = base_roundness * size_factor
                R = numpy.mean(4 * max_rareas[:, 0] * math.pi / numpy.square(max_rareas[:, 1]) * (
                    numpy.log(max_rareas[:, 0]) / numpy.log(max_rareas[:, 2])))
                roundness += "%f," % (1 - R)
            else:
                roundness += ","

            # Get largest 3 polygons
            if _areas_list:
                if len(_areas_list) < 3:
                    _area = min(_areas_list)
                else:
                    _area = sorted(_areas_list)[-3]
                # Second pass, get larget N polygons
                delete_list = ["in_memory\\L3", "in_memory\\BOX"]
                select3 = arcpy.Select_analysis(polygon, delete_list[0], where_clause="AREA>=%f" % _area)
                # Get bounding box for entire area
                arcpy.MinimumBoundingGeometry_management(delete_list[0], delete_list[1], "RECTANGLE_BY_AREA",
                                                         mbg_fields_option="MBG_FIELDS", group_option="ALL")
                with arcpy.da.SearchCursor(delete_list[1], ["MBG_Width", "MBG_Length"]) as cur2:
                    for r in cur2:
                        adv_elongation += "%f," % (row[1] / row[0])

                map(arcpy.Delete_management, delete_list)
            else:
                adv_elongation += ","

    return dispersiveness, closure_str, fragmentation, roundness, adv_elongation


def add_track_position(polygon, timestamp, track_dict):
    arcpy.AddField_management(polygon, "EYE_X", "DOUBLE")
    arcpy.AddField_management(polygon, "EYE_Y", "DOUBLE")
    arcpy.AddField_management(polygon, "TO_EYE", "DOUBLE")
    arcpy.AddField_management(polygon, "CVX_TO_EYE", "DOUBLE")
    x0, y0 = track_dict[timestamp]
    with arcpy.da.UpdateCursor(polygon,
                               ["SHAPE@", "CNTRX", "CNTRY",
                                "TO_EYE", "CNTRX_CVX", "CNTRY_CVX",
                                "CVX_TO_EYE", "EYE_X", "EYE_Y"]) as cur:
        for row in cur:
            row[3] = line_dist((row[1], row[2]), (x0, y0))
            row[6] = line_dist((row[4], row[5]), (x0, y0))
            row[7] = x0
            row[8] = y0
            cur.updateRow(row)
    print "%s: polygon distance to eye; convex hull distance to eye; closure" % polygon


def clean_fields(polygon):
    F = arcpy.ListFields(polygon)
    for field in F:
        if field.name.find("_1") != -1:
            arcpy.DeleteField_management(polygon, field.name)
            print "%s: Field %s deleted" % (polygon, field.name)
    pass


def execute(input_feat, output_feat, track_dict, date_format, levels=[20, 25, 30, 35, 40], prefix_start=0,
            prefix_end=-4):
    arcpy.env.overwriteOutput = True
    arcpy.env.workspace = "in_memory"
    try:
        # Copy to destination
        arcpy.CopyFeatures_management(input_feat, output_feat)
        print "Copying %s -> %s" % (input_feat, output_feat)
        # Get timestamp
        q = os.path.basename(input_feat)
        timestamp = time.mktime(datetime.datetime.strptime(q[prefix_start:prefix_end], date_format).timetuple())
        # Add distance to track
        add_track_position(output_feat, timestamp, track_dict)
        # Clean fields
        clean_fields(output_feat)
        # Dispersivness and EVERYTHING
        dispersive = generate_dispersiveness(output_feat, levels)
        print "OK", dispersive
        return dispersive
    except Exception, ex:
        logging.exception(ex.message)
        return "Error"


def main(workspace, date_format="%Y%m%d_%H%M%S", track_pickle=None):
    stage1 = utils.stage1_folder
    stage2 = utils.stage2_folder

    utils.create_dirs([stage2])

    track_pickle = track_pickle or utils.track_pickle
    track_dict = cPickle.load(open(track_pickle))

    error_list = []
    disperiveness_list = {}

    output_file = open(os.path.join(utils.work_base_folder, "Dispersiveness.csv"), "w")
    output_file.write("date_string,dispersiveness\n")

    for q in utils.list_folder_sorted_ext(folder=stage1, ext=".shp"):
        f = os.path.join(stage1, q)
        adv_feature = utils.relocate(q, stage2)
        r = execute(f, adv_feature, track_dict, date_format)
        if r is None:
            error_list.append(r)
        else:
            output_file.write("%s,%f\n" % (q, r))

    output_file.close()

    print "Done"
    print "Errors:", error_list
