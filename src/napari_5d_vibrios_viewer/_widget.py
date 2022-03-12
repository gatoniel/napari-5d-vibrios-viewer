"""
This module is an example of a barebones QWidget plugin for napari

It implements the Widget specification.
see: https://napari.org/plugins/stable/guides.html#widgets

Replace code below according to your needs.
"""
import os
from glob import glob

import dask.array as da
from dask import delayed
from magicgui.widgets import FileEdit
from qtpy.QtWidgets import QHBoxLayout, QPushButton, QWidget
from skimage.io.collection import alphanumeric_key
from tifffile import imread


def new_imread(f):
    return imread(f)[1:, ...]


def read_files(files):
    filenames = sorted(glob(files), key=alphanumeric_key)
    sample = new_imread(filenames[0])

    lazy_imread = delayed(new_imread)
    lazy_arrays = [lazy_imread(fn) for fn in filenames]
    dask_arrays = [
        da.from_delayed(delayed_reader, shape=sample.shape, dtype=sample.dtype)
        for delayed_reader in lazy_arrays
    ]
    return da.stack(dask_arrays, axis=0)


class DaskViewer(QWidget):
    # your QWidget.__init__ can optionally request the napari viewer instance
    # in one of two ways:
    # 1. use a parameter called `napari_viewer`, as done here
    # 2. use a type annotation of 'napari.viewer.Viewer' for any parameter
    def __init__(self, napari_viewer):
        super().__init__()
        self.viewer = napari_viewer

        self.file_edit = FileEdit(label="Folder: ", mode="d")
        btn = QPushButton("Click me!")
        btn.clicked.connect(self._on_click)

        self.setLayout(QHBoxLayout())
        self.layout().addWidget(self.file_edit.native)
        self.layout().addWidget(btn)

    def _on_click(self):
        path = self.file_edit.value
        channels = list(range(1, 4))
        channel_names = ["mKate", "mKokappa", "GFP"]
        channel_colormaps = ["red", "bop orange", "green"]
        stacks = [read_files(os.path.join(path, f"*ch{i}*.tif")) for i in channels]

        for i in range(len(channels)):
            print(stacks[i].shape)
            self.viewer.add_image(
                stacks[i], name=channel_names[i], colormap=channel_colormaps[i]
            )
