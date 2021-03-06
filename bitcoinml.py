"""

Automatically generated by Colaboratory.

"""

#Import Libraries
import tweepy
from textblob import TextBlob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timezone
!pip install treeinterpreter
from treeinterpreter import treeinterpreter
from sklearn.ensemble import RandomForestRegressor
import pandas_datareader as web

# Twitter API credentials
consumerKey = ""
consumerSecret = ""
accessToken = ""
accessTokenSecret = ""

# Enter Auth crednetials and create API
authenticate = tweepy.OAuthHandler(consumerKey, consumerSecret)
authenticate.set_access_token(accessToken, accessTokenSecret)

api = tweepy.API(authenticate, wait_on_rate_limit = True)

# Get tweets relating bitcoin, using "popular" to get tweets from a range of dates
# Using while loop with try/except to counter any memory or system error
query = "bitcoin"
max_tweets = 10
posts = []
last_id = -1
while len(posts) < max_tweets:
  count = max_tweets - len(posts)
  try:
    new_tweets = api.search(q=query, count= count, lang="en",result_type = "popular",max_id=str(last_id - 1))
    if not new_tweets:
      break
    posts.extend(new_tweets)
    last_id = new_tweets[-1].id
  except tweepy.TweepError as e:
    break

for tweet in posts:
  print(tweet)

# Create a dataframe with a column called Tweets
tweet_data = pd.DataFrame(data=[[tweet_info.created_at.date(),tweet_info.created_at.time(),tweet_info.text]for tweet_info in posts],columns=['Date',"Time",'Tweets'])
#Show the first 5 rows of data
tweet_data

# Cleaning Data

# Create a function to clean the tweets
def clean_data(text):
  text = text.split()
  i = 0
  while i < len(text):
    if text[i][0] == "@":
      text.remove(text[i])
      i=0
      continue
    if text[i][0] == "#":
      if len(text[i]) == 1:
        text.remove(text[i])
      else:
        temp = list(text[i])
        temp.remove(temp[0])
        temp = "".join(temp)
        text[i] = temp
      i=0
      continue
    if text[i] == "RT":
      text.remove(text[i])
      i=0
      continue
    if text[i][0:4] == "http":
      text.remove(text[i])
      i=0
      continue
    i+=1
  return " ".join(text)

tweet_data["Tweets"] = tweet_data["Tweets"].apply(clean_data)
tweet_data

# See oldest date and earliest date
print(tweet_data["Date"].min())
print(tweet_data["Date"].max())

# Get Bitcoin info from yahoo finance
start = tweet_data["Date"].min()
end = tweet_data["Date"].max()
stock_data = web.DataReader("BTC-USD", "yahoo", start, end).reset_index()
stock_data

# Add Bitcoin's Prices to tweet_data

tweet_data["Prices"] = ""

# Compare dates and add corresponding prices to tweet data table
for x in range(0, len(tweet_data)):
  for y in range(0, len(stock_data)):
    tweet_date = tweet_data.Date.iloc[x]
    stock_date = stock_data.Date.iloc[y]
    # Turn both datas into datetime objects for comparison
    tweet_datetime = datetime(tweet_date.year, tweet_date.month, tweet_date.day)
    stock_datetime = datetime(stock_date.year, stock_date.month, stock_date.day)

    if stock_datetime == tweet_datetime:
      tweet_data.at[x, "Prices"] = stock_data.Close[y]
      break
tweet_data

# Filling in missing prices with average of existing prices

def find_average(data):
  data_sum = 0
  count = 0
  for i in range(0, len(data)):
    if data.Prices.iloc[i] != "":
      data_sum+=int(data.Prices.iloc[i])
      count += 1
  if data_sum == 0:
    return data.Close.iloc[0]
  else:
    return data_sum / count

# Apply function and fill in missing data
average_price = find_average(tweet_data)

for i in range(0, len(tweet_data)):
  if tweet_data.Prices.iloc[i] =="":
    tweet_data.Prices.iloc[i] = int(average_price)

tweet_data

