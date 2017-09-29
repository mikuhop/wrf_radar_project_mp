import sys
import os
import datetime

import pandas as pd

import arcpy

import utils
import mp_start

arcpy.CheckOutExtension("spatial")
arcpy.env.overwriteOutput = True
arcpy.env.workspace = "in_memory"

radar_base_folder = r'E:\radar_isabel'

wrf_base_folder = r'C:\Users\sugar\Desktop\wrf3.6.1'
wrf_schemes = [  # Biased cases
    'ARWH_KainFritschCu_Morrison', #0
    'ARWH_KainFritschCu_WSM6',
    'ARWH_TiedtkeCu_Morrison',
    'ARWH_TiedtkeCu_WSM6',
    # Unbiased cases
    'ARWH_KainFritschCu_Morrison', #4
    'ARWH_KainFritschCu_WDM6',
    'ARWH_KainFritschCu_WSM6',
    'ARWH_TiedtkeCu_Morrison',
    'ARWH_TiedtkeCu_WDM6',
    'ARWH_TiedtkeCu_WSM6', #9
    'wrf_gary'
]
wrf_postfix = 'reflec_netcdf'

# masks = [(datetime.datetime(2003, 9, 18, 0, 0, 0), datetime.datetime(2003, 9, 18, 23, 59, 59),
#          r'E:\wrf3.6.1\Mask\mask1.shp'),
#         (datetime.datetime(2003, 9, 19, 0, 0, 0), datetime.datetime(2003, 9, 19, 23, 59, 59),
#          r'E:\wrf3.6.1\Mask\mask2.shp')]

radar_levels = range(20, 45, 5)
wrf_bias = [
    [23, 28, 33, 38, 44],  # KF/M
    [14, 20, 27, 34, 41],  # KF/WSM6
    [20, 25, 29, 34, 40],  # TK/M
    [17, 23, 28, 33, 40],  # TK/WSM6
    None,
    None,
    None,
    None,
    None,
    None,
    None
]

# Radar resolution = 30min, WRF resolution = 30min
analytical_time = map(pd.Timestamp.to_datetime,
                      pd.date_range('2003-09-18 00:00:00', '2003-09-18 01:00:00', freq="30min"))
if __debug__:
    print(analytical_time)


def run_radar(skip_list, DISCARD_EXISTED):
    utils.working_mode = "radar"
    _, file_list = utils.list_files_by_timestamp(radar_base_folder,
                                                 analytical_time,
                                                 allow_diff_sec=600,
                                                 file_ext="img",
                                                 dformat="%Y%m%d-%H%M%S")
    mp_start.start_mp(work_base_folder=radar_base_folder,
                      file_list=file_list,
                      levels=radar_levels,
                      working_mode="radar",
                      stage2_datetime_format="%Y%m%d_%H%M%S",
                      skip_list=skip_list,
                      discard=DISCARD_EXISTED)


def run_wrf(case, skip_list, DISCARD_EXISTED):
    #global masks
    utils.working_mode = "wrf"
    if wrf_bias[case]:
        wrf_levels = wrf_bias[case]
    else:
        wrf_levels = radar_levels
    # mask_files, wrf_files = utils.list_files_by_timestamp(os.path.join(wrf_base_folder, wrf_schemes[case], wrf_postfix),
    #                                                       analytical_time,
    #                                                       allow_diff_sec=300,
    #                                                       file_ext="nc",
    #                                                       dformat="refl_3.5km_%Y-%m-%d_%H_%M",
    #                                                       mask_config=None)
    # mask_files = filter(None, mask_files)
    # wrf_files = filter(None, wrf_files)

    mp_start.start_mp(work_base_folder=os.path.join(wrf_base_folder, wrf_schemes[case], 'reflec_netcdf'),
                      file_list=None,
                      levels=wrf_levels,
                      masks=None,
                      working_mode="wrf",
                      stage2_datetime_format="refl_3km_%Y_%m_%d_%H_%M",
                      skip_list=skip_list,
                      discard=DISCARD_EXISTED)


def main(argv):
    DISCARD_EXISTED = True
    skip_dict = {
        "contour": 1,
        "smooth": 1,
        "basic": 1,
    }
    skip_list = [k for k,v in skip_dict.iteritems() if v]
    # If we do the skip, we cannot discard previous results
    if skip_list:
        DISCARD_EXISTED = False
    print skip_list, DISCARD_EXISTED
    case = int(argv[1])
    if case < 0:
        run_radar(skip_list, DISCARD_EXISTED)
    else:
        run_wrf(case, skip_list, DISCARD_EXISTED)


if __name__ == "__main__":
    main(sys.argv)
