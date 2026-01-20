import pandas as pd
from os.path import join

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity

class recommend:

  def __init__(self, root):
    self.url = join(root, r"model\recommendation")
    self.movie = {"Angry":["Family", "Drama"], "Disgust": ["Musical", "Fantasy"], "Happy":["Action", "Science Fiction", "Thriller"], "Fear":["Musical","Action", "Fantasy"], "Sad":["Comedy", "Drama", "Romance"], "Surprise":["Adventure","Mystery", "Horror"], "Neutral":["Adventure","Mystery", "Horror"]}
    self.book = {"Angry":["Romance", "Travel"], "Disgust": ["Fantasy", "History"], "Happy":["Science_fiction", "Thriller"], "Fear":["Fantasy", "Sport"], "Sad":["Romance"], "Surprise":["Thrilller", "Horror"], "Neutral":["Thrilller", "Horror"]}
    self.song = {"Angry":["Calm"], "Disgust": ["Sad"], "Happy":["Happy"], "Fear":["Calm"], "Sad":["Happy"], "Surprise":["Energetic"], "Neutral":["Energetic"]}

  def get_movie(self, title):
    mv = pd.read_csv(join( self.url,'final_movies.csv'))
    return mv[mv['title'].isin(title)][['title', 'year', 'overview']].to_json(orient="records")
  def get_book(self, title):
    mv = pd.read_csv(join( self.url,'final_book (1).csv'))
    return mv[mv['title'].isin(title)][['title', 'author', 'synopsis']].to_json(orient="records")
  def get_song(self, title):
    mv = pd.read_csv(join( self.url,'songs1.csv'))
    return mv[mv['name'].isin(title)][['name', 'artist', 'release_date']].to_json(orient="records")
  def get_sport(self, title):
    mv = pd.read_csv(join( self.url,'activity.csv'))
    return mv[mv['Title'].isin(title)][['Title', 'Description']].to_json(orient="records")
  def get_fun(self,title):
    mv = pd.read_csv(join( self.url,'activity.csv'))
    return mv[mv['Title'].isin(title)][['Title', 'Description']].to_json(orient="records")

  def movie_recommend(self,mood, already_watch,  title, pref):
    genre = self.movie[mood]
    genre = list(set(genre) & set(pref)) 
    if len(genre)==0:
      genre = self.movie[mood]
    smd = pd.read_csv(join( self.url,'final_movies.csv'))
    smd['description'] = smd['description'].fillna('')
    links_small = pd.read_csv(join( self.url,'links_small.csv'))
    links_small = links_small[links_small['tmdbId'].notnull()]['tmdbId'].astype('int')
    smd['id'] = smd['id'].astype('int')
    smd = smd[smd['id'].isin(links_small)]
    smd['genres'] = smd['genres'].astype('str')
    id = []
    for i, row in smd.iterrows():
      if row['title']==title or any(check in row['genres'].split(',') for check in genre):
        id.append(row['id'])
    df = smd[smd['id'].isin(id)]

    if title:
      tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
      tfidf_matrix = tf.fit_transform(df['description'])
      cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
      df = df.reset_index()
      titles = df[['title', 'year', 'overview']]
      indices = pd.Series(df.index, index=df['title'])
      idx = indices[title]
      sim_scores = list(enumerate(cosine_sim[idx]))
      sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
      sim_scores = sim_scores[1:5]
      movie_indices = [i[0] for i in sim_scores]
      ans = titles.iloc[movie_indices]
      ans = ans[~ans['title'].isin(already_watch)]
      ans = ans.head(1)
      res = ans.values.tolist()
      if len(res)>0:
        return ans.to_json(orient="records")
      
    vote_counts = df[df['vote_count'].notnull()]['vote_count'].astype('int')
    vote_averages = df[df['vote_average'].notnull()]['vote_average'].astype('int')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.85)
    
    df = df[(df['vote_count'] >= m) & (df['vote_count'].notnull()) & (df['vote_average'].notnull())]
    df['vote_count'] = df['vote_count'].astype('int')
    df['vote_average'] = df['vote_average'].astype('int')
    
    df['wr'] = df.apply(lambda x: (x['vote_count']/(x['vote_count']+m) * x['vote_average']) + (m/(m+x['vote_count']) * C), axis=1)
    df = df[~df["title"].isin(already_watch)]
    ans = df.sort_values('wr', ascending=False).head(1)
    ans = ans[['title', 'year', 'overview']]
    return ans.to_json(orient="records")


  def book_recommend(self, mood ,already_read, title, pref):
    genre = self.book[mood]
    genre = list(set(genre) & set(pref)) 
    if len(genre)==0:
      genre = self.book[mood]
    bd = pd.read_csv(join( self.url,'final_book (1).csv'))
    bd['synopsis'] = bd['synopsis'].fillna('')
    bd['id'] = bd['id'].astype('int')
    bd['genre'] = bd['genre'].astype('str')
    bd['genre'] = bd['genre'].str.title()
    df = bd[bd['genre'].isin(genre)]
    
    if title:
      tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
      tfidf_matrix = tf.fit_transform(df['synopsis'])
      cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
      df = df.reset_index()
      titles = df[['title', 'author', 'synopsis']]
      indices = pd.Series(df.index, index=df['title'])
      idx = indices[title]
      sim_scores = list(enumerate(cosine_sim[idx]))
      sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
      sim_scores = sim_scores[1:5]
      book_indices = [i[0] for i in sim_scores]
      ans = titles.iloc[book_indices]
      ans = ans[~ans['title'].isin(already_read)]
      ans = ans.head(1)
      res = ans.values.tolist()
      if len(res)>0:
        return ans.to_json(orient="records")

    vote_counts = df[df['num_ratings'].notnull()]['num_ratings'].astype('int')
    vote_averages = df[df['rating'].notnull()]['rating'].astype('float')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.65)
    
    df = df[df['num_ratings'] >= m]
    df['num_ratings'] = df['num_ratings'].astype('int')
    df['rating'] = df['rating'].astype('float')
    df['wr'] = df.apply(lambda x: (x['num_ratings']/(x['num_ratings']+m) * x['rating']) + (m/(m+x['num_ratings']) * C), axis=1)
    df = df[~df["title"].isin(already_read)]
    ans = df.sort_values('wr', ascending=False).head(1)
    ans = ans[["title", "author", "synopsis"]]
    return ans.to_json(orient="records")
    
  def song_recommend(self,Mood, listen, percentile=0.65):
    sd = pd.read_csv(join( self.url,'songs1.csv'))
    df = sd[sd['mood'].isin(self.song[Mood])]
    popularity = df[df['popularity'].notnull()]['popularity'].astype('int')
    C = popularity.mean()
    df = df[df['popularity'] >= C]
    if len((df[~df["name"].isin(listen)]).index)>=3:
      df = df[~df["name"].isin(listen)]
    df = df.sort_values('popularity', ascending=False).head(3)
    
    return df[['name', 'artist', 'release_date']].to_json(orient="records")

  def other_recommend(self,Mood, category, already_done, title):
    ad = pd.read_csv(join( self.url,'activity.csv'))

    id = []
    for i, row in ad.iterrows():
      if any(check in row['Mood'].split(', ') for check in Mood):
        id.append(row['Title'])
    df = ad[(ad['Title'].isin(id)) & (ad['Category']==category)]
    print(df.head(5))
    df = df[~df['Title'].isin(already_done)]

    print(id)
    if title:
      tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=0, stop_words='english')
      tfidf_matrix = tf.fit_transform(df['Descripion'])
      cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
      df = df.reset_index()
      titles = df[['Title', 'Description']]
      indices = pd.Series(df.index, index=df['Title'])
      idx = indices[already_done[0]]
      sim_scores = list(enumerate(cosine_sim[idx]))
      sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
      sim_scores = sim_scores[1:5]
      book_indices = [i[0] for i in sim_scores]
      ans = titles.iloc[book_indices]
      ans = ans[~ans['Title'].isin(already_done)]
      ans = ans.head(1)
      res = ans.values.tolist()
      if len(res)>0:
        return ans.to_json(orient="records")
      
    return (df[["Title", "Description"]].head(1)).to_json(orient="records")