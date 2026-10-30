
import pdb
import netCDF4 as nc4
import datetime as dt
import common.geo_tools as gt

from pathlib import Path



def test_wrf_crs():
    date = dt.datetime.now() - dt.timedelta(hours=24)
    sdate = f'{date:%Y%m%d}_v54'

    bpath = Path('/mnt/aqf2-scratch2/opforecastv54') / \
        sdate / 'esme_local'/ 'forecast' / 'run'/ 'WRF' / 'run'


    assert bpath.exists()

    #pdb.set_trace()
    files = sorted(bpath.glob('wrfout_*'))
    assert len(files) > 0


    with nc4.Dataset(files[0]) as ifile:
        crs = gt.get_wrf_crs(ifile)


        print(crs)

def test_declination_tool_with_dem_aspect():
    path = Path('/mnt/aqf2-scratch1/df-test/efire/data/derived-inputs/dem') / \
                        'derived-30x30m-EPSG-9473--dems1sv1_0--aspect.tif'


test_wrf_crs()
