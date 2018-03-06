import datetime, heapq, json, operator, pymongo, tweepy
from .util import *
from .keys import angus as angus_keys
from .keys import twitter as twitter_keys

from config import *

from database import Database
from .twitter import Connection
from .faces import Connection as Faces
from .sentiment import Predictor


class Scrapbot:

	def __init__(self, connection, database, predictor, faces):
		self.connection = connection
		self.connection.connect()
		self.database = database
		self.predictor = predictor
		if not self.predictor.trained:
			self.predictor.train()
		self.faces = faces
		self.language = "spanish"
		self.topics = TOPICS

	def seeds(self):
		print("seeds...")

		while True:
			try:
				users = [user._json for user in list(self.connection.api.lookup_users(screen_names=SEEDS))]
				break
			except tweepy.error.RateLimitError:
				self.connection.wait(api_family='users', api_url='/users/lookup')
				# Continue While

		self.database.connect()
		self.database.database.twitter_seeds.drop()

		# Removes private users
		users = [user for user in users if not user['protected']]
		# Removes unwanted data
		copies = []
		for user in users:
			copy =  {}
			for key, value in user.items():
				if key in self.connection.user_fields:
					copy[key] = value
			copies.append(copy)
		users = copies
		# Add extra data
		for user in users:
			user['created_at'] = to_datetime(user['created_at'])
			user['ratio'] = user['followers_count']/max([1.0, user['friends_count']])
			user['seeds'] = []
			for user2 in users:
				if user['id'] != user2['id'] and self.connection.api.show_friendship(source_id=user["id"], target_id=user2['id'])[0].following:
					user['seeds'].append(user2['id'])

		self.database.database.twitter_seeds.insert_many(users)
		self.database.close()

	def timeline(self):
		print("timeline...")

		self.database.connect()
		self.database.database.tweets.drop()

		users = list(self.database.database.twitter_users.find())
		
		for i, user in enumerate(users):
			tweets = []
			while True:
				try:
					response = self.connection.api.user_timeline(user_id = user['id'], trim_user = True, count=100)
					response = [tweet._json for tweet in response]

					for tweet in response:
						"""
						Stores tweets from user
						"""
						tweet_copy = {}
						for attr in tweet.keys():
							if attr in self.connection.tweet_fields:
								tweet_copy[attr] = tweet[attr]

						tweet_copy["user_id"] = user["id"]
						tweet_copy['created_at'] = to_datetime(tweet_copy['created_at'])
						tweet_copy["sentiment"] = self.predictor.predict(text_from_tweet(tweet_copy['text'], tweet_copy['entities']))
						self.database.database.tweets.insert_one(tweet_copy)
						tweets.append(tweet_copy)

					if len(response):
						"""
						Marks user 'active'
						"""
						last_tweet = response[0]
						tweet_date = to_datetime(last_tweet['created_at'])
						today = datetime.datetime.today()
						threemonthsago = today - datetime.timedelta(days=30*3)
						user['active'] = tweet_date > threemonthsago
					else:
						user['active'] = False

					break
				except tweepy.error.RateLimitError:
					self.connection.wait(api_family = 'statuses', api_url = '/statuses/user_timeline')
					# Continues While
				except tweepy.error.TweepError:
					break

			if 'active' not in user:
				user['active'] = True
			
			self.database.database.twitter_users.update({'_id': user['_id']}, {'$set': {'hours': graph(tweets), 'active' : user['active']}})

			print("{0}/{1} = {2:.2f}%".format(i+1, len(users), (i+1)*100/len(users)), end="\r")
		
		hours_map = {}
		for seed in list(self.database.database.twitter_seeds.find()):
			hours_map[seed['id']] = empty_graph();
		for user in list(self.database.database.twitter_users.find()):
			u_seeds = user['seeds']
			for s in u_seeds:
				hours_map[s] = add_graph(hours_map[s], user['hours'])
		for seed, h in hours_map.items():
			self.database.database.twitter_seeds.update({'id': seed}, {'$set': {'followers_hours': h}})

		self.database.close()

	def followers(self):
		"""
		Generates a map {Key = user_id, Value = seed_id}
		"""
		print("followers...")

		self.database.connect()
		self.database.database.twitter_users.drop()
		seeds = list(self.database.database.twitter_seeds.find())
		self.database.close()

		"""
		We'll extend a list of lists of the seeds' followers_ids
		"""
		followers_ids = [[] for _ in range(len(seeds))]
		for i, seed in enumerate(seeds):
			print("Exploring followers of seed: {0}".format(seed['screen_name']))

			cursor = -1
			while True:
				try:
					response = self.connection.api.followers_ids(screen_name=seed['screen_name'], cursor=cursor)
					temp_ids = [str(id) for id in response[0]]
					if temp_ids:
						followers_ids[i].extend(temp_ids)
						cursor = response[1][1]
					else:
						break
				except tweepy.error.RateLimitError:
					self.connection.wait(api_family = 'followers', api_url = '/followers/ids')
					# Continue While
			
			print("{0}/{1} = {2:.2f}%".format(i+1, len(seeds), (i+1)*100/len(seeds)), end="\r")

		followers_map = {}
		for i, seed in enumerate(seeds):
			for follower_id in followers_ids[i]:
				if follower_id in followers_map:
					followers_map[follower_id].append(seed['id'])
				else:
					followers_map[follower_id] = [seed['id']]

		MAX_ARGUMENT_SIZE_PER_REQUEST = 100

		self.database.connect()
		self.faces.connect()

		N = len(followers_map)
		followers_ids = list(followers_map.keys())
		
		for i, page in enumerate(paginate(followers_ids, MAX_ARGUMENT_SIZE_PER_REQUEST)):
			while True:
				try:
					users = self.connection.api.lookup_users(user_ids=page)
					break
				except tweepy.error.RateLimitError:
					self.connection.api.wait(api_family = 'users', api_url = '/users/lookup')
					# Continue While

			# Removes private users
			users = [user._json for user in users if not user.protected]
			# Removes unwanted data
			copies = []
			for user in users:
				copy =  {}
				for key, value in user.items():
					if key in self.connection.user_fields:
						copy[key] = value
				copies.append(copy)
			users = copies
			# Add extra data
			for user in users:
				user['created_at'] = to_datetime(user['created_at'])
				user['ratio'] = user['followers_count']/max([1.0, user['friends_count']])
				user['seeds'] = followers_map[(str(user['id']))]
				user['active'] = not user['default_profile']
				if not user['default_profile_image']:
					user['age'], user['gender'] = self.faces.estimate(user['profile_image_url_https'].replace("_normal", ""))
				else:
					user['age'], user['gender'] = None, None

			self.database.database.twitter_users.insert_many(users)
			print("{0}/{1} = {2:.2f}%".format(i+1, len(users), (i+1)*100/len(users)), end="\r")
		
		self.database.close()
		
	def influencers(self):
		print("influencers...")

		N = 100

		self.database.connect()
		self.database.database.twitter_influencers.drop()
		self.database.database.twitter_users.update({}, {'$unset': {"friends": 1}}, multi=True)
		self.database.database.twitter_seeds.update({}, {'$unset': {"influencers": 1}}, multi=True)
		self.database.database.twitter_users.remove({'friends_count': {'$gt' : 5000}})

		seeds = list(self.database.database.twitter_seeds.find({}, {"id": 1, "screen_name" : 1}))

		result_map = {seed['id']: 0 for seed in seeds}

		for j, seed in enumerate(seeds):
			print("Seed {0}".format(seed['screen_name']))
			users = list(self.database.database.twitter_users.aggregate(
				[
				{"$match":
					{'seeds': seed['id']}
				},
				{"$project":
					{
					'_id': 0,
					'id': 1,
					'screen_name': 1,
					'friends_count': 1
					}
				},
				{'$sample':
					{'size': 5000}
				}
				]))

			influencers_map = {}
			for i, user in enumerate(users):

				if not "friends" in user:
					# if 'friends' not set yet
					# Lets query them
					# In other case, ignore.
			
					cursor = -1
					user_friends = []
					while True:
						try:
							response = self.connection.api.friends_ids(user_id = user['id'], cursor=cursor)
							user_friends.extend(response[0])

							if len(user_friends) == 0:
								self.database.database.twitter_users.remove({'id': user['id']})
								self.database.database.tweets.remove({'user_id': user['id']})
								break

							# Hotfix. Sometimes the users response is higher than the 'friends_count' value.
							if len(user_friends) >= user['friends_count'] - percentage(5, user['friends_count']):
								break
							else:
								cursor = response[1][1]
						except tweepy.error.RateLimitError:
							self.connection.wait(api_family = 'friends', api_url = '/friends/ids')
						except tweepy.error.TweepError:
							break

					user["friends"] = user_friends
					self.database.database.twitter_users.update_one({"id": user["id"]}, {'$set': {"friends": user["friends"]}})			

				for user_id in user["friends"]:
					if user_id in influencers_map:
						influencers_map[user_id] += 1
					else:
						influencers_map[user_id] = 1

				print("{0}/{1} = {2:.2f}%  seed: {3}/{4}".format(i+1, len(users), (i+1)*100/len(users), j+1, len(seeds)), end="\r")

			result_map[seed['id']] = heapq.nlargest(N, influencers_map.items(), key=operator.itemgetter(1))
			
		for i, seed in enumerate(result_map.keys()):

			influencers_ids = [influencer_id for influencer_id, value in result_map[seed]]
			self.database.database.twitter_seeds.update_one({'id': seed}, {'$set': {'influencers': influencers_ids}})
			
			remaining_influencers_ids = {}
			for influencer_id, value in result_map[seed]:
				user = self.database.database.twitter_users.find_one({'id': influencer_id})
				if user:
					del user['_id']
					user['value'] = value
					self.database.database.twitter_influencers.insert_one(user)
				else:
					remaining_influencers_ids.update({influencer_id: value})


			while True:
				try:
					result = self.connection.api.lookup_users(user_ids=remaining_influencers_ids.keys())
					break
				except tweepy.error.RateLimitError:
					self.connection.wait(api_family = 'users', api_url = '/users/lookup')
					# Continue While
			
			for user in result:
				result_copy = {}
				for key, value in user._json.items():
					if key in self.connection.user_fields:
						result_copy[key] = value
				result_copy['created_at'] = to_datetime(result_copy['created_at'])
				result_copy['value'] = remaining_influencers_ids[user._json['id']]
				self.database.database.twitter_influencers.insert_one(result_copy)

			print("{0}/{1} = {2:.2f}%".format(i+1, len(seeds), (i+1)*100/len(seeds)), end="\r")


		self.database.close()


	def sentiment_topics(self):
		print("topics...")
		self.database.connect()

		# Remove fields from twitter_users copy
		self.database.database.twitter_influencers.update({},
			{'$unset': {'age': 1, 'gender': 1, 'hours': 1, 'friends': 1, 'seeds': 1}}, multi=True)

		# Search index text
		self.database.database.tweets.create_index([('text', pymongo.TEXT)], name='search_index', default_language=self.language)
		self.database.database.twitter_topics.drop()

		amonthago = datetime.datetime.now() - datetime.timedelta(days=30)
		topics = []
		for topic in self.topics:
			result = {
				'NEU': 0,
				'P': 0,
				'N' : 0
			}
			tweets = self.database.database.tweets.find({'$text': {'$search': topic}, 'created_at': {'$gte': amonthago}}, {'sentiment': 1})
			for tweet in tweets:
				result[tweet['sentiment']] += 1
			topics.append({'name': topic, 'sentiment': result})
		self.database.database.twitter_topics.insert_many(topics)
		self.database.close()

