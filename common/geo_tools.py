
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
