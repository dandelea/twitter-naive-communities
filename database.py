import json, pymongo, datetime

class Database:

	def __init__(self, schema = "twitter"):
		self.schema = schema
		self.client = None
		self.database = None
		self.closed = True

	def connect(self):
		self.client = pymongo.MongoClient()
		self.database = self.client[self.schema]
		self.closed = False
	
	def drop(self):
		if not self.closed:
			self.client.drop_database(self.schema)
	clear = drop

	def close(self):
		if not self.closed:
			self.client.close()
			self.closed = True
	disconnect = close

	""" QUERIES """

	""" Seeds """

	def find_seed_by_screen_name(self, screen_name):
		self.connect()
		result = self.database.twitter_seeds.find_one({'screen_name' : screen_name})
		self.close()
		return result

	def find_seed_by_id(self, seed_id):
		self.connect()
		result = self.database.twitter_seeds.find_one({'id' : seed_id})
		self.close()
		return result

	def active_hours(self, seed_id):
		self.connect()
		result = self.database.twitter_seeds.find_one({'id' : seed_id})
		self.close()
		return result['followers_hours']

	""" Users """

	def find_user_by_id(self, user_id):
		self.connect()
		result = self.database.twitter_users.find_one({'id': user_id})
		self.close()
		return result

	def highest_ratio_by_seed(self, seed_id):
		self.connect()
		result = list(self.database.twitter_users.find({'seeds': seed_id},
			{'_id':0, 'created_at': 0, 'friends': 0, 'hours': 0, 'seeds': 0}).sort('ratio',-1).limit(100))
		self.close()
		return result

	def gender_proportion(self, seed_id):
		self.connect()
		db_result = list(self.database.twitter_users.aggregate([
			{ '$unwind' : '$gender'},
			{ '$group' : { '_id' : '$gender', 'count' : { '$sum' : 1} } }]
		))
		total = self.database.twitter_users.count({'gender': {'$ne': None}})
		self.close()
		result = {'total' : total}
		for group in db_result:
			result[group['_id']] = group['count']

		return result

	def age_proportion(self, seed_id):
		ages = [13, 18, 25, 30, 35, 40, 45, 50, 60, 65]
		result = [None for _ in range(len(ages))]
		self.connect()
		for i, age in enumerate(ages):
			if i==len(ages)-1:
				count = self.database.twitter_users.count({'seeds': seed_id, 'age' : {'$gte' : age}})
				result[i] = {'min': age, 'count' : count}
			else:
				count = self.database.twitter_users.count({'seeds': seed_id, 'age' : {'$gte' : age, '$lt' : ages[i+1]}})
				result[i] = {'min': age, 'max': ages[i+1], 'count' : count}
		total = self.database.twitter_users.count({'seeds': seed_id, 'age' : {'$ne' : None}})
		self.close()
		return {'total' : total, 'count' : result}

	def count_users_by_seed(self, seed_id):
		self.connect()
		result = self.database.twitter_users.count({'seeds': seed_id})
		self.close()
		return result

	def count_active_users_by_seed(self, seed_id):
		self.connect()
		result = self.database.twitter_users.count({'seeds': seed_id, 'active' : True})
		self.close()
		return result

	def is_active(self, user_id):
		user = find_user_by_id(user_id)
		result = user!=None
		if result:
			result = result['active']
		return result

	## Influencers ##

	def main_influencers(self):
		result = []
		self.connect()
		result = list(self.database.twitter_influencers.find({}, {'_id': 0}).sort([('value', -1)]))
		self.close()
		return result

	## Topics

	def find_topic(self, name):
		self.connect()
		result = self.database.twitter_topics.find_one({'name': name}, {'_id': 0})
		self.close()
		return result