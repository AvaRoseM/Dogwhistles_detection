import json
import praw
import os
from dotenv import load_dotenv

load_dotenv()

reddit = praw.Reddit(
    client_id = os.getenv('client_id'),
    client_secret = os.getenv('client_secret'),
    user_agent = os.getenv('user_agent'),
)

sub = reddit.subreddit("WhitePeopleTwitter")

posts = {}

filters = [sub.new(limit=None), sub.hot(limit=None)] 
for t in ["year", "month", "week"]:
    filters.append(sub.top(time_filter=t, limit=None))

for filter in filters:
    for post in filter:
        posts[post.id] = post

with open("WhitePeopleTwitter_14_11.jsonl", "w", encoding="utf-8") as f:
    for post in posts.values():

        post.comments.replace_more(limit=None) #includes the comments hidden behind "read more" on Reddit

        comments = []
        for c in post.comments.list():
            comments.append({
                "id": c.id,
                "parent_id": c.parent_id,
                "body": c.body,
                "created_utc": c.created_utc,
                "score": c.score,
            })

        record = {
            "id": post.id,
            "title": post.title,
            "selftext": post.selftext,
            "created_utc": post.created_utc,
            "score": post.score,
            "comments": comments,
        }

        f.write(json.dumps(record, ensure_ascii=False) + "\n")