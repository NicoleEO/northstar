# vim: fdm=indent
# author:     Fabio Zanini
# date:       17/06/19
# content:    Test the algorithm on same artificial data
import numpy as np
import pandas as pd
from semiannotate import Subsample, AtlasFetcher


def test_run_within_atlas():
    aname = 'Darmanis_2015'
    atlas = AtlasFetcher().fetch_atlas(
            aname, kind='subsample')
    matrix = atlas['counts']
    cell_types = atlas['cell_types'].values
    print(cell_types)

    sa = Subsample(aname, matrix)
    sa()

    # Nobody's perfect
    assert((cell_types == sa.membership).mean() >= 0.9)


def test_run_across_atlas():
    atlas = AtlasFetcher().fetch_atlas(
            'Enge_2017', kind='subsample')
    matrix = atlas['counts']
    cell_types = atlas['cell_types'].values

    sa = Subsample('Baron_2016', matrix)
    sa()

    # Nobody's perfect
    # Baron annotates Stellate cells more accurately, so we skip them
    assert((cell_types == sa.membership)[:60].mean() >= 0.7)


if __name__ == '__main__':

    test_run_across_atlas()

