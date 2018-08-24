# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

"""
Module exports :class:`MorikawaFujiwara2013Asc`
"""

import numpy as np

from openquake.hazardlib import const
from openquake.hazardlib.imt import PGV, PGA, SA, IJMA
from openquake.hazardlib.gsim.base import GMPE, CoeffsTable

from openquake.hazardlib.geo.surface import SimpleFaultSurface
from openquake.hazardlib.geo import Line, Point
from openquake.hazardlib.geo.mesh import Mesh

from openquake.hazardlib.gsim.si_midorikawa_1999 import \
    _get_min_distance_to_volcanic_front


VOLCANIC_FRONT_PACIFIC_LATS = np.array([24., 31., 34.1, 36.1, 37.2, 39.3, 42.6,
                                        43.6, 44.3, 45.9])
VOLCANIC_FRONT_PACIFIC_LONS = np.array([141.6, 140.2, 139.7, 138.7, 140.1,
                                        141., 141.2, 145., 146.9, 150.])

VOLCANIC_FRONT_PHILIPPINES_LATS = np.array([24.5, 24.5, 27.9, 29.5, 31.5,
                                            33.4, 34.9, 35.3, 35.3, 36.2])
VOLCANIC_FRONT_PHILIPPINES_LATS = np.array([122., 124., 128.3, 129.7, 130.8,
                                            131.6, 132., 133.7, 134.9, 136.9])


def _get_volcanic_front_surface(lons, lats):
    usd = 0.
    lsd = 6.
    dip = 90.
    msp = 5.
    trc = Line([Point(lo, la) for lo, la in zip(lons, lats)])
    srfc = SimpleFaultSurface.from_fault_data(trc, usd, lsd, dip, msp)
    rjb = srfc.get_joyner_boore_distance(Mesh(lons, lats, None))
    rx = srfc.get_rx_distance(Mesh(lons, lats, None))
    rjb *= np.sign(rx)
    return rjb


