import pymongo

class Database:
    """
    Manages the MongoDB connection
    """

    def __init__(self, schema="twitter"):
        self.schema = schema
        self.client = None
        self.database = None
        self.closed = True

    def connect(self):
        """
        Opens a connection.
        Dumps the 'client' and 'database' variales.
        """
        self.client = pymongo.MongoClient()
        self.database = self.client[self.schema]
        self.closed = False

    def drop(self):
        """
        Clear the database.
        Alias: clear()
        """
        if not self.closed:
            self.client.drop_database(self.schema)
    clear = drop

    def close(self):
        """
        Close the current connection.
        Alias: disconnect()
        """
        if not self.closed:
            self.client.close()
            self.closed = True
    disconnect = close

    """ QUERIES """

    """ Seeds """

    def find_seed_by_screen_name(self, screen_name):
        """
        Finds 'twitter_seeds' by 'screen_name'.
        """
        self.connect()
        result = self.database.twitter_seeds.find_one({'screen_name' : screen_name})
        self.close()
        return result

    def find_seed_by_id(self, seed_id):
        """
        Finds 'twitter_seeds' by 'id'.
        """
        self.connect()
        result = self.database.twitter_seeds.find_one({'id' : seed_id})
        self.close()
        return result

    def active_hours(self, seed_id):
        """
        Get 'followers_hours' from 'twitter_seeds' where 'id'.
        """
        self.connect()
        result = self.database.twitter_seeds.find_one({'id' : seed_id})
        self.close()
        return result['followers_hours']

    """ Users """

    def find_user_by_id(self, user_id):
        """
        Finds 'twitter_users' by 'id'.
        """
        self.connect()
        result = self.database.twitter_users.find_one({'id': user_id})
        self.close()
        return result

    def highest_ratio_by_seed(self, seed_id):
        """
        Get 'twitter_users' with highest 'ratio' where 'seeds'.
        """
        self.connect()
        result = list(self.database.twitter_users.find(
            {'seeds': seed_id},
            {'_id':0, 'created_at': 0, 'friends': 0, 'hours': 0, 'seeds': 0}
        ).sort('ratio', -1).limit(100))
        self.close()
        return result

    def gender_proportion(self):
        """
        Calculates gender proportion from 'twitter_users'.
        Example result: {'total': X, 'female': X, 'male': X}
        """
        self.connect()
        db_result = list(self.database.twitter_users.aggregate([
            {'$unwind' : '$gender'},
            {'$group' : {'_id' : '$gender', 'count' : {'$sum' : 1}}}
        ]))
        total = self.database.twitter_users.count({'gender': {'$ne': None}})
        self.close()
        result = {'total' : total}
        for group in db_result:
            result[group['_id']] = group['count']

        return result

    def age_proportion(self, seed_id):
        """
        Calculates age proportion from 'twitter_users' where 'seeds'.
        Example result: {'total': X, 'count': [{'min': X, 'max': X, 'count': X}]}
        """
        ages = [13, 18, 25, 30, 35, 40, 45, 50, 60, 65]
        result = [None for _ in range(len(ages))]
        self.connect()
        for i, age in enumerate(ages):
            if i == len(ages)-1:
                count = self.database.twitter_users.count(
                    {'seeds': seed_id, 'age' : {'$gte' : age}}
                )
                result[i] = {'min': age, 'count' : count}
            else:
                count = self.database.twitter_users.count(
                    {'seeds': seed_id, 'age' : {'$gte' : age, '$lt' : ages[i+1]}}
                )
                result[i] = {'min': age, 'max': ages[i+1], 'count' : count}
        total = self.database.twitter_users.count({'seeds': seed_id, 'age' : {'$ne' : None}})
        self.close()
        return {'total' : total, 'count' : result}

    def count_users_by_seed(self, seed_id):
        """
        Counts 'twitter_users' where 'seeds'.
        """
        self.connect()
        result = self.database.twitter_users.count({'seeds': seed_id})
        self.close()
        return result

    def count_active_users_by_seed(self, seed_id):
        """
        Counts 'twitter_users' where 'seeds' and 'active' = True.
        """
        self.connect()
        result = self.database.twitter_users.count({'seeds': seed_id, 'active' : True})
        self.close()
        return result

    def is_active(self, user_id):
        """
        Find 'active' from 'twitter_users' where 'id'.
        Returns None if not found.
        """
        user = self.find_user_by_id(user_id)
        result = user != None
        if result:
            result = result['active']
        return result

    ## Influencers ##

    def main_influencers(self):
        """
        Get 'twitter_influencers' order by 'value' desc.
        """
        result = []
        self.connect()
        result = list(self.database.twitter_influencers.find({}, {'_id': 0}).sort([('value', -1)]))
        self.close()
        return result

    ## Topics

    def find_topic(self, name):
        """
        Get 'twitter_topics' where 'name'.
        """
        self.connect()
        result = self.database.twitter_topics.find_one({'name': name}, {'_id': 0})
        self.close()
        return result
