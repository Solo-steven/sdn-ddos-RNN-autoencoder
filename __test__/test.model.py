
import sys
import os
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)


import pandas as pd
import numpy as np
from model import RNNAutoEncoderDetector


if __name__ == "__main__":
    normal_df = pd.read_csv('{}/data/normal.csv'.format(parent))
    anomal_df = pd.read_csv('{}/data/attack.csv'.format(parent))
    normal_df_drop_id = normal_df.drop(['datapath_id'], axis=1)
    anomal_df_drop_id = anomal_df.drop(['datapath_id'], axis=1)

    model = RNNAutoEncoderDetector()
    model.train(normal_df_drop_id)
    model.envalute(normal_df_drop_id, anomal_df_drop_id)
