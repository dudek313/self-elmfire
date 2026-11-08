"""Near-surface physics: humidity, fuel-moisture equilibria and wind."""

from __future__ import annotations


import numpy as np

from dataclasses import dataclass



class Humidity:
    """Relative humidity and the dead-fuel equilibrium moisture contents."""

    @staticmethod
    def relative_humidity(t2_k, q2, psfc_pa):
        """RH (%) from T2 (K), mixing ratio Q2 (kg/kg) and PSFC (Pa).

        Saturation vapour pressure over water after Murphy & Koop (2005)
        eq. 10, as in WRF-SFIRE. Q2 is a mixing ratio, so
        e = q p / (0.622 + q) (WRF-SFIRE uses the specific-humidity form,
        which differs by < 1 %).
        """
        temp = np.asarray(t2_k, dtype="float64")
        mix = np.maximum(q2, 0.0)
        vap = mix * psfc_pa / (0.622 + mix)
        log_t = np.log(temp)
        sat = np.exp(
            54.842763 - 6763.22 / temp - 4.210 * log_t + 0.000367 * temp
            + np.tanh(0.0415 * (temp - 218.8))
            * (53.878 - 1331.22 / temp - 9.44523 * log_t + 0.014025 * temp)
        )
        return np.clip(100.0 * vap / sat, 0.0, 100.0)


    @staticmethod
    def equilibrium(t2_k, rh):
        """Drying and wetting equilibria (%), Van Wagner & Pickett / Viney.

        Returns ``(Ed, Ew)`` with Ed >= Ew, matching WRF-SFIRE.
        """
        hum = np.asarray(rh, dtype="float64")
        tail = (0.18 * (21.1 + 273.15 - np.asarray(t2_k))
                * (1.0 - np.exp(-0.115 * hum)))
        dry = 0.942 * hum ** 0.679 + 0.000499 * np.exp(0.1 * hum) + tail
        wet = 0.618 * hum ** 0.753 + 0.000454 * np.exp(0.1 * hum) + tail
        return (np.maximum(np.maximum(dry, wet), 0.0),
                np.maximum(np.minimum(dry, wet), 0.0))

    @classmethod
    def equilibrium_from_state(cls, t2_k, q2, psfc_pa):
        """``(Ed, Ew)`` directly from T2, Q2 and PSFC."""
        return cls.equilibrium(t2_k, cls.relative_humidity(t2_k, q2, psfc_pa))


@dataclass
class FuelMoistureModel:
    """Equilibrium time-lag dead fuel moisture model of WRF-SFIRE (%).

    Ported from ``phys/module_fr_fire_phys.F``: drying/adsorption towards
    the equilibria with lag ``tau``; during rain above the threshold,
    wetting towards saturation with lag ``wetting_lag_ratio * tau``.
    """

    rain_threshold_mm_h: float = 0.05   # rain this light counts as none
    saturation_rain_mm_h: float = 8.0   # stronger rain only lasts longer
    wetting_lag_ratio: float = 1.4      # wetting lags 1.4, 14, 140 h
    saturation_pct: float = 250.0

    def step(self, moisture, tau_h, dt_h, equilibrium, rain_mm_h):
        """Advance ``moisture`` by ``dt_h`` hours.

        ``equilibrium`` is ``(Ed, Ew)``; ``rain_mm_h`` the rain rate.
        """
        ed, ew = equilibrium
        moisture = np.asarray(moisture, dtype="float64")
        excess = np.asarray(rain_mm_h, dtype="float64")
        excess = excess - self.rain_threshold_mm_h
        raining = excess > 0
        rate_wet = (
            1.0 - np.exp(-np.maximum(excess, 0.0) / self.saturation_rain_mm_h)
        ) / (self.wetting_lag_ratio * tau_h)
        rate = np.where(raining, rate_wet, 1.0 / tau_h)
        target = np.where(raining, self.saturation_pct,
                          np.clip(moisture, ew, ed))
        return moisture + (target - moisture) * (1.0 - np.exp(-rate * dt_h))


