import pandas as pd
md = pd.read_csv('./songs.csv')
d = md.sort_values('popularity', ascending=False)
d.to_csv('songs1.csv')
