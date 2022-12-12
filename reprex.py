# -*- coding: utf-8 -*-
# Python 3.9
# Environment: emoji-weather
import os
from mastodon import Mastodon
    
if __name__ == "__main__":
   
    MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")
    MASTODON_URL = "https://tooting.ch"
    print(type(MASTODON_ACCESS_TOKEN))
    print(MASTODON_ACCESS_TOKEN)
    masto = Mastodon(api_base_url = MASTODON_URL, access_token = MASTODON_ACCESS_TOKEN)
    masto.toot("This is a test!")