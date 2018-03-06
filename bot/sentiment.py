from nltk.corpus import stopwords

from pprint import pprint

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import ShuffleSplit, GridSearchCV

from xml.dom.minidom import parse

from .data import emojis, abbreviations, corpus
from .util import Tokenizer

import copy, numpy, os.path, pickle, random, time 

best_parametersPvsN = {
	"multinomialnaive__alpha": 0.2,
	"tfidf__binary": True,
	"tfidf__max_df": 0.8,
	"tfidf__ngram_range": (1, 1),
	"tfidf__smooth_idf": True,
	"tfidf__sublinear_tf": False,
	"tfidf__tokenizer": Tokenizer('spanish'),
	"tfidf__use_idf": False
}

best_parametersSvsNS = {
	"multinomialnaive__alpha": 0.5,
	"tfidf__binary": True,
	"tfidf__max_df": 0.8,
	"tfidf__ngram_range": (1, 3),
	"tfidf__smooth_idf": True,
	"tfidf__sublinear_tf": True,
	"tfidf__tokenizer": Tokenizer('spanish'),
	"tfidf__use_idf": False
}

class Predictor:
	"""
	Works with two predictors:
		* First. Predicts if the tweet has/hasnt sentiment value.
		* Second. In case has sentiment, predicts Positive / Negative.
	"""

	def __init__(self, parametersPvsN=best_parametersPvsN, parametersSvsNS=best_parametersSvsNS,
		language = "spanish"):
		self.parametersPvsN = parametersPvsN
		self.parametersSvsNS = parametersSvsNS
		self.modelPvsN = None
		self.modelSvsNS = None
		self.tweets = corpus["tweets"]
		self.classifications = corpus["classifications"]
		self.trained = False
		

		index_shuf = list(range(len(self.tweets)))
		random.shuffle(index_shuf)

		tweets_shuf = [self.tweets[i] for i in index_shuf]
		class_shuf = [self.classifications[i] for i in index_shuf]

		self.tweets = numpy.array(tweets_shuf)
		self.classifications = numpy.array(class_shuf)

	def train(self, path="bot/data/trained_models.sav"):

		if os.path.exists(path):

			with open(path, "rb") as input_file:
				(self.modelSvsNS, self.modelPvsN) = pickle.load(input_file)
			self.trained = True

		else:

			tfidf1 = TfidfVectorizer(
				binary = self.parametersPvsN["tfidf__binary"],
				max_df = self.parametersPvsN["tfidf__max_df"],
				ngram_range = self.parametersPvsN["tfidf__ngram_range"],
				smooth_idf = self.parametersPvsN["tfidf__smooth_idf"],
				sublinear_tf = self.parametersPvsN["tfidf__sublinear_tf"],
				tokenizer = self.parametersPvsN["tfidf__tokenizer"],
				use_idf = self.parametersPvsN["tfidf__use_idf"])
				
			multinomibalnb1 = MultinomialNB(
				alpha = self.parametersPvsN["multinomialnaive__alpha"])

			self.modelPvsN = Pipeline([('tfidf', tfidf1),
						   ('multinomialnaive', multinomibalnb1)])

			tfidf2 = TfidfVectorizer(
				binary = self.parametersSvsNS["tfidf__binary"],
				max_df = self.parametersSvsNS["tfidf__max_df"],
				ngram_range = self.parametersSvsNS["tfidf__ngram_range"],
				smooth_idf = self.parametersSvsNS["tfidf__smooth_idf"],
				sublinear_tf = self.parametersSvsNS["tfidf__sublinear_tf"],
				tokenizer = self.parametersSvsNS["tfidf__tokenizer"],
				use_idf = self.parametersSvsNS["tfidf__use_idf"])

			multinomibalnb2 = MultinomialNB(
				alpha = self.parametersSvsNS["multinomialnaive__alpha"])

			self.modelSvsNS = Pipeline([('tfidf', tfidf2),
						   ('multinomialnaive', multinomibalnb2)])

			classificationsSvsNS = copy.deepcopy(self.classifications)
			classificationsSvsNS[numpy.where(classificationsSvsNS == 'P')[0]] = 'S'
			classificationsSvsNS[numpy.where(classificationsSvsNS == 'N')[0]] = 'S'
			classificationsSvsNS[numpy.where(classificationsSvsNS == 'NEU')[0]] = 'NS'

			neutral_indices = numpy.where(self.classifications == 'NEU')[0]
			tweetsPvsN = numpy.delete(self.tweets, neutral_indices)
			classificationsPvsN = numpy.delete(self.classifications, neutral_indices)

			self.modelPvsN.fit(tweetsPvsN, y=classificationsPvsN)
			self.modelSvsNS.fit(self.tweets, y=classificationsSvsNS)

			with open(path, "wb") as f:
				pickle.dump((self.modelSvsNS, self.modelPvsN), f)

			self.trained = True

	def predict(self, x):
		if self.trained:
			sentiment = self.modelSvsNS.predict([x])[0]
			if sentiment=="S":
				polarity = self.modelPvsN.predict([x])[0]
				return polarity
			else:
				return "NEU"

