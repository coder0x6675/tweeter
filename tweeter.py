#!/usr/bin/env python
# A mastodon/twitter bot framework able to post tweets automatically using ChatGPT.


import re
import os
import sys
import time
import random

import dotenv
import openai
import mastodon
import tweepy

dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
dotenv.load_dotenv(dotenv_path)
OPENAI_API_KEY              = os.environ.get("OPENAI_API_KEY")
MASTODON_API_BASE_URL       = os.environ.get("MASTODON_API_BASE_URL")
MASTODON_CLIENT_SECRET      = os.environ.get("MASTODON_CLIENT_SECRET")
MASTODON_ACCESS_TOKEN       = os.environ.get("MASTODON_ACCESS_TOKEN")
TWITTER_BEARER_TOKEN        = os.environ.get("TWITTER_BEARER_TOKEN")
TWITTER_CONSUMER_KEY        = os.environ.get("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET     = os.environ.get("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN        = os.environ.get("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.environ.get("TWITTER_ACCESS_TOKEN_SECRET")

openai.api_key = OPENAI_API_KEY


# 2: Exit before generating tweets.
# 1: Exit before posting tweets.
# 0: Run the full program.
DEBUG = 0

SYSTEM_FILE = "./system.txt"
TOPIC_DIRECTORY = "./topics"
LENGTH_LIMITS = {
    "mastodon": 500,
    "twitter": 280,
}


def parse_topics(text):
    """Parses lines into descriptions and links"""
    topics = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("|"):
            topics[-1][1].append( line.removeprefix("|").strip() )
        else:
            topics.append( (line, []) )
    return topics


def get_prompt(type, description):
    """Takes a type of topic and a description and creates a full ChatGPT prompt from it"""
    n = "n" if type[0] in "aeiou" else ""
    prompt = f"Write a{n} {type} tweet {description}"
    return prompt


def format_text(text):
    """Removes formatting errors from a string"""
    text = text.encode("ascii", errors="ignore").decode() # Delete non-ascii characters
    text = text.strip().strip("'\"").strip()              # Delete surrounding quotes
    text = re.sub("  +", ". ", text)                      # Assume consecutive spaces was originally a dot
    text = re.sub(" ([,.;:!?])", r"\1", text)             # Delete spaces before punctuation
    text = re.sub("([,.;:!?])[,.;:!?]+", r"\1", text)     # Delete repeated punctuations
    text = " ".join(text.split())                         # Delete duplicate whitespaces
    return text


def length_to_tokens(length_in_characters):
    """Estimates ChatGPT tokens based on the given text length"""
    AVERAGE_LETTERS_PER_WORD = 6
    WORD_TO_TOKEN_RATIO = 1.3 # 1 word ~ 1.3 tokens
    BUFFER = 20
    length_in_words = length_in_characters / AVERAGE_LETTERS_PER_WORD
    tokens = length_in_words * WORD_TO_TOKEN_RATIO
    return int(round(tokens + BUFFER))


def ask_chatgpt(prompt, length, temperature=1, system="You are a helpful assistant."):
    """Asks a question of ChatGPT"""
    completion = openai.ChatCompletion.create(
        model       = "gpt-3.5-turbo",
        messages    = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        max_tokens  = length_to_tokens(length),
        temperature = temperature,
    )
    response = completion.choices[0].message.content
    return response


def shorten_text(text, length):
    """Shortens a given text using ChatGPT"""
    system = "Your task is to shorten the given texts while retaining the most important parts."
    completion = openai.ChatCompletion.create(
        model    = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        max_tokens  = length_to_tokens(length),
    )
    response = completion.choices[0].message.content
    return response


def mastodon_post(text):
    """Posts the given text to Mastodon"""
    mastodon_instance = mastodon.Mastodon(
        api_base_url  = MASTODON_API_BASE_URL,
        client_secret = MASTODON_CLIENT_SECRET,
        access_token  = MASTODON_ACCESS_TOKEN,
    )
    mastodon_instance.status_post(text)


def twitter_post(text):
    """Posts the given text to Twitter"""
    twitter_instance = tweepy.Client(
        bearer_token        = TWITTER_BEARER_TOKEN,
        consumer_key        = TWITTER_CONSUMER_KEY,
        consumer_secret     = TWITTER_CONSUMER_SECRET,
        access_token        = TWITTER_ACCESS_TOKEN,
        access_token_secret = TWITTER_ACCESS_TOKEN_SECRET,
    )
    twitter_instance.create_tweet(text=text)


def main():

    # Load the ChatGPT system profile
    with open(SYSTEM_FILE, "r") as file:
        system = file.read()

    # Select a random topic type
    pattern = re.compile(r"\d+-\w+")
    files = [file for file in os.listdir(TOPIC_DIRECTORY) if re.fullmatch(pattern, file)]
    if not files:
        print("Warning: No topic files found.")
        sys.exit(0)

    weights = []
    topics = []
    for file in files:
        split = file.split("-")
        weights.append(int(split[0]))
        topics.append(split[1])

    index = random.choices(range(len(files)), weights=weights, k=1)[0]
    topic_type = topics[index]

    # Select a random topic of that type
    topics_file = os.path.join(TOPIC_DIRECTORY, f"{files[index]}")
    with open(topics_file, "r") as file:
        topics = parse_topics(file.read())
    topic, links = random.choice(topics)

    # Generate the base tweet
    if DEBUG > 1:
        sys.exit(0)
    prompt = get_prompt(topic_type, topic)
    link = "\n"+random.choice(links) if links else ""
    print(f"Prompt: '{prompt}'")
    text_limit = min(LENGTH_LIMITS.values())
    tweet = ask_chatgpt(prompt, length=text_limit, temperature=1.3, system=system)

    # Generate the mastodon tweet
    mastodon_tweet = tweet
    while len(mastodon_tweet + link) > LENGTH_LIMITS["mastodon"]:
        print("Warning: Tweet too long, shortening...")
        mastodon_tweet = shorten_text(mastodon_tweet, length=text_limit)
    print(f"Response: {mastodon_tweet}")
    mastodon_tweet = format_text(mastodon_tweet)
    tweet = mastodon_tweet
    mastodon_tweet += link
    print(f"Mastodon tweet ({len(tweet)}): '{tweet}'")

    # Generate the twitter tweet
    twitter_tweet = tweet
    while len(twitter_tweet + link) > LENGTH_LIMITS["twitter"]:
        print("Warning: Tweet too long, shortening...")
        twitter_tweet = shorten_text(twitter_tweet, length=text_limit)
    twitter_tweet = format_text(twitter_tweet)
    tweet = twitter_tweet
    twitter_tweet += link
    print(f"Twitter tweet ({len(tweet)}): '{tweet}'")

    # Post the tweet
    if DEBUG > 0:
        sys.exit(0)
    mastodon_post(mastodon_tweet)
    time.sleep(60 + random.uniform(0, 840))
    twitter_post(twitter_tweet)


if __name__ == "__main__":
    main()


