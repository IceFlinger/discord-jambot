from botmodule import botmodule 

class moduleClass(botmodule):
	def default_config(self):
		return {
		"commands": ["ss", "screenshare"]
		}

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			command = cmd["cmd"]
			if command in config["commands"]:
				if message.author.voice:
					await message.channel.send("<https://www.discordapp.com/channels/" + str(message.author.voice.channel.guild.id) + "/" + str(message.author.voice.channel.id)+">")
				else:
					await message.channel.send("You are not in a voice channel")
