import glob, sys
import pandas as pd

path_pattern = sys.argv[1] # Path to csv files + pattern -> datasets/collected_wines*
destination_file = sys.argv[2] # Path + name of destination file

dfs = glob.glob('{}.csv'.format(path_pattern))
result = pd.concat([pd.read_csv(df) for df in dfs], ignore_index=True)
result.to_csv('{}.csv'.format(destination_file), index=False)