# Sort data by dates 
tweet_data.sort_values("Date", inplace=True)
tweet_data.reset_index(drop=True, inplace=True)
tweet_data

# Functions for finding subjectivity and polarity
def find_subjectivity(text):
  return TextBlob(text).sentiment.subjectivity

def find_polarity(text):
  return TextBlob(text).sentiment.polarity

# Apply functions
tweet_data["Subjectivity"] = tweet_data["Tweets"].apply(find_subjectivity)
tweet_data["Polarity"] = tweet_data["Tweets"].apply(find_polarity)
tweet_data

# Function for determining analysis
def find_analysis(score):
  if score < 0:
    return "Negative"
  elif score == 0:
    return "Neutral"
  elif score > 0:
    return "Positive"
  
# Apply function
tweet_data["Analysis"] = tweet_data["Polarity"].apply(find_analysis)
tweet_data

# Function for finding sentimental analysis percent 
def find_percent(PNNtype, data):
  #PNNtype is positive, negative, or neutral, type is str
  count = 0
  for x in range(0, len(data)):
    if data.Analysis.iloc[x] == PNNtype:
      count += 1
  
  return round(count/data.shape[0],1)*100

# Get percent of positive, negative, neutral tweets
postivive_tweets_percent = find_percent("Positive", tweet_data)
negative_tweets_percent = find_percent("Negative", tweet_data)
neutral_tweets_percent = find_percent("Neutral", tweet_data)

print("Percentage of Postive tweets are: {}\nPercentage of Negative tweets are: {}\nPercentage of Neutral tweets are: {}".format(postivive_tweets_percent, negative_tweets_percent, neutral_tweets_percent))

# Machine Learning Algorthm starts here
# Create seperate df for ML
shorten_df = tweet_data[["Date", "Prices", "Polarity", "Analysis"]].copy()

#Preparing training and testing arrays
#Indexing is made by dividing the df in 60 % is training and rest is testing
training_df = shorten_df.loc["0":str(int(shorten_df.shape[0]*.6))]
testing_df = shorten_df.loc[str(int(shorten_df.shape[0]*.6+1)): str(shorten_df.shape[0]-1)]

training_df

# Function for preparing arrays, made to aviod repeatative code
def prep_polarityAnalysis_array(data):
  temp_list = []
  for date, row in data.T.iteritems():
    value = np.asarray([shorten_df.loc[date, "Polarity"]])
    temp_list.append(value)
  return np.asarray(temp_list)

# Preparing arrays for polarity, analysis, and prices
# polarity and analysis
polarity_train = prep_polarityAnalysis_array(training_df)
polarity_test = prep_polarityAnalysis_array(testing_df)

# Prices
prices_train = pd.DataFrame(training_df["Prices"])

# Applying data into regressor
rf = RandomForestRegressor()
rf.fit(polarity_train, prices_train)

# Getting Predictions
prediction, bias, contributions = treeinterpreter.predict(rf, polarity_test)
print(prediction)

# Reformatting data for plotting
# Puttings predictions into a list
prediction_2 = []
for x in prediction:
  prediction_2.append(round(float(x[0]),1))

# Putting predictions, actual price, and the date into one dataframe
comparison_df = testing_df[["Date", "Prices"]].copy()
comparison_df.rename(columns={"Prices":"Actual"}, inplace=True)
comparison_df["Prediction"] = prediction_2
comparison_df.reset_index(drop=True, inplace=True)


comparison_df.plot()
print("Comparison table:")
print(comparison_df)

# Final thoughs
'''
Problems:
- Using twitter data is not the best because most twitters are very neutral
- Many users that use the bitcoin hashtag are promoting some company
- Twitter's api has a limit on the amount of tweets to obtain around 3,200
- Google's colab has a limited disk and I was not able to obtain around 200 tweets
- Some dates dont have a closing price <- this is where I replace with an average
- Tweets come in every second so its hard to get more dates

Solution(may be implement later): 
- Get a tweet from the bitcoin hashtag every other day so we have more variety of prices to test and train
- Could use another data venders such as news outlets 

*Made for educational purposes to understand and practice with machine learning* 
'''
