
import netCDF4 as nc4

import pre.wrf.helpers as pwh

import tests.test_config as tc



class TestWrfDomain:

    WRFOUT_FILES = None

    @classmethod
    def setup_class(cls):

        assert hasattr(tc, 'WRF_DATA_PATH'), 'missing a WRF run path'

        assert tc.WRF_DATA_PATH.exists()

        cls.WRFOUT_FILES = sorted( tc.WRF_DATA_PATH.glob('wrfout_*') )
       
        assert len(cls.WRFOUT_FILES) > 0


    def test_get_wrf_crs(self):
        path = type(self).WRFOUT_FILES[0]


        with nc4.Dataset(path) as ifile:
            crs = pwh.WrfDomain.get_wrf_crs( ifile )


    def test_create_from_path(self):
        path = type(self).WRFOUT_FILES[0]


        wrf_dom = pwh.WrfDomain.create_from_path( path )

