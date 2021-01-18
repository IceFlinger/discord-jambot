from botmodule import botmodule 
import discord


class moduleClass(botmodule):
	def on_init(self):
		self.bottom = 0

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if (self.bottom == message.channel.id) and (not message.author.id == client.user.id):
			await message.channel.send("─▲▲▲▲▲▲▲.▲.▄███████▄\n▀███████████████████")
			#await message.channel.send("▄███████▄.▲.▲▲▲▲▲▲▲\n███████████████████▀▀")
			#await message.channel.send("███████████████████▀▀")
			self.bottom = 0
		if cmd and not self.bottom:
			if cmd["cmd"] == "g8r":
				await message.channel.send("─────────▄█▀████▄▄\n─▄██████████████████▄\n▼▼▼▼.▼.▼.▼.▼.▼.▼.█████▄")
				#await message.channel.send("──────▄▄████▀█▄\n───▄██████████████████▄\n─▄█████.▼.▼.▼.▼.▼.▼.▼▼▼▼")
				#await message.channel.send("───▄██████████████████▄")
				#await message.channel.send("─▄█████.▼.▼.▼.▼.▼.▼.▼▼▼▼")
				self.bottom = message.channel.id

'''
──────▄▄████▀█▄
───▄██████████████████▄
─▄█████.▼.▼.▼.▼.▼.▼.▼▼▼▼
▄███████▄.▲.▲▲▲▲▲▲▲
███████████████████▀

─────────▄█▀████▄▄\n─▄██████████████████▄\n▼▼▼▼.▼.▼.▼.▼.▼.▼.█████▄
─────▲▲▲▲▲▲▲.▲.▄███████▄\n────▀███████████████████
'''
