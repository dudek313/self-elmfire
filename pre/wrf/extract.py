

import os
import glob
import numpy as np
import netCDF4 as nc4
import xarray as xr
import rioxarray
import wrf

import config as cfg

from pyproj import CRS
from pathlib import Path



class WrfToElmfire:

    def __init__(self, wrf_bpath: Path,
                 domains:list[str]=cfg.DOMAINS,
                 file_search_pattern:str=cfg.DOMAIN_FILE_SEARCH_PATTERN):
        self.wrf_bpath = wrf_bpath
        self.domains = domains
        self.file_search_pattern = domain_file_search_pattern

    def do(self):
        
        for dom in self.domains:
            paths = self._find_files( dom )
            self._read_files( paths )


    def _read_files(self, paths):
        paths = sorted(paths)

        ws_list, wd_list, t_list, rh_list = [], [], [], []

        for i, path in enumerate(paths):
            with nc4.Dataset(path) as ifile:
                if i == 0:
                    wrf_crs = self._read_wrf_crs(ifile)

                self._process_file(ifile,
                                ws_list, wd_list, t_list, rh_list)





    def _find_files(self, domain:str):
        """
        Finds hourly WRF files, extracts variables using wrf-python,
        and stacks them into multi-band GeoTIFFs for ELMFIRE.
        """
        
        nc_file_pattern = self.file_search_pattern.format(domain=domain)
       
        nc_files = self.wrf_bpath.glob(nc_file_pattern)
        nc_files = sorted( nc_files )
        

        if not nc_files:
            raise FileNotFoundError(f"No WRF files found matching pattern: {nc_file_pattern}")

        print(f"Found {len(nc_files)} hourly files to process...")


        return nc_files


    def _get_projection(self, ifile):
        # wrf.get_crs extracts the native projection object
        native_proj = wrf.get_crs(wspd_wdir)

        # Extract LCC parameters directly from the projection object attributes
        truelat1 = native_proj.truelat1
        truelat2 = native_proj.truelat2
        lat_0 = native_proj.moad_cen_lat
        lon_0 = native_proj.stand_lon

        # Explicitly force WRF's perfect sphere radius to map accurately to EPSG:9473
        wrf_crs = CRS.from_string(
            f"+proj=lcc "
            f"+lat_1={truelat1} "
            f"+lat_2={truelat2} "
            f"+lat_0={lat_0} "
            f"+lon_0={lon_0} "
            f"+a=6370000 +b=6370000 "
            f"+units=m +no_defs"
        )
        print(f"Extracted WRF LCC Parameters: lat_1={truelat1}, lat_2={truelat2}, lon_0={lon_0}")




def test():
    alg = WrfToElmfire(


if __name__ == '__main__':
    test()
