# -*- coding: utf-8 -*-
# Python 3.9
# Environment: emoji-weather
import os
from mastodon import Mastodon
    
if __name__ == "__main__":
   
    MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_TOKEN_TEST_ACCOUNT")
    MASTODON_URL = "https://tooting.ch"

    masto = Mastodon(api_base_url = MASTODON_URL, access_token = MASTODON_ACCESS_TOKEN)
    masto.toot("This is a test!")