class Extractor:

	def __init__(self, database):
		self.database = database

	def tweets_map(self, output='tweets_map.json'):
		geojson = {
			'type' : 'FeatureCollection',
			'features' : []
		}
		tweets = list(self.database.database.tweets.find())
		for user_id in [user['id'] for user in self.database.database.twitter_users.find({'active': True}, {'id': 1})]:
			if self.database.database.tweets.find_one({'user_id': user_id, 'place': {'$ne':null}}):

				example = {
					'type' : 'Feature',
					'geometry' : {},
					'properties' : {
						'created_at' : '',
						'text' : '',
						'user_id' : ''
					}
				}

				example['geometry'] = last_tweet['place']['bounding_box']
				example['properties']['created_at'] = last_tweet['created_at']
				example['properties']['text'] = last_tweet['text']
				example['properties']['user_id'] = user['id']
				geojson['features'].append(example)

		with open(output, 'w') as out:
			json.dump(geojson, out)


def run_bot():
	database = Database()
	connection = Connection(accounts = twitter_keys,
		user_fields = USER_FIELDS,
		tweet_fields = TWEET_FIELDS)
	faces = Faces(accounts = angus_keys)
	predictor = Predictor()
	bot = Scrapbot(connection = connection,
		database = database,
		predictor = predictor,
		faces = faces)
	bot.seeds()
	bot.followers()
	bot.influencers()
	bot.timeline()
	bot.sentiment_topics()
