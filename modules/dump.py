from botmodule import botmodule 
import time
import discord
import datetime
import logging

class moduleClass(botmodule):
	def default_config(self):
		return {"fileprefix": "dump",
		"userprefix": True,
		"timeprefix": True}

	def on_init(self):
		self.logger = logging.getLogger("jambot.dump")

	def write_line(self, config, f, msg):
		timestamp = string(msg.created_at + ": ") if config["timeprefix"] else ""
		usertag = string(author.discriminator + ": ") if config["userprefix"] else ""
		f.write(timestamp + usertag + msg.clean_content)
		

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			command = cmd["cmd"]
			args = cmd["args"]
			admin = cmd["admin"]
			if isinstance(message.channel, discord.DMChannel) and admin and command=="dump":
				if len(args) != 1:
					await message.channel.send("Need channel id")
				else:
					channel = discord.utils.get(client.get_all_channels(), id=int(args[0]))
					timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y%m%d%H%M%S')
					f = file(config["fileprefix"] + "-" + channel.guild.name + "-" + channel.name + "-" + timestamp + ".log", "w")
					logging.info("Dumping..." + args[0])
					linecount = 0
					async for histm in channel.history():
						self.write_line(config, f, histm)
						linecount += 1
						if ((linecount%1000)==0):
							logging.info(str(linecount/1000).split(".")[0] + "k lines")
					logging.info("Dumped" + linecount + "lines")
