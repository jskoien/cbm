#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This file is part of CbM (https://github.com/ec-jrc/cbm).
# Author    : Konstantinos Anastasakis
# Credits   : GTCAP Team
# Copyright : 2021 European Commission, Joint Research Centre
# License   : 3-Clause BSD

import glob
from os.path import join, normpath
from copy import copy
from descartes import PolygonPatch
from rasterio.plot import show
import rasterio
import matplotlib.pyplot as plt
import json

from cbm.get import chip_images
from cbm.utils import config, spatial_utils
from mpl_toolkits.axes_grid1 import ImageGrid


def overlay_parcel(img, geom):
    """Create parcel polygon overlay"""
    patche = [PolygonPatch(feature, edgecolor="yellow",
                           facecolor="none", linewidth=2
                           ) for feature in geom['geom']]
    return patche


def chips(aoi, pid, dates, band, chipsize, quiet=True):
    """Plot chip image with parcel polygon overlay.

    Examples:
        import cbm
        cbm.get.chip_images.by_pid(aoi, year, pid, start_date, end_date,
                                    band, chipsize)

    Arguments:
        aoi, the area of interest e.g.: es, nld (str)
        year, the year of the parcels dataset (int)
        pid, the parcel id (int).
        start_date, Start date '2019-06-01' (str)
        end_date, End date '2019-06-01' (str)
        band, 3 Sentinel-2 band names. One of [‘B02’, ‘B03’, ‘B04’, ‘B08’]
            (10 m bands) or [‘B05’, ‘B06’, ‘B07’, ‘B8A’, ‘B11’, ‘B12’]
            (20 m bands). 10m and 20m bands can be combined.
            The first band determines the resolution in the output
            composite. Defaults to B08_B04_B03.
        chipsize, size of the chip in pixels (int).
    """
    columns = 4

    if type(dates) is list:
        start_date, end_date = dates[0], dates[1]
    else:
        start_date, end_date = dates, dates
    year = start_date.split('-')[0]
    workdir = normpath(join(config.get_value(['paths', 'temp']),
                            f'{aoi}{str(year)}', str(pid)))
    chip_images.by_pid(aoi, year, pid, start_date, end_date,
                       band, chipsize, quiet)

    chips_dir = normpath(join(workdir, 'chip_images'))
    if type(dates) is list:
        chips = normpath(join(chips_dir, f"*{band}.tif"))
    else:
        chips = normpath(
            join(chips_dir, f"*{start_date.replace('-', '')}*{band}.tif"))

    chips_list = glob.glob(chips)

    if len(chips_list) > 0:
        if len(chips_list) < columns:
            columns = len(chips_list)

        with open(normpath(join(workdir, 'info.json')), 'r') as f:
            json_data = json.load(f)

        with rasterio.open(chips_list[0]) as img:
            img_epsg = img.crs.to_epsg()
            geom = spatial_utils.transform_geometry(json_data, img_epsg)
            patches = overlay_parcel(img, geom)

        if not quiet:
            for chip in chips_list:
                print(chip)

        rows = int(len(chips_list) // columns +
                   (len(chips_list) % columns > 0))
        fig = plt.figure(figsize=(30, 10 * rows))
        grid = ImageGrid(fig, 111,  # similar to subplot(111)
                         nrows_ncols=(rows, columns),  # creates grid of axes
                         axes_pad=0.4,  # pad between axes in inch.
                         )

        for ax, t in zip(grid, chips_list):
            with rasterio.open(t) as img:
                for patch in patches:
                    ax.add_patch(copy(patch))
                show(img, ax=ax)
                ax.set_title(t.split('_')[-1].split('.')[0], fontsize=20)

        if len(chips_list) > columns:
            for ax in grid[-((columns * rows - len(chips_list))):]:
                ax.remove()

        plt.show()
    else:
        print("! No images to show.")
