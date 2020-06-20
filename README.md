# Bitcoin-ML
by: Anthony Bravo
Predicts bitcoin price using sentimental analysis and machine learning

overview:
1. pulls tweets from twitter using tweepy
2. cleans data -> removing hashtags, retweets, mentions, and urls
3. reorders data by data
4. pulls stock prices from yahoo using pandas datareader
5. place prices with corresponding dates
6. find subjectivity and polarity using textblob
7. seperate dataframe by training and testing data
8. prepare numpy arrays to be insert to random forest regressor and treeinterpreter]
9. get predictions and plot
