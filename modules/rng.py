from botmodule import botmodule 
import discord
import random

class moduleClass(botmodule):
	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			command = cmd["cmd"]
			args = cmd["args"]
			if  (command == "r")or(command == "random")or(command == "roll"):
				if not args:
					await message.channel.send("One number to roll up to or two to roll in between")
				elif len(args) == 1:
					try:
						await message.channel.send(str(random.randint(1, int(args[0]))))
					except:
						await message.channel.send("That's not a number")
				elif len(args) == 2:
					try:
						await message.channel.send(str(random.randint(int(args[0]), int(args[1]))))
					except:
						await message.channel.send("Those aren't numbers")
			elif (command == "choose") and len(args)>1:
				try:
					choice = random.randint(0, len(args)-1)
					await message.channel.send(args[choice])
				except:
					await message.channel.send("Couldn't choose for some reason")
			elif (command == "shuffle") and len(args)>1:
				try:
					random.shuffle(args)
					await message.channel.send(" ".join(args))
				except:
					await message.channel.send("Couldn't shuffle for some reason")
