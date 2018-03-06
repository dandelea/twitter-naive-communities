# Twitter naive data extraction for social communities

This is my master's project in 2016/2017. It consist in a scrapper, a text-processing module and a face-recognition api. Its main objective is to extract useful data from a large social community and be able to classify them. It can provide with information about the main social influencers of a semantic group.

The target field of this test group is 'Spain Videogames Journalists & Influencers', consisting in two vloggers: [Pazos64](https://twitter.com/pazos_64) and [JinoGamerHC](https://twitter.com/jinogamerhc).

## Getting Started
### Prerequisites

```
./install.sh
```
or... do the following:

#### Python3 & Friends
```
sudo apt-get install python3 python3-pip python3-numpy python-lxml python3-scipy python3-pandas build-essential gfortran libatlas-base-dev
```

#### MongoDB
[Installaton Instructions](https://docs.mongodb.com/manual/installation/)

#### Python library dependencies
* [Pymongo](https://api.mongodb.com/python/current/) for database connection.
* [NLTK](https://www.nltk.org/) for text processing.
* [AngusSDK](https://github.com/angus-ai/angus-sdk-python) for face data extraction.
* [Gensim](https://radimrehurek.com/gensim/) for topic extraction.
* [Tweepy](http://www.tweepy.org/) for TwitterAPI connection.
* [Scikit Learn](http://scikit-learn.org/stable/) for text processing (TFIDF vectorization and naive-bayes classifier).
* [Flask](http://flask.pocoo.org/) for a minimal server to a web app.
* [LXML](http://lxml.de/) for miminal XML parsing.

```
sudo pip install -r pip-requirements.txt
```

### Installation
* Angus.ai
  * Create an account at the [angus.ai](https://www.angus.ai/) site.
  * Register a stream app. Default gateway, copy & paste client_id and access_token.
    * `angusme` 
* NLTK Download dependencies
  * `python3`
  * `import nltk`
  * `nltk.download()`
  * Download *_punkt*, *sentiwordnet*, *snowball_data*, *stopwords* and *words*.
* Keys and passwords in [keys.py](keys.py). Follow the structured maps.
* Configuration parameters in [config.py](config.py).
  
### Run scrapping
```
python3 manage.py bot
```

### Restoring the database
```
python3 manage.py restore
```

It creates a clean local database on MongoDB.

### Run server
```
python3 manage.py runserver
```

## Logs
Logs are rotated and stored at `info.log`.

## Author
Daniel de los Reyes Leal

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Hat tip to anyone who's code was used.
* People who encouraged me on working at what I loved.
* A quick shoutout to [Strongman Tarrako](https://www.youtube.com/user/StrongmanTarrako)
* Espetos.