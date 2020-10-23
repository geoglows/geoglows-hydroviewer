import glob
import os

import pandas as pd

from .app import GeoglowsHydroviewer as App

SHAPE_DIR = App.get_custom_setting('global_delineation_shapefiles_directory')


def get_project_directory(project):
    workspace_path = App.get_app_workspace().path
    project = str(project).replace(' ', '_')
    return os.path.join(workspace_path, 'projects', project)


def shapefiles_downloaded():
    shape_dir_contents = glob.glob(os.path.join(SHAPE_DIR, '*geoglows*.zip'))
    if len(shape_dir_contents) == 39:
        return True
    return False


def walk_upstream(df: pd.DataFrame, target_id: int, id_col: str, next_col: str, order_col: str = None,
                  same_order: bool = False) -> tuple:
    """
    Traverse a stream network table containing a column of unique ID's, a column of the ID for the stream/basin
    downstream of that point, and, optionally, a column containing the stream order.
    (c) Riley Hales, all rights reserved. This function is from a not-yet-published python package.

    Args:
        df (pd.DataFrame): a pandas DataFrame containing the id_col, next_col, and order_col if same_order is True
        target_id (int): the ID of the stream to begin the search from
        id_col (str): name of the DataFrame column which contains stream/basin ID's
        next_col (str): name of the DataFrame column which contains stream/basin ID's of the downstream segments
        order_col (str): name of the DataFrame column which contains stream orders
        same_order (bool): True limits searching to streams of the same order as the starting stream. False searches
            all streams until the head of each branch is found

    Returns:
        Tuple of stream ids in the order they come from the starting point. If you chose same_order = False, the
        streams will appear in order on each upstream branch but the various branches will appear mixed in the tuple in
        the order they were encountered by the iterations.
    """
    df_ = df[[id_col, next_col]]

    # start a list of the upstream ids
    upstream_ids = [target_id, ]
    upstream_rows = df_[df_[next_col] == target_id]

    while not upstream_rows.empty or len(upstream_rows) > 0:
        print('yes')
        if len(upstream_rows) == 1:
            upstream_ids.append(upstream_rows[id_col].values[0])
            upstream_rows = df_[df_[next_col] == upstream_rows[id_col].values[0]]
        elif len(upstream_rows) > 1:
            for s_id in upstream_rows[id_col].values.tolist():
                upstream_ids += list(walk_upstream(df_, s_id, id_col, next_col, order_col, same_order))
                upstream_rows = df_[df_[next_col] == s_id]
    return tuple(set(upstream_ids))
