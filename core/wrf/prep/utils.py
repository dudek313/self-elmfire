

import numpy as np
import netCDF4 as nc4
import datetime as dt

WRF_TIME_FMT = "%Y-%m-%d_%H:%M:%S" 



def get_wrf_datetimes(ifile:nc4.Dataset) -> list[dt.datetime]:
    """Decoded ``Times`` variable.
    """
    
    raw = nc4.chartostring(ifile.variables["Times"][:])
    
    return [
            dt.datetime.strptime(str(s), WRF_TIME_FMT)
                for s in np.atleast_1d(raw)
        ]


