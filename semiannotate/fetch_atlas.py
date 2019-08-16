# vim: fdm=indent
#author:     Fabio Zanini
#date:       12/08/19
#content:    Fetch cell atlas data, averaged by cell type
__all__ = ['AtlasFetcher']

import os
import numpy as np
import pandas as pd
import requests
import io
import loompy
import tempfile


class AtlasFetcher(object):
    '''Fetch averaged cell atlas data'''
    atlas_table = None

    def fetch_atlas_table(self):
        '''Fetch atlas table from GitHub repo'''
        url = 'https://github.com/iosonofabio/atlas_averages/raw/master/table.tsv'
        r = requests.get(url)
        table = pd.read_csv(io.BytesIO(r.content), sep='\t')
        self.atlas_table = table

    def list_atlases(self):
        '''List atlases available on GitHub repo'''
        if self.atlas_table is None:
            self.fetch_atlas_table()
        return self.atlas_table.copy()

    def fetch_atlas(self, atlas_name):
        '''Fetch an atlas from GitHub repo

        Args:
            atlas_name (str): the name of the atlas (see atlas table)
        '''
        if self.atlas_table is None:
            self.fetch_atlas_table()

        url = self.atlas_table.at[atlas_name, 'URL']
        r = requests.get(url)

        # Use a temp file, loompy has its own quirks
        fd, path = tempfile.mkstemp()
        try:
            with os.fdopen(fd, 'wb') as tmp:
                # do stuff with temp file
                tmp.write(r.content)

            with loompy.connect(path) as dsl:
                matrix = dsl.layers[''][:, :]
                cell_types = dsl.ca['CellType']
                n_of_cells = dsl.ca['NumberOfCells']
                features = dsl.ra['GeneName']

        finally:
            os.remove(path)

        # Package into dataframes
        counts = pd.DataFrame(
            data=matrix,
            index=features,
            columns=cell_types,
            )
        number_of_cells = pd.Series(
            data=n_of_cells,
            index=cell_types,
            )

        return {
            'counts': counts,
            'number_of_cells': number_of_cells,
            }

    def fetch_multiple_atlases(self, atlas_names):
        '''Fetch and combine multiple atlases

        Args:
            atlas_names (list of str): the names of the atlases (see
            atlas table)
        '''
        ds = {}
        if len(atlas_names) == 0:
            return ds

        # Fetch data for all atlases
        for atlas_name in atlas_names:
            ds[atlas_name] = self.fetch_atlas(atlas_name)

        # Get overlapping features, list of all cells, etc.
        # Rename cells to ensure there are no duplicates
        cell_names = []
        cell_names_new = []
        features = None
        cell_dataset = []
        for at, d in ds.items():
            cell_names.extend(d['counts'].columns.tolist())
            cell_names_new.extend(['{:}_{:}'.format(at, x) for x in d['counts'].columns])
            cell_dataset.extend([at] * d['counts'].shape[1])
            if features is None:
                features = d['counts'].index.values
            else:
                features = np.intersect1d(
                    features, d['counts'].index.values,
                    )
        cell_names = np.array(cell_names)
        cell_names_new = np.array(cell_names_new)

        # Fill the combined dataset
        matrix = np.empty((len(features), len(cell_names)), np.float32)
        n_cells_per_type = np.empty(len(cell_names), int)
        i = 0
        for at, d in ds.items():
            n = d['counts'].shape[1]
            matrix[:, i: i+n] = d['counts'].loc[features].values
            n_cells_per_type[i: i+n] = d['number_of_cells'].values
            i += n

        counts = pd.DataFrame(
            data=matrix,
            index=features,
            columns=cell_names_new,
            )
        number_of_cells = pd.Series(
            data=n_cells_per_type,
            index=cell_names_new,
            )
        cell_dataset = pd.Series(
            data=cell_dataset,
            index=cell_names_new,
            )

        return {
            'counts': counts,
            'number_of_cells': number_of_cells,
            'atlas': cell_dataset,
            }