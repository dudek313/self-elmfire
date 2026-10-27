
import netCDF4 as nc4
import pyproj as prj





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

    def grid_north_angle(crs, lon, lat, eps=1e-5):
        """Clockwise angle (deg) from the CRS's grid north (+y) to 
        true north at (lon, lat).
        """
        t = Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        x0, y0 = t.transform(lon, lat)
        x1, y1 = t.transform(lon, lat + eps)

        return np.degrees(np.arctan2(x1 - x0, y1 - y0))



    def north_offset(crs_a, crs_b, lon, lat):
        """Clockwise rotation (deg) from A's grid north to B's grid north
        at (lon, lat).
        """
        return grid_north_angle(crs_a, lon, lat) - grid_north_angle(crs_b, lon, lat)



