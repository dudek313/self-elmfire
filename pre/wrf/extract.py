

import os
import glob
import numpy as np
import pyproj as prj
import netCDF4 as nc4
import xarray as xr
import rioxarray as xrio

import config as cfg
import common.geo_tools as gt

from pathlib import Path



class WrfToElmfire:
    """Transform WRF outputs to GeoTiff as required by ELMFIRE.
    Each GeoTiff file collates the WRF outputs into a single file where
    timesteps are represented as Tiff Bands.

    The 
    """

    def __init__(self,
                 wrf_bpath: Path,
                 elmfire_crs: prj.CRS, 
                 domains:list[str]=cfg.DOMAINS,
                 file_search_pattern:str=cfg.DOMAIN_FILE_SEARCH_PATTERN):

        self.wrf_bpath = wrf_bpath
        self.elmfire_crs = elmfire_crs
        self.domains = domains
        self.file_search_pattern = file_search_pattern

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
                    wrf_crs = gt.get_wrf_crs(ifile)

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



def test():
    BPATH = Path('/mnt/aqf2-scratch2/opforecastv54/20261025_v54/esme_local') \
                    / 'forecast' / 'run' / 'WRF' / 'run'

    alg = WrfToElmfire(
                wrf_bpath=BPATH,
            )

    alg.do()

if __name__ == '__main__':
    test()
