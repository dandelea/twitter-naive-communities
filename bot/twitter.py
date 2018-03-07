import datetime
import time
import tweepy

class Connection:
    """
    Manages the connection with the Twitter API.
    """

    def __init__(self, accounts, user_fields, tweet_fields):
        self.accounts = accounts
        self.index = 0
        self.user_fields = user_fields
        self.tweet_fields = tweet_fields
        self.api = None

    def connect(self):
        """
        Activates a connection.
        """
        auth = tweepy.OAuthHandler(
            self.accounts[self.index]['consumer_key'],
            self.accounts[self.index]['consumer_secret']
        )
        auth.set_access_token(
            self.accounts[self.index]['access_token'],
            self.accounts[self.index]['access_token_secret']
        )
        self.api = tweepy.API(auth)

    def next(self):
        """
        Switchs to next twitter account.
        If got to the end, restart from the beginning.
        """
        if self.index == len(self.accounts)-1:
            self.index = 0
        else:
            self.index += 1
        print("Switch to account {0}".format(self.index))
        self.connect()

    def wait(self, api_family, api_url):
        """
        Check if has to wait for a specific endpoint.
        If the result is True, sleep.
        """
        copy_index = self.index
        while True:
            rate_limit_status = self.api.rate_limit_status()
            if rate_limit_status['resources'][api_family][api_url]['remaining'] == 0:
                self.next()
                if self.index == copy_index:
                    # Full circle
                    rate = self.api.rate_limit_status()['resources']
                    sleep_time = rate[api_family][api_url]['reset'] - int(time.time()) + 5
                    wakeup_date = datetime.datetime.now() + datetime.timedelta(seconds=sleep_time)
                    print("Sleeping until {0}".format(wakeup_date.strftime("%c")))
                    time.sleep(sleep_time)
                    break
            else:
                break
                