
import enum
import numpy as np
import pyproj as prj
import netCDF4 as nc4
import datetime as dt

from typing import Self
from pathlib import Path
from dataclasses import dataclass, field


class ProjID(enum.IntEnum):
    LAMBERT = 1
    POLAR_STEREOGRAPHIC = 2
    MERCATOR = 3

WRF_EARTH_RADIUS = 6370000.0
WRF_SPHERE = f'+a={WRF_EARTH_RADIUS} +b={WRF_EARTH_RADIUS} +units=m +no_defs'


@dataclass
class WrfDomain:
    """Projection and geometry of one WRF domain, with the files/times it covers.
    """

    grid_id: int
    crs: prj.CRS
    x0: float              # projected x of mass point (i=0)
    y0: float              # projected y of mass point (j=0)
    dx: float
    dy: float
    nx: int
    ny: int
    records: list = field(default_factory=list)   # (datetime, path, time_index), sorted

    @property
    def times(self) -> list[dt.datetime]:
        return [r[0] for r in self.records]

    def fractional_index(self, x_target, y_target, target_crs):
        """WRF (i, j) fractional mass-grid indices of points in ``target_crs``.
        """
        t = prj.Transformer.from_crs(target_crs, self.crs, always_xy=True)
        
        x, y = t.transform(x_target, y_target)
        
        return (np.asarray(x) - self.x0) / self.dx, (np.asarray(y) - self.y0) / self.dy

    #def contains(self, grid: Grid, margin_cells: float = 2.0) -> bool:
    #    xs = np.linspace(grid.xmin, grid.xmax, 21)
    #    ys = np.linspace(grid.ymin, grid.ymax, 21)
    #    X, Y = np.meshgrid(xs, ys)
    #    
    #    fi, fj = self.fractional_index(X.ravel(), Y.ravel(), grid.crs)
    #    
    #    return bool(fi.min() >= margin_cells and fj.min() >= margin_cells
    #                and fi.max() <= self.nx - 1 - margin_cells and fj.max() <= self.ny - 1 - margin_cells)


    @staticmethod
    def get_wrf_crs(ifile:nc4.Dataset) -> prj.CRS:
        """pyproj CRS for a WRF domain from its global attributes
           (spherical earth, R=6370 km).

           Supported projections:
                1 Lambert,
                2 polar stereographic,
                3 Mercator 
        """
        proj = int(ifile.MAP_PROJ)
        lon0 = float(ifile.STAND_LON)
        t1   = float(ifile.TRUELAT1)
        t2   = float(ifile.TRUELAT2)
        sphere = WRF_SPHERE

        match proj:
            case ProjID.LAMBERT:
                lat0 = t1

                if hasattr(ifile, 'MOAD_CEN_LAT'):
                    lat0 = float(ifile.MOAD_CEN_LAT)
                
                p4str = f'+proj=lcc +lat_1={t1} +lat_2={t2} +lat_0={lat0} ' + \
                        f'+lon_0={lon0} {sphere}'
                
                return prj.CRS.from_proj4( p4str )
            
            case ProjID.POLAR_STEREOGRAPHIC:
                pole = 90 if t1 >= 0 else -90
               
                p4str = f'+proj=stere +lat_0={pole} +lat_ts={t1} ' + \
                        f'+lon_0={lon0} {sphere}'

                return prj.CRS.from_proj4( p4str )
            
            case ProjID.MERCATOR:
                p4str = f'+proj=merc +lat_ts={t1} +lon_0={lon0} {sphere}' 
                
                return prj.CRS.from_proj4( p4str )
        
        raise ValueError(f"WRF MAP_PROJ={proj} is not supported (1 Lambert, 2 polar stereographic, 3 Mercator)")


    @classmethod
    def create_from_path(cls, path: str) -> Self:

        with nc4.Dataset(path) as ds:
            crs = cls.get_wrf_crs(ds)
            lat = np.asarray(ds.variables["XLAT"][:], dtype="float64")
            lon = np.asarray(ds.variables["XLONG"][:], dtype="float64")
        
            dx, dy = float(ds.DX), float(ds.DY)

            gid = 1
            if hasattr(ds, 'GRID_ID'):
                gid = int(ds.GRID_ID)

        if lon.ndim == 3:
            lon = lon[0]
            lat = lat[0]

        ny, nx = lat.shape
        
        t = prj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        x,y = t.transform(lon, lat)
        
        jj, ii = np.mgrid[0:ny, 0:nx]
        # Least-squares origin from every mass point (XLAT/XLONG are only float32).
        x0 = float(np.mean(x - ii * dx))
        y0 = float(np.mean(y - jj * dy))
        
        err = max(np.abs(x - (x0 + ii * dx)).max(), np.abs(y - (y0 + jj * dy)).max())
        
        if err > 0.1 * min(dx, dy):
            raise ValueError(f"{path}: reconstructed WRF projection does not match XLAT/XLONG "
                             f"(max error {err:.0f} m); check MAP_PROJ/TRUELAT/STAND_LON")
        
        return WrfDomain(gid, crs, x0, y0, dx, dy, nx, ny)



