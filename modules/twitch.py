from jambot import botmodule
#Twitch module
#Load in server context for access to member updates

class moduleClass(botmodule):
	def default_config(self):
		return {"announce_channel": 0, #bad gross wrong but im lazy
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.twitch")

	def get_stream(user):
		stream = None
		if "activities" in user:
			for act in user["activies"]:
				if isinstance(act, discord.ActivityType.Streaming):
					stream = act
		return stream

	async def on_member_update(self, client, config, before, after):
		was_streaming = get_stream(before)
		now_streaming = get_stream(after)
		if !was_streaming and now_streaming:
			channel = discord.utils.get(client.get_all_channels(), id=config["announce_channel"])
			channel.send(after.name + " is now streaming " + now_streaming.details + " at " + now_streaming.url)
