from botmodule import botmodule 
import discord
import logging
import asyncio
import io

from akinator.async_aki import Akinator
from akinator import AkiNoQuestions
import akinator
import asyncio


class moduleClass(botmodule):
	def default_config(self):
		return {'question_limit': 30}

	async def on_ready(self, client, config):
		self.aki = Akinator()
		self.game_intro = False
		self.game_running = False
		self.guessing = False
		self.current_channel = 0
		self.last_guess = None
		self.question_count = 0 

	async def on_message(self, client, config, message):
		if (not message.author.id == client.user.id):
			cmd = client.get_cmd(message)
			if cmd:
				if cmd["cmd"] == "akinator":
					if (not self.game_running) and (not self.game_intro):
						self.game_intro = True
						await message.channel.send("Starting new akinator game.")
						self.current_channel = message.channel.id
						await message.channel.send("Are you thinking of a (C)haracter/(P)erson, an (A)nimal, or an (O)bject?")
					else:
						await message.channel.send("Akinator game is already running, use >quitaki to restart")
				if cmd["cmd"] == "quitaki":
					if (self.game_running or self.game_intro):
						await message.channel.send("Quitting current game.")
						self.game_intro=False
						self.game_running=False
						self.current_channel = 0
						self.guessing = False
						self.last_guess = None
						self.question_count = 0 
						await self.aki.close()
					else:
						await message.channel.send("No game running, start with >akinator.")
			else:
				input = message.content.lower()
				if self.game_running and (message.channel.id == self.current_channel):
					if self.guessing:
						if (input == "y") or (input == "yes"):
							await message.channel.send("I win! Try again with >akinator.") #too lazy to figure out how to get command prefix rn
							self.game_intro=False
							self.game_running=False
							self.current_channel = 0
							self.guessing = False
							self.last_guess = None
							self.question_count = 0 
							await self.aki.close()
						elif (input == "n") or (input == "no"):
							if self.aki.progression >= 90 or (self.question_count > config['question_limit']):
								await message.channel.send("Alright you win, play again with >akinator.") #too lazy to figure out how to get command prefix rn
								self.game_intro=False
								self.game_running=False
								self.guessing = False
								self.current_channel = 0
								self.last_guess = None
								self.question_count = 0 
								await self.aki.close()
							else:
								self.guessing = False
								await message.channel.send(self.aki.question)
								self.question_count += 1
					else:
						answer = None
						if (input == "y") or (input == "yes"):
							answer = 'yes'
						elif (input == "n") or (input == "no"):
							answer = 'no'
						elif (input == "i") or (input == "idk"):
							answer = 'i'
						elif (input == "probably") or (input == "p"):
							answer = 'probably'
						elif (input == "maybe") or (input == "m"):
							answer = 'probably not'
						if answer:
							async with message.channel.typing():
								try:
									await self.aki.answer(answer)
									if self.aki.progression >= 80:
										candidate = await self.aki.win()
										if candidate['name'] != self.last_guess:
											self.guessing = True
											await message.channel.send("I think you are thinking of: ")
											await message.channel.send(candidate['name'])
											await message.channel.send(candidate['description'])
											await message.channel.send(candidate['absolute_picture_path'])
											self.last_guess = candidate['name']
											await message.channel.send("Am I right? yes/no")
									else:
										await message.channel.send(self.aki.question)
										self.question_count += 1
								except AkiNoQuestions:
									self.guessing = True
									await message.channel.send("I think you are thinking of: ")
									await message.channel.send(candidate['name'])
									await message.channel.send(candidate['description'])
									await message.channel.send(candidate['absolute_picture_path'])
									self.last_guess = candidate['name']
									await message.channel.send("Am I right? yes/no")
				if self.game_intro:
					game_mode = None
					if (input == "c") or (input == "p"):
						game_mode = 'en'
					elif (input == "a"): 
						game_mode = 'en_animals'
					elif (input == "o"):
						game_mode = 'en_objects'
					if game_mode:
						async with message.channel.typing():
							await self.aki.start_game(language=game_mode)
							self.game_running=True
							self.game_intro=False
							await message.channel.send(self.aki.question)
							self.question_count += 1
							await message.channel.send("Answer with (Y)es, (N)o, (I)DK, (P)robably, (M)aybe")