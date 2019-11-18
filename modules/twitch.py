from botmodule import botmodule
import logging
import discord
#Twitch module
#Load in server context for access to member updates

class moduleClass(botmodule):
	def default_config(self):
		return {"announce_channel": 0, #bad gross wrong but im lazy
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.twitch")

	def get_stream(self, user):
		stream = None
		for act in user.activities:
			if isinstance(act, discord.Streaming):
				stream = act
		return stream

	async def on_member_update(self, client, config, before, after):
		was_streaming = self.get_stream(before)
		now_streaming = self.get_stream(after)
		if (not was_streaming) and now_streaming:
			channel = discord.utils.get(client.get_all_channels(), id=config["announce_channel"])
			channel.send(after.name + " is now streaming " + now_streaming.details + " at " + now_streaming.url)