def calculate_best_parameters(tweets, classifications, language):
	'''
	Best:
	All at once
		Best score: 0.720
		Best parameters set:
		multinomialnaive__alpha: 0.1
		tfidf__binary: False
		tfidf__max_df: 0.8
		tfidf__ngram_range: (1, 3)
		tfidf__smooth_idf: False
		tfidf__sublinear_tf: True
		tfidf__tokenizer: <__main__.Tokenizer object at 0x7f1f9169a400>
		tfidf__use_idf: False


	Sentiment VS No-Sentiment
		Best score: 0.895
		Best parameters set:
		multinomialnaive__alpha: 0.5
		tfidf__binary: True
		tfidf__max_df: 0.8
		tfidf__ngram_range: (1, 3)
		tfidf__smooth_idf: True
		tfidf__sublinear_tf: True
		tfidf__tokenizer: <Tokenizer object at 0x7f64ac6295c0>
		tfidf__use_idf: False

	Positive VS Negative
		Best score: 0.811
		Best parameters set:
		multinomialnaive__alpha: 0.2
		tfidf__binary: True
		tfidf__max_df: 0.8
		tfidf__ngram_range: (1, 1)
		tfidf__smooth_idf: True
		tfidf__sublinear_tf: False
		tfidf__tokenizer: <Tokenizer object at 0x7f1ff4105da0>
		tfidf__use_idf: False
	'''

	tfidf = TfidfVectorizer(analyzer='word')
	multinomibalnb = MultinomialNB()

	model = Pipeline([('tfidf', tfidf),
				   ('multinomialnaive', multinomibalnb)])

	parameters = {
		'tfidf__ngram_range': [(1, 1), (1, 2), (1, 3)],
		'tfidf__max_df': [0.7, 0.8, 0.9, 1],
		'tfidf__smooth_idf': [True, False],
		'tfidf__use_idf': [True, False],
		'tfidf__sublinear_tf': [True, False],
		'tfidf__binary': [True, False],
		'tfidf__tokenizer': [Tokenizer(language)],
		'multinomialnaive__alpha': [0.001, 0.01, 0.05, 0.1, 0.2, 0.3, 0.5, 1]
	}

	grid_search = GridSearchCV(model, parameters, n_jobs=4, verbose=0, cv=ShuffleSplit(tweets.size))

	print("%d documents" % len(tweets))
	print()
	
	print("Performing grid search...")
	print("pipeline:", [name for name, _ in model.steps])
	print("parameters:")
	pprint(parameters)
	t0 = time.time()
	grid_search.fit(tweets, classifications)
	print("done in %0.3fs" % (time.time() - t0))
	print()
	
	print("Best score: %0.3f" % grid_search.best_score_)
	print("Best parameters set:")
	best_parameters = grid_search.best_estimator_.get_params()
	for param_name in sorted(parameters.keys()):
		print("\t%s: %r" % (param_name, best_parameters[param_name]))
	print("--------------------------------------------------------")
	print()