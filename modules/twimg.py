from botmodule import botmodule 
import time
import twitter
import sys
import discord
from urllib.parse import urlparse
from twitter import *
import datetime
import re
import logging
import json

def tweet_id(value):
	query = urlparse(value)
	if query.hostname in ('www.twitter.com', 'twitter.com'):
		try:
			if query.path.split('/')[2] == 'status':
				return query.path.split('/')[3]
		except:
			return None
	# fail?
	return None

class moduleClass(botmodule):
	def default_config(self):
		return {"access_token": "",
		"access_secret": "",
		"consumer_secret": "",
		"consumer_key": "",
		"twitter_name": "",
		"img_preview": False}

	def on_init(self):
		self.logger = logging.getLogger("jambot.twimg")	

	async def post_images(self, client, config, message, status):
		#print(json.dumps(status))
		if "extended_entities" in status:
			for img in status["extended_entities"]["media"][1:]:
				await message.channel.send(img["media_url_https"])

	async def on_message(self, client, config, message):
		links = re.findall(r'(https?://\S+)', message.clean_content)
		try:
			for link in links:
				if 'twitter' in link:
					tweetId = tweet_id(link)
					t = Twitter(auth=OAuth(config["access_token"], config["access_secret"], config["consumer_key"], config["consumer_secret"]))
					status = t.statuses.show(id=tweetId, tweet_mode='extended')
					if config["img_preview"]:
						await self.post_images(client, config, message, status)
					if "quoted_status_permalink" in status:
						await message.channel.send(status["quoted_status_permalink"]["expanded"])
		except:
			for error in sys.exc_info():
				print(str(error))
			pass