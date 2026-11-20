import pandas as pd
from datetime import datetime
import re

subreddits = {"4chan": "4chan_09_11.jsonl",
              "Antiwork": "Antiwork_10_11.jsonl",
              "AsianMasculinity": "AsianMasculinity_11_11.jsonl",
              "aznidentity": "aznidentity_11_11.jsonl",
              "BlackPeopleTwitter": "BlackPeopleTwitter_11_11.jsonl",
              "climateskeptics": "climateskeptics_12_11.jsonl",
              "conservatives": "conservatives_12_11.jsonl",
              "conspiracy": "conspiracy_12_11.jsonl",
              "GoldandBlack": "GoldandBlack_12_11.jsonl",
              "HermanCainAward": "HermanCainAward_12_11.jsonl",
              "KotakuInAction": "KotakuInAction_13_11.jsonl",
              "MensRights": "MensRights_13_11.jsonl",
              "NoFap": "NoFap_13_11.jsonl",
              "prolife": "prolife_13_11.jsonl",
              "TrueUnpopularOpinion": "TrueUnpopularOpinion_13_11.jsonl",
              "WhitePeopleTwitter": "WhitePeopleTwitter_14_11.jsonl"
             } # subreddits dictionnary with the subreddit names as its keys and the corresponding files collected through the API as its values


"""
POSTS DATAFRAME

"""


dataframes = []

for subreddit in subreddits:
    df = pd.read_json(subreddits[subreddit], lines=True) # turns each jsonl file into a DataFrame
    df["subreddit"] = subreddit # creates a subreddit column in the DataFrames to keep track of it
    dataframes.append(df) # creates a list of subreddit DataFrames

posts = pd.concat(dataframes) # concatenates the DataFrames list into one DataFrame

posts["created_utc"] = pd.to_datetime(posts["created_utc"], unit="s") # turns each post's UTC timestamp into a datetime object
too_old = posts["created_utc"] <= datetime(2023, 12, 14) # localizes the posts from before 14/12/2023 (there were only 5)
posts = posts[~too_old] # removes the posts from before 2023

posts = posts.reset_index(drop=True) # resets the index column that was left in shambles after the concatenation and the deletion

posts.head(10)


"""
COMMENTS DATAFRAME

"""


comments_dataframes = []

for x in posts.index:
    df = pd.DataFrame(posts.loc[x, "comments"]) # turns the "comments" list of dictionnaries of each post into a DataFrame
    df["subreddit"] = posts.loc[x, "subreddit"] # again, creates a "subreddit" column into each DataFrame
    comments_dataframes.append(df)

comments = pd.concat(comments_dataframes)

comments['created_utc'] = pd.to_datetime(comments['created_utc'], unit='s')


"""
CLEANING THE DATAFRAMES
"""


#checks for deleted comments 
deleted_comments = comments[comments["body"] == "[deleted]"]
#print(deleted_comments.head())
print(f"There's {len(deleted_comments)} deleted comments in the comments dataset.")
#print(len(comments))

removed_comments = comments[comments["body"] == "[removed]"]
#print(removed_comments.head())
print(f" There's {len(removed_comments)} removed comments in the comments dataset.")

#the comments variable is now without any deleted comments
comments = comments[comments["body"] != "[deleted]"]
comments = comments[comments["body"] != "[removed]"]


#we verify if we have duplicates in the posts and comments

posts = posts.drop(columns=["comments"])
all_dups_p = posts[posts.duplicated(keep=False)] #keep False to mark all of the occurences of a duplicate
#print('Rows involved in duplicates in posts:', len(all_dups_p))

all_dups_c = comments[comments.duplicated(keep=False)] 
#print('Rows involved in duplicates in comments:', len(all_dups_c))


#regular expression to delete all the links and replace them by URL REMOVED 
comments['body'] = comments['body'].apply(   x: re.sub(r'(?:https?:\//|www\.)[^\s<>"\']+', "[URL_REMOVED]", x))
posts['selftext'] = posts['selftext'].apply(lambda x: re.sub(r'(?:https?:\//|www\.)[^\s<>"\']+', "[URL_REMOVED]", x))


#comments whitout the ones containing only urls 
comments = comments[comments["body"] !="[URL_REMOVED]"]


comments = comments.reset_index(drop=True)

comments.sample(10)


"""
CREATING CSV FILE

"""


text = pd.concat([posts["title"], posts["selftext"], comments["body"]], ignore_index=True) # creates a DataFrame that only contains the text bearing columns

text.to_csv("data.csv", index=False, header=["text"], encoding="utf-8") # turns the text DataFrame into a csv file