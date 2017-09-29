# coding=utf-8
# The multi-processing call of arcpy is buggy. I think later we should always use MPI instead of simple multi-processing map

# Multiple core processing

import os
import sys
from pprint import pprint

import utils
import add_advanced_geometry
import add_basic_geometry
import array_contour
import wrfout_contour
import contour_polygon_filling

import multiprocessing
import cPickle
import itertools


import pyproj
import arcpy


def call_func(func_args_tuple):
    __func = func_args_tuple[0]
    __args = func_args_tuple[1]
    return __func(*__args)


def create_func_args_tuple(func_name, *args):
    __func = [func_name] * len(args[0])
    __args = zip(*args)
    return zip(__func, __args)


def start_mp(work_base_folder,
             file_list=None,
             masks=None,
             levels=[15, 20, 25, 30, 35, 40],
             working_mode="wrf",
             stage2_datetime_format="refl_3_5km_%Y_%m_%d_%H_%M",
             skip_list=[],
             discard=False):
    arcpy.CheckOutExtension("Spatial")

    # pool = multiprocessing.Pool(4)

    proj = pyproj.Proj(utils.projStr)

    arcpy.env.workspace = "in_memory"
    arcpy.env.overwriteOutput = True

    # 1. We need setup folders
    base = work_base_folder
    cnt_folder = os.path.join(base, utils.cnt_folder)
    cnt_polygon_folder = os.path.join(base, utils.cnt_polygon_folder)
    stage1_folder = os.path.join(base, utils.stage1_folder)
    stage2_folder = os.path.join(base, utils.stage2_folder)
    utils.create_dirs([cnt_folder, cnt_polygon_folder, stage1_folder, stage2_folder], discard)

    # Contour
    if file_list is not None:
        base_input = file_list # Since we have sorted timestamp input, we don't have to sort them, otherwise it could be wrong
    else:
        # base_input = utils.list_folder_sorted_ext(base, ".nc" if working_mode == "wrf" else ".img")
        base_input = utils.list_folder_sorted_ext(base, ".img")

    # Get the full name of input files, contour polygon
    base_input_path = [os.path.join(base, p) for p in filter(None, base_input)]
    cnt_output_path = [utils.relocate(p, cnt_folder, ".shp") for p in base_input_path]
    levels_arg = [levels] * len(base_input_path)
    # if not masks:
    #     mask_list = [None] * len(base_input)
    # elif type(masks) is str:
    #     mask_list = [masks] * len(base_input)
    # elif len(masks) == len(base_input):
    #     mask_list = masks
    # else:
    #     raise ValueError("mask_list is not valid. It must be a list, or a single mask, or None")
    mask_list = [None] * len(base_input)

    # Get the contour function
    contour_func = wrfout_contour.execute if working_mode == "wrf" else array_contour.execute
    if 'contour' not in skip_list:
        if 1:
            [p(*q) for (p, q) in
             create_func_args_tuple(contour_func, base_input_path, cnt_output_path, levels_arg, mask_list)]
        else:
            pool.map(call_func,
                     create_func_args_tuple(contour_func, base_input_path, cnt_output_path, levels_arg, mask_list))
    else:
        pprint("Contour skipped")

    # Fill contour, we need refresh filelist in cnt_folder
    cnt_input = utils.list_folder_sorted_ext(cnt_folder, ".shp")
    cnt_input_path = [os.path.join(cnt_folder, p) for p in cnt_input]
    cnt_output_polygon_path = [utils.relocate(p, cnt_polygon_folder, ".shp").replace("-", "_") for p in cnt_input]
    levels_arg = [levels] * len(cnt_input_path)
    if 'smooth' not in skip_list:
        if 1:
            [p(*q) for (p, q) in
             create_func_args_tuple(contour_polygon_filling.execute, cnt_input_path, cnt_output_polygon_path, levels_arg)]
        else:
            pool.map(call_func,
                     create_func_args_tuple(contour_polygon_filling.execute, cnt_input_path, cnt_output_polygon_path,
                                            levels_arg))
    else:
        pprint("Smoothing and polygonize skipped")

    # Get basic metric
    bsm_input = utils.list_folder_sorted_ext(cnt_polygon_folder, ".shp")
    bsm_input_path = [os.path.join(cnt_polygon_folder, p) for p in bsm_input]
    bsm_output_path = [utils.relocate(p, stage1_folder, ".shp") for p in bsm_input]
    levels_arg = [levels] * len(bsm_input_path)
    if 'basic' not in skip_list:
        if 1:
            [p(*q) for (p, q) in create_func_args_tuple(add_basic_geometry.execute, bsm_input_path, bsm_output_path)]
        else:
            pool.map(call_func, create_func_args_tuple(add_basic_geometry.execute, bsm_input_path, bsm_output_path))
    else:
        pprint("Basic shape metrics skipped")

    # We will automatically interpolate track for radar.    
    if working_mode != "wrf":
        import interpolate_track
        interpolate_track.main(utils.ibtrac, work_base_folder, stage1_folder, "%Y%m%d_%H%M%S")

    asm_input = utils.list_folder_sorted_ext(stage1_folder, ".shp")
    asm_input_path = [os.path.join(stage1_folder, p) for p in asm_input]
    asm_output_path = [utils.relocate(p, stage2_folder, ".shp") for p in asm_input]
    # It is a little bit complex for advanced shape metrics
    track_pickle = os.path.join(work_base_folder, "%s.pickle" % utils.case_name)
    track_dict = cPickle.load(open(track_pickle))
    l = len(asm_input)
    date_format = stage2_datetime_format
    levels_arg = [levels] * l
    func_stub = create_func_args_tuple(add_advanced_geometry.execute, asm_input_path, asm_output_path, [track_dict] * l,
                                       [date_format] * l, levels_arg)
    # if not __debug__:
    #     dispersiveness = pool.map(call_func, func_stub)
    # else:
    # No matter how fast from beginning, this step must be single-threaded, because return may hang.
    dispersiveness = [p(*q) for p, q in func_stub]
    from pprint import pprint as pp
    level_strs = map(str, levels)
    variable_strs = ["dispersiveness", "closure", "frag", "asymmetry", "elongation2"]
    header_list = map('-'.join, list(itertools.product(variable_strs, level_strs)))
    with open(os.path.join(work_base_folder, "dispersiveness.csv"), "w") as dispersive_output:
        dispersive_output.write("time_string," + ",".join(header_list) + ",comment\n")
        for a, d in zip(asm_input, dispersiveness):
            dispersive_output.write(a + "," + "".join(d) + "\n")
        dispersive_output.close()


# Main
if __name__ == "__main__":
    start_mp()
