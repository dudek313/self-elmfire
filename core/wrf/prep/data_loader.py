



"""
Loads data from a set of WRF runs and preprocesses them into ELMFIRE format.
"""


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

@dataclass
class IterRecord:
    ts: dt.datetime
    ts_idx: int
    ifile: nc4.Dataset
    is_spinup: bool

    @classmethod
    def create(cls, spinup_start, simul_start, 
               ts, ts_idx,
               ifile,
               total_ts_count):

        assert ts >= spinup_start
        
        is_spinup = ts < simul_start

        return cls(
                ts=ts,
                ts_idx=ts_idx,
                ifile=ifile,
                is_spinup=is_spinup
                total_count=total_ts_count
            )



class WrfRunsSequencer:
    """
    This implementation is designed for the DCCEEW/CAS/AR daily forecasts,
    where each forecast covers 4 days, and one day ahead of the previous day.
    For spinup of 100h mousture variabes, we need to use previous forecasts to
    seed the integration of moisture.

    Here we provide multiple paths, with the last being the most recent
    (important).
    """

    def __init__(self,
                 wrf_bpaths: list[Path],
                 domain_ids:list[str]=cfg.DOMAINS,
                 file_search_pattern:str=cfg.DOMAIN_FILE_SEARCH_PATTERN):
        """
        wrf_bpaths need to be sorted from lowest to highest priority.
        """

        self.wrf_bpaths = wrf_bpaths
        self.domain_ids = domain_ids
        self.file_search_pattern = file_search_pattern


    def find_file_priority_sequence(self):
        """
        Read multiple base paths for sequenced wrf runs from lowest (oldest) to
        newest.
        """
        all_paths = {}

        for did in self.domain_ids:
            dom_paths = {}

            search_pattern = self.file_search_pattern.format(domain=did)

            #lowest priority first, highest priority overtaking if found
            for bpath in self.wrf_bpaths:
                paths = bpath.glob( search_pattern )

                for path in paths:
                    fname = path.name
                    dom_paths[fname] = path

            all_paths[did] = dom_paths

        return all_paths



class TimestepIterator:

    def __init__(self,
                 domain_paths: list[Path],
                 start_utc_tstamp:dt.datetime,
                 end_utc_date:dt.datetime=None,
                 spinup_hours:int=72):
        

        self.domain_paths = domain_paths
        self.start_utc_tstamp = start_utc_tstamp
        self.end_utc_date = end_utc_date
        self.spinup_hours = spinup_hours

        self.spinup_start = self.start_utc_tstamp - \
                                    dt.timedelta(hours=spinup_hours)


    def __iter__(self):
        """
        We assume that lexicographical sort of the files results in time
        sort.
        """
        paths = sorted( self.domain_paths )

        total_ts_count = 0
        for i, path in enumerate(paths):
            with nc4.Dataset(path) as ifile:
                tstamps = self._read_time_stamps(ifile)

                if i == 0:
                    assert ts <= self.spinup_hours

                for j, ts in enumerate(tstamps):
                    if self.spinup_start > ts:
                        continue

                    total_ts_count += 1

                    yield IterRecord(
                            spinup_start=self.spinup_start,
                            simul_start=self.start_utc_tstamp,
                            ts=ts,
                            ts_idx=j,
                            ifile=ifile,
                            total_ts_count=total_ts_count)
       

                    
