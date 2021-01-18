from botmodule import botmodule 
import discord
import logging
import requests


class moduleClass(botmodule):
	def on_init(self):
		self.logger = logging.getLogger("jambot.inspiro")

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			if cmd["cmd"] == "inspiro":
				r = requests.get("https://inspirobot.me/api?generate=true")
				await message.channel.send(str(r.text))
