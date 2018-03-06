from nltk import word_tokenize
from nltk.stem import SnowballStemmer
from string import punctuation

import datetime, re, time

def strip_punctuation(s):
	"""
	Removes punctuation symbols from input text.
	"""
	return ''.join(c for c in s if c not in punctuation)

def percentage(percent, whole):
	"""
	Returns percentage value.
	"""
	return (percent * whole) / 100.0

def find_dict_with_key(my_list, key, value):
	try:
		index = [ x[key] for x in my_list ].index(value)
	except ValueError:
		index = -1
	return index

def paginate(mylist, slice_size):
	"""
	Paginates a list into a list of lists of input size.
	"""
	return [mylist[i:i+slice_size] for i in range(0, len(mylist), slice_size)]

def to_datetime(tweet_date):
	"""
	Translates Twitter style date.
	"""
	return datetime.datetime.fromtimestamp(time.mktime(time.strptime(tweet_date, '%a %b %d %H:%M:%S %z %Y')))

def text_from_tweet(tweet, entities):
	hashtags = entities['hashtags']
	symbols = entities['symbols']
	urls = entities['urls']
	user_mentions = entities['user_mentions']

	if 'media' in entities:
		media = entities['media']
		for m in media:
			tweet = tweet.replace(m['url'], "")
	for u in urls:
		tweet = tweet.replace(u['url'], "")
	for um in user_mentions:
		variations_username = [um['screen_name'], um['screen_name'].lower()]
		for username in variations_username:
			tweet = tweet.replace(username, "")
	for hs in hashtags:
		tweet = tweet.replace("#"+hs['text'], hs['text'])
	for s in symbols:
		tweet = tweet.replace("$"+s['text'], "")
	tweet = strip_punctuation(tweet)
	tweet = tweet.replace("…", "")
	tweet = tweet.strip()
	tweet = re.sub(" +"," ", tweet)
	if tweet.isspace():
		tweet = ""
	return tweet

def round_datetime(date):
	"""
	Converts a date into its 00-minute nearest hour. Returns a string.
	"""
	approx = round(date.minute/60.0) * 60
	date = date.replace(minute=0)
	date += datetime.timedelta(seconds=approx * 60)
	time = date.time()
	return time.strftime('%H:%M')

def count_hours(dates):
	"""
	Calculate a dict with key 00-minute hour and value count dates
	"""
	result = {}
	hs = ["{0}:00".format(str(i).zfill(2)) for i in range(24)]
	for h in hs:
		result[h] = 0;
	for date in dates:
		aux = round_datetime(date)
		result[aux] += 1
	return result

def empty_graph():
	return count_hours([])

def graph(tweets):
	dates = [tweet["created_at"] for tweet in tweets]
	result = count_hours(dates)
	return result

def add_graph(graph1, graph2):
	for key, value in graph2.items():
		graph1[key] += value;
	return graph1

class Tokenizer(object):
	def __init__(self, language):
		self.sbs = SnowballStemmer(language=language, ignore_stopwords=True)
		self.language = language
	def __call__(self, text):
		# Prevent punctuations ,.;... to occur in words
		text = "".join([ch for ch in text if ch not in punctuation])
		tokens = word_tokenize(text, language=self.language)
		stems = self.stem_tokens(tokens)
		return stems
	def stem_tokens(self, tokens):
		stemmed = []
		for item in tokens:
			stemmed.append(self.sbs.stem(item))
		return stemmed