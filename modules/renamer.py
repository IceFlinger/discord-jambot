from botmodule import botmodule 
import time
import discord
import datetime
import random
import logging
import requests
from io import BytesIO

linkmatch = re.compile(r'(https?://\S+)')

class moduleClass(botmodule):
	def default_config(self):
		return {"localfolder": "/tmp",
		"webfolder": "http://localhost/"}

	def on_init(self):
		self.logger = logging.getLogger("jambot.renamer")

	def write_line(self, config, f, msg):
		timestamp = str(str(msg.created_at) + ": ") if config["timeprefix"] else ""
		usertag = str(msg.author.name + "#" + msg.author.discriminator + ": ") if config["userprefix"] else ""
		f.write(timestamp + usertag + msg.clean_content + "\n")		

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			command = cmd["cmd"]
			args = cmd["args"]
			admin = cmd["admin"]
			if admin and command=="getnames":
				users = []
				for user in message.guild.members:
					users.append(user)
				filename = str(time.now()) + ".txt"
				with open(config["localfolder"] + filename, 'w') as out:
  				  for user in users:
  				  	out.write(user.name + "#" + user.discriminator + "\n")
  				await message.channel.send(config["webfolder"] + filename)
			if admin and command=="setnames" and len(linkmatch.findall(args[0])) == 1:
				r = requests.get(args[0])
				setnames = {}
				randoms = []
				pool = []
				for name in r.content.split("\n"):
					if "#" in name:
						if ":" in name:
							setnames[name.split(":")[0]] = setnames[name.split(":")[1]]
						else:
							randoms.append(name)
					else:
						pool.append(name)
				if len(randoms) != len(pool):
					await message.channel.send("Mismatch between unassigned users/names")
				else:
					random.shuffle(pool)
					for random in randoms:
						setnames[random] = pool.pop()
				for username, nickname in setnames:
					user = discord.utils.get(message.guild.members, name=username.split("#")[0], discriminator=username.split("#")[1])
					await user.edit(nick=nickname)
				await message.channel.send("renamed users")