class MorikawaFujiwara2013Asc(GMPE):
    """  """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.ACTIVE_SHALLOW_CRUST

    #: Supported intensity measure type is PGV
    DEFINED_FOR_INTENSITY_MEASURE_TYPES = set([
        PGV, PGA, SA, IJMA
    ])

    #: Supported intensity measure component is greater of
    #: of two horizontal components :
    #: attr:`~openquake.hazardlib.const.IMC.GREATER_OF_TWO_HORIZONTAL`
    DEFINED_FOR_INTENSITY_MEASURE_COMPONENT = \
        const.IMC.AVERAGE_HORIZONTAL

    #: Supported standard deviation type is total
    DEFINED_FOR_STANDARD_DEVIATION_TYPES = set([
        const.StdDev.TOTAL
    ])

    #: No sites parameters are required
    REQUIRES_SITES_PARAMETERS = set(['vs30', 'z1pt4'])

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag'))

    #: Required distance measure is Rrup
    REQUIRES_DISTANCES = set(('rrup', ))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        C = self.COEFF[imt]
        # computing the mean
        mean = C['c1'] + self._get_mean(sites, rup, dists, C)
        stds = self._get_std(sites)
        return mean, stds

    def _get_std(self, dists):
        # std is constant for all the intensity measures - Hao (pers. comm.)
        return np.ones_like(dists.rrup) * 0.46

    def _get_mean(self, sites, rup, dists, C):
        mwprime = min(rup.mag, C['mw0'])
        mean = (C['a'] * (mwprime - C['mw1'])**2 +
                C['b1'] * dists.rrup +
                np.log(dists.rrup + C['d'] * 10**(C['e'] * mwprime)) +
                C['pd'] * np.log10(np.max(sites.z1pt4, C['dlmin']) / C['d0']) +
                C['ps]'] * np.log10(np.min(sites.vs30, C['vsmax']) / C['v0'])
                )
        return mean


    COEFFS = CoeffsTable(sa_damping=5, table="""\
  IMT mw0 mw1  a      b1       b2        b3        c1     c2     c3     d        e   pd       dlmin   d0  ps        vsmax  v0  gne         gsw        ph
 IJMA 8.2 16 -0.0321 -0.003736 -0.003320 -0.004195 6.9301 6.9042 7.2975 0.005078 0.5  0.032214 320.0  300 -0.756496 1200.0 350 6.0657E-05  5.9144E-05 -0.2284
  PGA 8.2 16 -0.0321 -0.005315 -0.005042 -0.005605 7.0830 7.1181 7.5035 0.011641 0.5 -0.055358  15.0  300 -0.523212 1950.0 350 7.6017E-05  6.3273E-05 -0.2426
  PGV 8.2 16 -0.0325 -0.002654 -0.002408 -0.003451 5.6952 5.6026 6.0030 0.002266 0.5  0.129142 105.0  300 -0.693402  850.0 350 4.6928E-05  3.7205E-05 -0.2643
 0.05 8.2 16 -0.0321 -0.005912 -0.005674 -0.006231 7.2151 7.2759 7.6801 0.012812 0.5 -0.071415  15.0  300 -0.368827 2000.0 350 8.7676E-05  6.6421E-05 -0.2414
 0.06 8.2 16 -0.0321 -0.006097 -0.005864 -0.006405 7.2852 7.3523 7.7504 0.014508 0.5 -0.081796  15.0  300 -0.309232 2000.0 350 8.6686E-05  6.6288E-05 -0.2427
 0.07 8.2 16 -0.0321 -0.006142 -0.005967 -0.006507 7.3397 7.4152 7.8127 0.015574 0.5 -0.089891  15.0  300 -0.247786 2000.0 350 8.5849E-05  6.6176E-05 -0.2439
 0.08 8.2 16 -0.0323 -0.006104 -0.006033 -0.006594 7.4122 7.4929 7.8938 0.016465 0.5 -0.093581  15.0  300 -0.234067 2000.0 350 8.5124E-05  6.6078E-05 -0.2451
 0.09 8.2 16 -0.0325 -0.006112 -0.006079 -0.006689 7.4817 7.5649 7.9649 0.017390 0.5 -0.089604  15.0  300 -0.252853 2000.0 350 8.4485E-05  6.5992E-05 -0.2461
 0.10 8.2 16 -0.0327 -0.006116 -0.006061 -0.006686 7.5396 7.6214 8.0219 0.018438 0.5 -0.084855  15.0  300 -0.284416 2000.0 350 8.3913E-05  6.5915E-05 -0.2470
 0.11 8.2 16 -0.0324 -0.005998 -0.005971 -0.006576 7.5072 7.5947 7.9960 0.017396 0.5 -0.076412  15.0  300 -0.305700 2000.0 350 8.3396E-05  6.5846E-05 -0.2479
 0.12 8.2 16 -0.0322 -0.005896 -0.005878 -0.006448 7.4920 7.5837 7.9782 0.016457 0.5 -0.076948  15.0  300 -0.351975 2000.0 350 8.2923E-05  6.5783E-05 -0.2486
 0.13 8.2 16 -0.0321 -0.005786 -0.005757 -0.006331 7.4788 7.5645 7.9644 0.015607 0.5 -0.072886  15.0  300 -0.395130 2000.0 350 8.2489E-05  6.5724E-05 -0.2494
 0.15 8.2 16 -0.0321 -0.005564 -0.005579 -0.006078 7.4630 7.5471 7.9360 0.014118 0.5 -0.061401  15.0  300 -0.461774 2000.0 350 8.1712E-05  6.5620E-05 -0.2506
 0.17 8.2 16 -0.0321 -0.005398 -0.005382 -0.005813 7.4557 7.5245 7.9097 0.012855 0.5 -0.051288  15.0  300 -0.536789 2000.0 350 8.1032E-05  6.5529E-05 -0.2516
 0.20 8.2 16 -0.0321 -0.005151 -0.005027 -0.005476 7.4307 7.4788 7.8719 0.011273 0.5 -0.043392  15.0  300 -0.633661 2000.0 350 8.0150E-05  6.5410E-05 -0.2528
 0.22 8.2 16 -0.0322 -0.005000 -0.004827 -0.005204 7.4139 7.4461 7.8311 0.010380 0.5 -0.035431  15.0  300 -0.665914 2000.0 350 7.9633E-05  6.5341E-05 -0.2535
 0.25 8.2 16 -0.0321 -0.004836 -0.004519 -0.004907 7.3736 7.3728 7.7521 0.009225 0.5 -0.032667  15.0  300 -0.719524 2000.0 350 7.8939E-05  6.5247E-05 -0.2543
 0.30 8.2 16 -0.0321 -0.004543 -0.004095 -0.004621 7.2924 7.2797 7.6656 0.007670 0.5 -0.019984  15.0  300 -0.793002 2000.0 350 7.7949E-05  6.5114E-05 -0.2553
 0.35 8.2 16 -0.0321 -0.004379 -0.003717 -0.004305 7.2417 7.1832 7.5796 0.006448 0.5 -0.010959  15.0  300 -0.845946 2000.0 350 7.7112E-05  6.5002E-05 -0.2559
 0.40 8.2 16 -0.0321 -0.004135 -0.003342 -0.003989 7.1785 7.0883 7.4889 0.005464 0.5  0.003891  15.0  300 -0.875246 2000.0 350 7.6387E-05  6.4905E-05 -0.2562
 0.45 8.2 16 -0.0321 -0.003973 -0.003063 -0.003934 7.1202 7.0100 7.4287 0.004657 0.5  0.017120  15.0  300 -0.892051 1973.0 350 7.3411E-05  6.4819E-05 -0.2564
 0.50 8.2 16 -0.0321 -0.003767 -0.002832 -0.003783 7.0604 6.9439 7.3615 0.003986 0.5  0.030246  15.0  300 -0.891130 1900.0 350 7.0750E-05  6.4742E-05 -0.2564
 0.60 8.2 16 -0.0321 -0.003389 -0.002450 -0.003351 6.9357 6.8166 7.2161 0.002946 0.5  0.057955  15.0  300 -0.869468 1779.9 350 6.6143E-05  6.4609E-05 -0.2561
 0.70 8.2 16 -0.0321 -0.002981 -0.002059 -0.002988 6.8272 6.6957 7.0854 0.002193 0.5  0.071145  15.0  300 -0.873924 1684.3 350 6.2249E-05  5.8715E-05 -0.2555
 0.80 8.2 16 -0.0321 -0.002640 -0.001692 -0.002587 6.7325 6.5864 6.9659 0.001641 0.5  0.089675  15.0  300 -0.846494 1605.7 350 5.8875E-05  5.3609E-05 -0.2547
 0.90 8.2 16 -0.0325 -0.002341 -0.001445 -0.002421 6.6845 6.5349 6.9211 0.001234 0.5  0.109109  15.0  300 -0.814706 1539.4 350 5.5900E-05  4.9105E-05 -0.2538
 1.00 8.2 16 -0.0327 -0.002138 -0.001322 -0.002331 6.6284 6.4748 6.8605 0.000936 0.5  0.128832  15.0  300 -0.778652 1482.4 350 5.3238E-05  4.5076E-05 -0.2527
 1.10 8.2 16 -0.0331 -0.001912 -0.001140 -0.002194 6.5971 6.4383 6.8304 0.000723 0.5  0.146198  15.3  300 -0.732989 1432.7 350 5.0830E-05  4.1432E-05 -0.2516
 1.20 8.2 16 -0.0337 -0.001790 -0.001053 -0.002213 6.5912 6.4200 6.8224 0.000576 0.5  0.161540  17.1  300 -0.703167 1388.7 350 4.8631E-05  3.8105E-05 -0.2505
 1.30 8.2 16 -0.0339 -0.001671 -0.000979 -0.002159 6.5588 6.3848 6.7827 0.000482 0.5  0.171349  19.0  300 -0.686586 1349.5 350 4.6609E-05  3.5044E-05 -0.2493
 1.50 8.2 16 -0.0347 -0.001516 -0.000811 -0.002020 6.5419 6.3510 6.7540 0.000417 0.5  0.195287  23.0  300 -0.650103 1282.1 350 4.2994E-05  2.9572E-05 -0.2469
 1.70 8.2 16 -0.0352 -0.001526 -0.000714 -0.001909 6.5209 6.3011 6.7004 0.000471 0.5  0.220718  27.2  300 -0.602410 1225.9 350 3.9832E-05  2.4787E-05 -0.2444
 2.00 8.2 16 -0.0359 -0.001604 -0.000673 -0.001576 6.4982 6.2617 6.6087 0.000703 0.5  0.253945  33.7  300 -0.543585 1156.6 350 3.5726E-05  1.8572E-05 -0.2407
 2.20 8.2 16 -0.0365 -0.001516 -0.000610 -0.001349 6.4920 6.2463 6.5766 0.000702 0.5  0.270206  38.3  300 -0.505691 1117.8 350 3.3318E-05  1.4928E-05 -0.2382
 2.50 8.2 16 -0.0375 -0.001457 -0.000586 -0.001266 6.4964 6.2485 6.5667 0.000826 0.5  0.291435  45.4  300 -0.458523 1067.8 350 3.0088E-05  1.0040E-05 -0.2346
 3.00 8.2 16 -0.0382 -0.001345 -0.000505 -0.001105 6.4414 6.1858 6.4858 0.001202 0.5  0.323118  57.8  300 -0.413921 1000.3 350 2.5482E-05  3.0684E-06 -0.2288
 3.50 8.2 16 -0.0384 -0.001270 -0.000512 -0.001000 6.3464 6.0849 6.3681 0.001647 0.5  0.355950  70.9  300 -0.375806  946.6 350 2.1587E-05 -2.8259E-06 -0.2232
 4.00 8.2 16 -0.0385 -0.001075 -0.000610 -0.001005 6.2459 6.0035 6.2727 0.002087 0.5  0.380773  84.7  300 -0.348309  902.4 350 1.8214E-05 -7.9318E-06 -0.2178
 4.50 8.2 16 -0.0389 -0.000904 -0.000605 -0.001061 6.1868 5.9423 6.2145 0.002489 0.5  0.405714  99.0  300 -0.309662  865.1 350 1.5238E-05 -1.2435E-05 -0.2126
 5.00 8.2 16 -0.0393 -0.000739 -0.000564 -0.001155 6.1466 5.8960 6.1817 0.002841 0.5  0.419676 113.8  300 -0.294664  833.1 350 1.5238E-05 -1.2435E-05 -0.2077
 5.50 8.2 16 -0.0398 -0.000570 -0.000626 -0.001254 6.1084 5.8725 6.1566 0.003139 0.5  0.434776 129.2  300 -0.289487  805.2 350 1.5238E-05 -1.2435E-05 -0.2029
 6.00 8.2 16 -0.0402 -0.000456 -0.000702 -0.001317 6.0920 5.8536 6.1257 0.003384 0.5  0.453344 145.0  300 -0.290399  780.5 350 1.5238E-05 -1.2435E-05 -0.1983
 6.50 8.2 16 -0.0405 -0.000308 -0.000785 -0.001361 6.0636 5.8218 6.0778 0.003580 0.5  0.455404 155.0  300 -0.281808  758.4 350 1.5238E-05 -1.2435E-05 -0.1939
 7.00 8.2 16 -0.0410 -0.000195 -0.000856 -0.001392 6.0586 5.8197 6.0652 0.003728 0.5  0.440951 155.0  300 -0.283250  738.5 350 1.5238E-05 -1.2435E-05 -0.1896
 7.50 8.2 16 -0.0412 -0.000109 -0.000880 -0.001413 6.0367 5.7971 6.0388 0.003833 0.5  0.427237 155.0  300 -0.275643  720.5 350 1.5238E-05 -1.2435E-05 -0.1855
 8.00 8.2 16 -0.0417 -0.000100 -0.000908 -0.001466 6.0378 5.7885 6.0381 0.003898 0.5  0.410255 155.0  300 -0.277723  704.1 350 1.5238E-05 -1.2435E-05 -0.1814
 8.50 8.2 16 -0.0419 -0.000100 -0.000940 -0.001496 6.0238 5.7674 6.0180 0.003927 0.5  0.393707 155.0  300 -0.278975  688.9 350 1.5238E-05 -1.2435E-05 -0.1775
 9.00 8.2 16 -0.0420 -0.000100 -0.001012 -0.001488 5.9972 5.7463 5.9881 0.003924 0.5  0.378643 155.0  300 -0.284384  675.0 350 1.5238E-05 -1.2435E-05 -0.1737
 9.50 8.2 16 -0.0423 -0.000100 -0.001098 -0.001485 5.9880 5.7507 5.9807 0.003890 0.5  0.363717 155.0  300 -0.290498  662.0 350 1.5238E-05 -1.2435E-05 -0.1701
10.00 8.2 16 -0.0427 -0.000100 -0.001179 -0.001498 5.9820 5.7595 5.9869 0.003828 0.5  0.348396 155.0  300 -0.298398  650.0 350 1.5238E-05 -1.2435E-05 -0.1665
    """)


