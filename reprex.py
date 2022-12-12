# -*- coding: utf-8 -*-
# Python 3.9
# Environment: emoji-weather
import os
from mastodon import Mastodon
    
if __name__ == "__main__":
   
    MASTO_TEST_TOKEN = os.environ.get("MASTO_TEST_TOKEN")
    MASTODON_URL = "https://tooting.ch"
    print(type(MASTO_TEST_TOKEN))
    print(MASTO_TEST_TOKEN)
    masto = Mastodon(api_base_url = MASTODON_URL, access_token = MASTO_TEST_TOKEN)
    masto.toot("This is a test!")