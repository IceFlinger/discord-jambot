from jambot import botmodule
import sys
import requests
import asyncio
import time
#Twitch module
#Only announces streams if loaded in channel context

def lim_space(string, count):
	if string == None:
		string = "" #REALLY TWITCH
	if len(string) > count:
		return string[0:count-3] + "..."
	else:
		return string

class moduleClass(botmodule):

	def default_config(self):
		return {
		"table_id": "streams",
		"max_gamelength": 32,
		"max_statuslength": 48,
		"interval": 60
		"api_client_id": ""
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.twitch")

	def do_command(self, client, config, c, e, command, args, admin):