def _get_correction_for_philippines(C, sites, rup, is_slab=False):
    r_volc_front = _get_min_distance_to_volcanic_front(sites.lons,
                                                       sites.lats)
    delta = 0.
    if rup.hypo_depth*30. >= 80 and is_slab:
        delta = C['ph']
    return C['gsw'] * r_volc_front * (rup.hypo_depth*30) + delta


def _get_correction_for_pacific(C, sites, rup):
    r_volc_front = _get_min_distance_to_volcanic_front(sites.lons,
                                                       sites.lats)
    return C['gne'] * r_volc_front * (rup.hypo_depth*30)


class MorikawaFujiwara2013SInterPacific(GMPE):
    """  """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        C = self.COEFF[imt]
        # computing the mean
        correction = _get_correction_for_pacific(C, sites, rup)
        mean = C['c2'] + self._get_mean(sites, rup, dists, C) + correction
        stds = self._get_std(sites)
        return mean, stds


class MorikawaFujiwara2013SInterPhilippines(GMPE):
    """  """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        C = self.COEFF[imt]
        # computing the mean
        correction = _get_correction_for_pacific(C, sites, rup)
        mean = C['c2'] + self._get_mean(sites, rup, dists, C) + correction
        stds = self._get_std(sites)
        return mean, stds


class MorikawaFujiwara2013SSlabPacific(GMPE):
    """  """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        C = self.COEFF[imt]
        # computing the mean
        correction = _get_correction_for_pacific(C, sites, rup)
        mean = C['c3'] + self._get_mean(sites, rup, dists, C) + correction
        stds = self._get_std(sites)
        return mean, stds


class MorikawaFujiwara2013SSlabPhilippines(GMPE):
    """  """

    #: Supported tectonic region type is active shallow crust
    DEFINED_FOR_TECTONIC_REGION_TYPE = const.TRT.SUBDUCTION_INTERFACE

    #: Required rupture parameters are magnitude, and hypocentral depth
    REQUIRES_RUPTURE_PARAMETERS = set(('mag', 'hypo_depth'))

    def get_mean_and_stddevs(self, sites, rup, dists, imt, stddev_types):
        """ """
        C = self.COEFF[imt]
        # computing the mean
        correction = _get_correction_for_philippines(C, sites, rup, True)
        mean = C['c3'] + self._get_mean(sites, rup, dists, C) + correction
        stds = self._get_std(sites)
        return mean, stds
