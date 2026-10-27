
import numpy as np
import netCDF4 as nc4
import pyproj as prj
import rasterio as rio




def get_wrf_crs(ncfile_handle:nc4.Dataset):
    h = ncfile_handle

    crs = None
    if h.MAP_PROJ == 1: # Lambert Conformal

            crs = prj.CRS.from_proj4(
                    f"+proj=lcc +lat_1={h.TRUELAT1} +lat_2={h.TRUELAT2} "
                    f"+lat_0={h.MOAD_CEN_LAT} +lon_0={h.STAND_LON} "
                     "+x_0=0 +y_0=0 +a=6370000 +b=6370000 +units=m +no_defs"
                )
    else:
        raise NotImplementedError(
            'currently only Lambert Conformal projection is supported.')

    return crs




class DeclinationTool:
    """For directional data, such as wind direction and DEM aspect,
    this class checks their declination.
    """

    def __init__(self, elmfire_domain_raster_path:Path=None):
        """

        This tool will check for declination bias in directional datasets such
        as wind direction and Digital Elevation directional aspect.

        """
        self.elmfire_domain_raster_path = elmfire_domain_raster_path

        self.elmfire_domain_crs = None
        self.elmfire_domain_raster = None


    def _context_elmfire_domain_load(self):
        return rio.open(self.elmfire_domain_raster_path)

            

    def is_same_grid_declination(self,
                                 raster:rio.io.DatasetReader,
                                 tolerance:float=0.1):

        decl = self.get_declination(raster)

        if np.abs(decl) < tolerance:
            return True

        return False


    def get_declination(self, raster:rio.io.DatasetReader):

        with self._context_elmfire_domain_load() as dom_raster:

            dom_crs = prj.CRS.from_user_input(dom_raster.crs)
            crs = prj.CRS.from_user_input(raster.crs)

            if crs == dom_crs:
                return 0.0

            #
            # find the lat/lon of the ELMFIRE domain centre
            #
            b = dom_raster
            cx = (b.bounds.left + b.bounds.right) / 2,
            cy = (b.bounds.bottom + b.bounds.top) / 2

            lon, lat = prj.Transformer.from_crs(dom_crs, "EPSG:4326",
                                            always_xy=True).transform(cx, cy)

            #
            # calculate north clockwise offset
            #
            decl  = type(self).north_offset(crs,  dom_crs, lon, lat)


            return decl



    @classmethod
    def grid_north_angle(cls, crs, lon, lat, eps=1e-5):
        """Clockwise angle (deg) from the CRS's grid north (+y) to 
        true north at (lon, lat).
        """
        t = prj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        x0, y0 = t.transform(lon, lat)
        x1, y1 = t.transform(lon, lat + eps)

        return np.degrees(np.arctan2(x1 - x0, y1 - y0))


    @classmethod
    def north_offset(cls, crs_a, crs_b, lon, lat):
        """Clockwise rotation (deg) from A's grid north to B's grid north
        at (lon, lat).
        """
        return cls.grid_north_angle(crs_a, lon, lat) - grid_north_angle(crs_b, lon, lat)




