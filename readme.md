# Tweeter

> A framework for automated Twitter/Mastodon promotion using LLMs.

This program will automate the process of generating marketable material using an LLM API, and craft a content to post to social platforms like Twitter and Mastodon. Enter the topics you want to generate material about in the topic-files (see [Usage](#Usage)), and the program will randomly select one to post about.

## Installation

Verify you have the required privileges, feel free to change anything you deem necessary. The following commands will install the program to `/srv`.

``` bash
cd /srv
git clone *REPO-URL*
cd tweeter
python -m venv venv
venv/bin/pip install -r requirements.txt
```

## Usage

Add the required OpenAI, Mastodon and Twitter API tokens to `.env`, and exclude it from version handling:

``` bash
git update-index --skip-worktree .env
chmod 600 .env
$EDITOR .env
```

Create at least one file in the *topics* directory. The name of the files should be `WEIGHT-TYPE`, where the `WEIGHT` is a whole number representing its likelihood of being picked, and the `TYPE` of the type of topics contained in that file. Do not use an extension. Here are a few examples of topic filenames:

- `topics/2-motivational`
- `topics/008-inspirational`
- `topics/1000-educational`

*Note:* Use a weight of 0 to effectively deactivate a topic.

Each line in a topic-file should contain a description of a topic you want to tweet about. As a guideline, each description should be a continuation of the sentance "Write a tweet...". Empty lines as well as initial or ending whitespaces are ignored. Lines beginning with '#' are treated as comments and are also ignored. Lines beginning with a '|' have special meaning and represents a link or URL that corresponds to the previously mentioned description. A link is optional, but if present it will be appended to the end of the tweet if that topic gets selected. Multiple links can be specified, in which case one will be picked randomly.

Here is an example of a topic file:

``` topics/educational.txt
# Write a tweet...

explaining how to search for articles online
    | https://google.com
    | https://duckduckgo.com
reminding my followers that my birthday is the 30th of february
announcing to the world that I'm using Arch Linux BTW
    | https://archlinux.org
```

Running the script will post a single tweet. Schedule the program to run periodically for continous posting. The systemd directory provides two pre-configured systemd unit files to achive this.

Optionally, the `system.txt` file can be changed to give the program a custom "personality" or writing style. Remember to exclude this file from version handling: `git update-index --skip-worktree system.txt`

Run the following commands to enable periodic posting. By default three posts will be uploaded at random times during the day.

``` bash
sudo cp systemd/tweeter.service /etc/systemd/system
sudo cp systemd/tweeter.timer /etc/systemd/system
sudo systemctl daemon-reload
sudo systemctl enable --now tweeter.timer
```

