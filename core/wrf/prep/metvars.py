
import pyproj as prj
import netCDF4 as nc4
import core.wrf.fuel_moisture as fm

import settings as S

STATE_VARS = (
        "t2", "q2",
        "psfc",
        "u10e", "v10e",
        "rain_base",
        *S.TIME_LAGS_HOURS,
)

RAIN_VARS = (
        ("RAINC", "I_RAINC"),
        ("RAINNC", "I_RAINNC"),
        ("RAINSH", None)
)



class Helper:

    def __init__(self):
        pass


    def read(self, dset, index: int, time: datetime, north) -> dict:
        """Native state at one WRF output time."""
        #window = self.request.window or (slice(None), slice(None))

        def var(name):
            values = dset.variables[name][index]#[window]
            return np.asarray(values, dtype="float64")

        u10e, v10e = Wind.earth_relative(
                                var("U10"),
                                var("V10"),
                                north)
        
        return {
                "time": time,
                "t2"  : var("T2"),
                "q2"  : var("Q2"),
                "psfc": var("PSFC"),
                "u10e": u10e,
                "v10e": v10e,
                "rain_acc": self._total_rain(dset, var),
            }

    @staticmethod
    def _total_rain(dset:nc4.Dataset, var):
        """Accumulated rain RAINC + RAINNC (+ RAINSH), bucket aware (mm)."""
        bucket = float(dset.__dict__.get("BUCKET_MM", -1.0))
        
        total = 0.0
        for name, bucket_name in RAIN_VARS:
            if name not in dset.variables:
                continue

            total += var(name)

            if bucket_name and \
                  bucket_name in dset.variables and \
                  bucket > 0:
                total += bucket * var(bucket_name)

        return total



class Wind:
    """Wind rotations between grids and ELMFIRE's speed/direction."""

    @staticmethod
    def true_north_azimuth(crs, x, y, lon, lat):
        """Azimuth (rad, clockwise from the grid +y) of true north."""
        to_xy = prj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
        
        x2, y2 = to_xy.transform(
            lon, np.minimum(np.asarray(lat) + 0.001, 89.999)
        )

        return np.arctan2(np.asarray(x2) - x, np.asarray(y2) - y)


    @staticmethod
    def earth_relative(u_grid, v_grid, north_az):
        """Rotate grid-relative components to (east, north) components."""
        cos_t, sin_t = np.cos(north_az), np.sin(north_az)
        return (u_grid * cos_t - v_grid * sin_t,
                u_grid * sin_t + v_grid * cos_t)


    @staticmethod
    def speed_direction(u_e, v_e, north_az,
                        height_factor=DEFAULT_WIND_HEIGHT_FACTOR):
        """ELMFIRE ws (20-ft, mph) and wd (deg *from*, grid north).

        ``north_az``: grid azimuth (rad) of true north on the target grid.
        """
        speed = np.hypot(u_e, v_e) * MS_TO_MPH * height_factor
        toward_grid = np.arctan2(u_e, v_e) + north_az
        return speed, np.degrees(toward_grid + np.pi) % 360.0


