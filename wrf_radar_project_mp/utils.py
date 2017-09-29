# coding=utf-8

import os
import sys
import shutil
import pyproj
import datetime
import time
import numpy


def create_dirs(dirs, discard=False):
    '''helper function: create folder structure'''
    for p in dirs:
        if p.find("in_memory") != -1:
            continue
        if discard:
            print "Removing ", os.path.abspath(p)
            shutil.rmtree(p, ignore_errors=True)
        if not os.path.exists(p):
            os.makedirs(p)
    pass


def relocate(old_path, new_folder, new_ext=None):
    """relocate file at ```old_path``` to ```new_folder``` and change its extension to ```new_ext```
    
    Parameters 
    -----------------
    old_path: string
        old file path

    new_folder: string 
        the folder new file will be stored
        
    new_ext: string
        the extension of new file will be replaced by ````new_ext````
    """
    rootname, ext = os.path.splitext(os.path.basename(old_path))
    rootname = rootname.replace(".", "_")
    base = os.path.basename(old_path)
    if new_ext is None:
        return os.path.join(new_folder, rootname + ext)
    if new_ext is "":
        return os.path.join(new_folder, rootname)
    else:
        # Add a "." in case forgotten
        return os.path.join(new_folder, rootname + (new_ext if new_ext.startswith(".") else ".%s" % new_ext))


def list_folder_sorted_ext(folder=".", ext=None):
    return sorted(filter(lambda p: ext is None or p.endswith(ext), os.listdir(folder)))


def list_files_by_timestamp(basedir, timelist, dformat, file_ext=None, mask_config=None, allow_diff_sec=300):
    '''find a list of files closest to given timelist'''

    def __find_files_in_list_by_time(files, ref_time):
        r = time.mktime(ref_time.timetuple())
        t = [datetime.datetime.strptime(os.path.basename(os.path.splitext(f)[0]), dformat) for f in files]
        s = numpy.array([time.mktime(p.timetuple()) for p in t])
        d = numpy.abs(s - r)
        if numpy.min(d) > allow_diff_sec:
            return None, None
        i = numpy.argmin(d)
        mask = None
        if mask_config is not None:
            for m in mask_config:
                if m[0] <= t[i] < m[1]:
                    mask = m[2]
                    break
        return mask, files[i]

    files = list_folder_sorted_ext(basedir, file_ext)
    return zip(*[__find_files_in_list_by_time(files, t) for t in timelist])


# configs
case_year = "2003"
case_name = "Isabel"

temp_folder = os.environ["TEMP"]
ibtrac = os.path.join(sys.path[0], 'ibtracs_na_1995.csv')
cnt_folder = "cnt"
cnt_polygon_folder = "cnt_polygon"
stage1_folder = "basic_metric"
stage2_folder = "adv_metric"
projStr = "+proj=lcc +lat_1=20 +lat_2=60 +lat_0=40 +lon_0=-96 +x_0=0 +y_0=0 +ellps=GRS80 +datum=NAD83 +units=m +no_defs"
projFunc = pyproj.Proj(projStr)
spatialRef = '''PROJCS["North_America_Lambert_Conformal_Conic",GEOGCS["GCS_North_American_1983",DATUM["D_North_American_1983",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",0.0],PARAMETER["False_Northing",0.0],PARAMETER["Central_Meridian",-96.0],PARAMETER["Standard_Parallel_1",20.0],PARAMETER["Standard_Parallel_2",60.0],PARAMETER["Latitude_Of_Origin",40.0],UNIT["Meter",1.0],AUTHORITY["ESRI",102009]]'''
resolution = 4000

