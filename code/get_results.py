from __future__ import print_function
import pandas as pd
import os
import sys
import glob
import datetime
import AngelScraper as AS
from tqdm import tqdm

a = AS.AngelScraper()
result_dir = a.results_folder

dfs = []

f_list = glob.glob(os.path.join(result_dir, '*.csv'))

print(len(f_list))

df = None

for f in tqdm(f_list):
    if df is None:
        df = pd.read_csv(f)
    else:
        df = pd.concat([df, pd.read_csv(f)], ignore_index=True)
        df = df.drop_duplicates()

print(df.head())
print(df.count())
print(df.describe())
print(df.columns)

df.to_csv(os.path.join(a.output_dir, 'results_so_far_{}.csv'.format(datetime.datetime.now())))
