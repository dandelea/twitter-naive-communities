import angus, json, urllib.request, os.path, sys

class Connection:
	"""
	Manages the connection with the Angus.ai API.
	Predicts the age and gender from a profile image.
	The API can do a lot of other things.
	"""

	def __init__(self, accounts):
		self.accounts = accounts
		self.index = 0
		self.service = None
		self.age_confidence = 0.5
		self.gender_confidence = 0.5

	def next(self):
		"""
		Switchs to next account in line.
		"""
		if self.account_index == len(self.accounts) - 1:
			print("All Angus accounts tested with no success. Aborting...")
			sys.exit()
		else:
			self.account_index = self.account_index + 1
			self.connect()

	def connect(self):
		"""
		Activates a Angus.AI connection.
		"""
		default_file = os.path.realpath(os.path.expanduser("~/.angusdk/config.json"))
		with open(default_file) as file:
			json_data = json.load(file)
		json_data['client_id'] = self.accounts[self.index]['client_id']
		json_data['access_token'] = self.accounts[self.index]['access_token']
		with open(default_file, 'w') as file:
			json.dump(json_data, file)
		self.service = angus.client.connect().services.get_service('age_and_gender_estimation', version=1)

	def estimate(self, image_url):
		"""
		Returns age, gender tuple
		"""
		if self.service:
			try:
				url = urllib.request.urlopen(image_url)
			except:
				return None, None

			has_error = True
			while has_error:
				try:
					job = self.service.process({'image': url})
					has_error = False
				except:
					print("Angus failed to process the image. Next account...")
					self.next()

			result = job.result

			if not 'Error' in result and result['status']==201:
				if result['nb_faces']:
					face = result['faces'][0]
					age, gender = None, None
					if face['age_confidence'] > self.age_confidence:
						age = face['age']
						if age < 13:
							age = 13
					if face['gender_confidence'] > self.gender_confidence:
						gender = face['gender']
					return age, gender
				else:
					return None, None
			else:
				return None, None
		else:
			raise Exception("Angus.AI connection not set.")