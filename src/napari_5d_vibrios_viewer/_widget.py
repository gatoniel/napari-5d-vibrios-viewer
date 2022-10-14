"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/plugins/stable/guides.html#widgets

Replace code below according to your needs.
"""
import os
from glob import glob

import dask.array as da
import numpy as np
from dask import delayed
from magicgui.widgets import FileEdit, Label
from qtpy.QtWidgets import QVBoxLayout, QPushButton, QWidget
from skimage.io.collection import alphanumeric_key
from tifffile import imread, TiffFile
from pathlib import Path

from dask.cache import Cache
from tqdm import tqdm

from .helpers import get_experiment_df

cache = Cache(2e10)  # Leverage twenty gigabytes of memory
cache.register()  # Turn cache on globally


@delayed
def read_page(f, page):
    print(f, page)
    return imread(f, key=page)


def new_imread(f):
    tif = TiffFile(f)
    lazy_arrays = [read_page(f, i) for i in range(1, len(tif.pages))]
    dask_arrays = [
        da.from_delayed(delayed_reader, shape=(1024, 1024), dtype=np.uint16)
        for delayed_reader in lazy_arrays
    ]
    img = da.stack(dask_arrays, axis=0)

    return img


def read_files(files):
    filenames = sorted(glob(files), key=alphanumeric_key)

    imgs = [new_imread(fn) for fn in tqdm(filenames)]
    img = da.stack(imgs, axis=0)

    return img


class DaskViewer(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.exp_df = get_experiment_df(
            r"Z:\Henriette\Chitin project 2021\Chitin - Confocal data overview.xlsx"
        )
        self.exp_df_60 = get_experiment_df(
            r"Z:\Henriette\Chitin project 2021\Chitin - Confocal data overview 60x.xlsx"
        )

        self.mut_label = Label(value="")
        self.file_edit = FileEdit(label="Folder: ", mode="d")
        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QVBoxLayout())
        self.layout().addWidget(self.mut_label.native)
        self.layout().addWidget(self.file_edit.native)
        self.layout().addWidget(btn)

    def _on_click(self):
        path = self.file_edit.value

        well = Path(path).name.split("_")[0]
        exp = Path(path).parents[0].name

        experiment_id = f"{exp}-{well}"

        try:
            descr = self.exp_df.loc[experiment_id, :]
        except KeyError:
            descr = self.exp_df_60.loc[experiment_id, :]

        label_text = f"{descr['Strains']} ({descr['Ratio']})"
        self.mut_label.value = label_text

        # channels = list(range(1, 5))
        channels = [4, 1, 2, 3]
        channel_names = ["brightfield", "mKate", "mKokappa", "GFP"]
        channel_colormaps = [
            "gray",
            "red",
            "bop orange",
            "green",
        ]
        # channels = list(range(1, 4))
        # channel_names = [f"ch{i}" for i in channels]
        # channel_colormaps = ["red", "green", "blue"]
        print(channels)
        stacks = [read_files(os.path.join(path, f"*ch{i}*.tif")) for i in channels]

        slices = [
            slice(None, -1),
            slice(None, -1),
            slice(1, None),
            slice(None, -1),
        ]

        for i in range(len(channels)):
            print(stacks[i].shape)
            self.viewer.add_image(
                stacks[i][..., slices[i], slices[i]],
                name=channel_names[i],
                colormap=channel_colormaps[i],
                opacity=0.5,
                scale=(1, 1, 0.3289, 0.3289),
            )
