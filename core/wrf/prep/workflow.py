

import os
import glob
import numpy as np
import pyproj as prj
import netCDF4 as nc4
import datetime as dt
import xarray as xr
import rioxarray as xrio

import config as cfg
import common.geo_tools as gt

import core.typedef as td
import core.wrf.prep.data_loader as wdl

from pathlib import Path


class Workflow:

    def __init__(self, per_domain_paths: td.PerDomainPathList,
                 start_utc_tstamp:dt.datetime,
                 end_utc_tstamp:dt.datetime=None,
                 spinup_hours:int=72):
        self.per_domain_paths = per_domain_paths
        self.start_utc_tstamp = start_utc_tstamp
        self.end_utc_tstamp   = end_utc_tstamp
        self.spinup_hours     = spinup_hours




    def do(self):

        for dom, dom_paths in self.per_domain_paths.items():
            self._process_domain(
                        domain_id=dom,
                        paths=dom_paths,
                    )


    def _process_domain(self, domain_id:str, paths: td.WrfFileNameToPath):
        
        ldr = wdl.TimestepIterator(
                            domain_paths=paths,
                            start_utc_tstamp=self.start_utc_tstamp,
                            end_utc_tstamp=self.end_utc_tstamp,
                            spinup_hours=self.spinup_hours)


        for rec in ldr:

            #self._process_accummulate_variables(rec)

            if not rec.is_spinup:
                print(f"{domain_id} - {rec.total_rec_count}: {rec.ts} is not spinup: ")
                #self._write_variables_to_file(rec)
            else:
                print(f"{domain_id} - {rec.total_rec_count}: {rec.ts} is spinup: ")




def test():
    BPATHS = [
            Path('/mnt/aqf2-scratch2/opforecastv54/20261106_v54/esme_local') \
                    / 'forecast' / 'run' / 'WRF' / 'run',

            Path('/mnt/aqf2-scratch2/opforecastv54/20261107_v54/esme_local') \
                    / 'forecast' / 'run' / 'WRF' / 'run',
        ]

    start_utc_tstamp = dt.datetime(year=2026, month=11, day=7, hour=10)


    wseq = wdl.WrfRunsSequencer(wrf_bpaths=BPATHS)
    paths: PerDomainPathList = wseq.find_file_priority_sequence()


    flow = Workflow(
                paths,
                start_utc_tstamp=start_utc_tstamp,
                spinup_hours=10
            )

    flow.do()




if __name__ == '__main__':
    test()
