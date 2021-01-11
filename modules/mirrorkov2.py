from botmodule import botmodule 
from random import choice
from io import BytesIO
import discord
import logging
import sys
import random
import re
import time
import string
import threading
from datetime import datetime, timedelta
from twitter import *
import math

#Markov chain jambot-discord module
#By ice at scrub club discord

mentionmatch = re.compile(r'^<@!?\d+>$')
linkmatch = re.compile(r'(https?://\S+)')

def mangle_line(line):
	links = linkmatch.findall(line) 
	#f = string.ascii_letters + string.digits + "():<>[].,!?/-^%$#@ "
	line = ' '.join(w for w in line.split() if w not in links) #Remove URLs
	line = ' '.join(w for w in line.split() if w[0] not in "[\"(") #Remove timestamp type stuff and quotes
	line = ' '.join(w for w in line.split() if w[-1] not in ";\"%") #Remove broken words
	#line = ' '.join(w for w in line.split() if not len(w)>35) #Remove long stuff
	#line = ''.join(c for c in line if c in f) #Filter whole string with f chars
	#logging.info(line)
	return line

class moduleClass(botmodule):
	def default_config(self):
		return {"replyrate":0.01,
		"learning":False,
		"maxchain":20,
		"sanity":50,
		"cooldown":2,
		"triggers": ["jambot"],
		"table_id": "jambot",
		"articles": ["<#sender>", "<#nick>", "<#@ping>", "you", "she", "he", "they"],
		"donttweet": [],
		"donttweet_swaps": [],
		"blacklist": [], #hacky bullshit
		"tweet_thres": 2,
		"tweet_delay": 60,
		"access_token": "",
		"access_secret": "",
		"consumer_secret": "",
		"consumer_key": "",
		"twitter_name": ""
		}

	def on_init(self):
		self.logger = logging.getLogger("jambot.mirrorkov2")
		self.tweeted = []
		self.composed = []
		self.tweet_timer = datetime.now()

	async def on_connect(self, client, config):
		self.tablename = "markov_" + config["table_id"]
		query = "CREATE TABLE IF NOT EXISTS " + self.tablename + " (word1 text DEFAULT '', word2 text DEFAULT '', word3 text DEFAULT '',\
		 freq int DEFAULT 0, user int, UNIQUE(word1, word2, word3, user))"
		await client.db_query(query)
		await client.db_commit()
		self.nickreply = False
		self.lastmsg = 0
		self.tweet_timer -= timedelta(seconds=config["tweet_delay"])

	def select_context(self, config, contexts):
		newpairs = {}
		for pair in contexts:
			key = (pair[0].lower(), pair[1].lower())
			if key in newpairs:
				newpairs[key] += pair[2]
			else:
				newpairs[key] = pair[2]
		#logging.info(newpairs)
		sort = sorted(newpairs, key=newpairs.get, reverse=True)
		for pair in sort:
			roll = random.randint(1,100)
			if roll <= config["sanity"]:
				return pair
		return sort[-1]

	async def single_word_contexts(self, client, config, word, userid):
		exist_contexts = []
		single_contexts = []
		results = await client.db_query("SELECT word1, word2, word3, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word1) LIKE LOWER(?)\
		 OR LOWER(word2) LIKE LOWER(?) OR LOWER(word3) LIKE LOWER(?)) GROUP BY word1, word2, word3 ORDER BY sum(mfreq) DESC", (userid, word, word, word))
		for context in results:
			single_contexts.append(context)
		for context in single_contexts:
			if context[0].lower() == word.lower() or context[1].lower() == word.lower():
				exist_contexts.append((context[0], context[1], context[3]))
			if context[1].lower() == word.lower() or context[2].lower() == word.lower():
				exist_contexts.append((context[1], context[2], context[3]))
		return exist_contexts

	async def build_sentence(self, client, config, message, sender, channel, userid):
		#logging.info("Building sentence")
		phrase = []
		try:
			#chainlength = 0
			exist_contexts = [] #look for words in the trigger sentence that we know already
			words = message.split()
			for word in range(len(words)):
				if (words[word].lower() in config["triggers"]) or mentionmatch.match(words[word]):
					words[word]="<@#mention>"
			if len(words) == 3 and words[0] == "<@#mention>":
				for context in await client.db_query("SELECT word1, word2, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word1) \
					LIKE LOWER(?) AND LOWER(word2) LIKE LOWER(?)) GROUP BY word1, word2 ORDER BY sum(mfreq)", (userid, words[1], words[2])):
					exist_contexts.append(context)
				for context in await client.db_query("SELECT word2, word3, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word2) \
					LIKE LOWER(?) AND LOWER(word3) LIKE LOWER(?)) GROUP BY word2, word3 ORDER BY sum(mfreq)", (userid, words[1], words[2])):
					exist_contexts.append(context)
				if len(exist_contexts) == 0: #we didn't find that exact pair's context, so check for each word individually
					exist_contexts+=await self.single_word_contexts(client, config, words[1], userid)
					exist_contexts+=await self.single_word_contexts(client, config, words[2], userid)
			elif len(words) == 2 and words[0] == "<@#mention>":
				exist_contexts+=await self.single_word_contexts(client, config, words[1], userid)
			else:
				for word1, word2 in zip(words[:-1], words[1:]):
					for context in await client.db_query("SELECT word1, word2, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word1)\
					 LIKE LOWER(?) AND LOWER(word2) LIKE LOWER(?)) GROUP BY word1, word2 ORDER BY sum(mfreq)", (userid, word1, word2)):
						exist_contexts.append(context)
					for context in await client.db_query("SELECT word2, word3, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word2)\
					 LIKE LOWER(?) AND LOWER(word3) LIKE LOWER(?)) GROUP BY word2, word3 ORDER BY sum(mfreq)", (userid, word1, word2)):
						exist_contexts.append(context)
			if len(exist_contexts) == 0:
				for word in words:
					if word != "<@#mention>":
						exist_contexts+=await self.single_word_contexts(client, config, word, userid)
			if exist_contexts:
				async with channel.typing():
					phrase_seed = self.select_context(config, exist_contexts)
					#logging.info(phrase_seed)
					if phrase_seed[0] == "<@#mention>":
						phrase.append(sender)
					else:
						phrase.append(phrase_seed[0])
					if phrase_seed[1] == "<@#mention>":
						phrase.append(sender)
					else:
						phrase.append(phrase_seed[1])
					current_pair = phrase_seed
					while current_pair[1] != None: #begin building sentence forwards from seed word
						next_contexts = await client.db_query("SELECT word1, word2, word3, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word1) LIKE LOWER(?))\
						 AND (LOWER(word2) LIKE LOWER(?)) ORDER BY mfreq DESC", (userid, ) + current_pair)
						if len(next_contexts) == 0:
							break
						next_link = next_contexts[-1]
						for context in next_contexts: 
							roll = random.randint(1,100)
							if roll <= config["sanity"]:
								next_link = context
								continue
						if next_link[2] == "<@#mention>":
							phrase.append(sender)
						else:
							phrase.append(next_link[2])
						if len(phrase) > config["maxchain"]:
							current_pair = (next_link[1], None)
						else:
							current_pair = (next_link[1], next_link[2])
					current_pair = phrase_seed
					while current_pair[0] != None: #begin building sentence backwards from seed word
						next_contexts = await client.db_query("SELECT word1, word2, word3, CASE user WHEN (?) THEN 100*freq ELSE freq END 'mfreq' FROM  " + self.tablename + " WHERE (LOWER(word2) LIKE LOWER(?))\
						 AND (LOWER(word3) LIKE LOWER(?)) ORDER BY mfreq DESC", (userid, ) + current_pair)
						if len(next_contexts) == 0:
							break
						next_link = next_contexts[-1]
						for context in next_contexts:
							roll = random.randint(1,100)
							if roll <= config["sanity"]:
								next_link = context
						if next_link[0] == "<@#mention>":
							phrase.insert(0, sender)
						else:
							phrase.insert(0, next_link[0])
						if len(phrase) > config["maxchain"]:
							current_pair = (None, next_link[1])
						else:
							current_pair = (next_link[0], next_link[1])
		except:
			raise
		sentence = " ".join(phrase)
		return sentence

	async def learn_sentence(self, client, config, message, userid):
		try:
			#logging.info(words)
			words = message.split()
			wlen = len(words)
			if wlen>2:
				mention = False
				for word in range(wlen):
					if (words[word].lower() in config["triggers"]) or mentionmatch.match(words[word]):
						mention = True
						words[word]="<@#mention>"
					if words[word].lower() == '@everyone':
						words[word]="everyone"
				index = 0
				if not (mention and wlen<5):
					if wlen > 3:
						await client.db_query("INSERT OR IGNORE INTO  " + self.tablename + " (word2, word3, user) VALUES (?, ?, ?)", (words[0], words[1], userid))
						await client.db_query("UPDATE  " + self.tablename + " SET freq = freq + 1 WHERE word2=? AND word3=? AND word1 is ''",\
						 (words[0], words[1]))
					while index < wlen-2:
						await client.db_query("INSERT OR IGNORE INTO  " + self.tablename + " (word1, word2, word3, user) VALUES (?, ?, ?, ?)",\
						 (words[index], words[index+1], words[index+2], userid))
						await client.db_query("UPDATE  " + self.tablename + " SET freq = freq + 1 WHERE word1=? AND word2=? AND word3=? AND user=?",\
						 (words[index], words[index+1], words[index+2], userid))
						index += 1
					if wlen > 3:
						await client.db_query("INSERT OR IGNORE INTO  " + self.tablename + " (word1, word2, user) VALUES (?, ?, ?)", (words[-2], words[-1], userid))
						await client.db_query("UPDATE  " + self.tablename + " SET freq = freq + 1 WHERE word1=? AND word2=? AND user=? AND word3 is ''",\
						 (words[-2], words[-1], userid))
		except:
			raise

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		sender = random.choice(config["articles"])
		if sender == "<#@ping>":
			sender = "<@!" + str(message.author.id) + ">"
		elif sender == "<#sender>":
			sender = message.author.name
		elif sender == "<#nick>": #and channel is a textchannel?
			if isinstance(message.author, discord.Member):
				sender = message.author.nick
			else:
				sender = message.author.name
		if (not message.author.id == client.user.id) and (not message.channel.id in config["blacklist"]):
			if cmd:
				await self.do_command(client, config, message)
			else:
				msg = " "
				msg = mangle_line(message.content)
				roll = config["replyrate"]>random.random()
				named = False
				if str(client.user.id) in msg:
					named = True
				for word in config["triggers"]:
					if word in msg.lower():
						named = True
				cooled = time.time()>(self.lastmsg+config["cooldown"])
				if (roll or named) and cooled:
					response = ""
					response = await self.build_sentence(client, config, msg, sender, message.channel, message.author.id)
					if response != "":
						sent = await message.channel.send(response)
						self.lastmsg = time.time()
						self.composed.append(sent.id)
				if config["learning"]:
					try:
						await self.learn_sentence(client, config, msg, message.author.id)
						await client.db_commit()
					except:
						pass

	async def do_command(self, client, config, message):
		cmd = client.get_cmd(message)
		command = cmd["cmd"]
		args = cmd["args"]
		admin = cmd["admin"]
		if command=="feed" and admin:
			hist = 1000
			if len(args) > 1:
				channel = discord.utils.get(client.get_all_channels(), id=int(args[0]))
				hist = int(args[1])
			else:
				channel = message.channel
				hist = int(args[0])
			logging.info("Learning...")
			await message.channel.send("Learning from " + channel.name)
			linecount = 0
			async for histm in channel.history(limit=hist):
				line = mangle_line(histm.content)
				await self.learn_sentence(client, config, line, histm.author.id)
				linecount += 1
				if ((linecount%1000)==0):
					logging.info(str(linecount/1000).split(".")[0] + "k lines")
			await client.db_commit()
			await message.channel.send("Learned from " + str(linecount) + " lines")
		elif command=="words":
			words = await client.db_query("SELECT COUNT(*) FROM (SELECT DISTINCT LOWER(word1) FROM  " + self.tablename + ")")
			contexts = await client.db_query("SELECT sum(freq) FROM  " + self.tablename)
			await message.channel.send("Currently have " + str(words[0][0]) + " words and " + str(contexts[0][0])  + " contexts.")
		elif command=="known" and args:
			for word in args[:8]:
				query = await client.db_query("SELECT sum(freq) FROM  " + self.tablename + " WHERE LOWER(word1) LIKE LOWER(?) OR LOWER(word2)\
				 LIKE LOWER(?) OR LOWER(word3) LIKE LOWER(?)", (word, word, word))
				contexts = query[0][0]
				if contexts != None:
					await message.channel.send("I know " + word + " in " + str(contexts)  + " contexts.")
				else:
					await message.channel.send("I don't know " + word)
		elif command=="clean" and admin:
			contexts = await client.db_query("SELECT sum(freq) FROM  " + self.tablename)[0][0]
			await message.channel.send("Used to have " + str(contexts)  + " contexts.")
			await client.db_query("UPDATE contexts SET freq = cast((freq+1)/2 as int)")
			contexts = await client.db_query("SELECT sum(freq) FROM  " + self.tablename)[0][0]
			await client.db_commit()
			await message.channel.send("Now have " + str(contexts)  + " contexts.")

	async def on_reaction_add(self, client, config, reaction, user):
		#my message
		mine = reaction.message.author == client.user
		#newer than a day
		fresh = reaction.message.created_at > (datetime.now() - timedelta(days=1))
		#not tweeted already
		new = reaction.message.id not in self.tweeted
		#something said by markov3 module
		composed = reaction.message.id in self.composed
		#twitter enabled/keys set
		tweeting = config["access_token"] != "" and config["access_secret"] != "" and config["consumer_key"] != "" and config["consumer_secret"] != "" and config["twitter_name"] != ""
		if mine and fresh and new and tweeting and composed:
			if reaction.count >= config["tweet_thres"] and datetime.now() > (self.tweet_timer + timedelta(seconds=config["tweet_delay"])):
				t = Twitter(auth=OAuth(config["access_token"], config["access_secret"] , config["consumer_key"], config["consumer_secret"]))
				orig_msg = reaction.message.content
				final_msg = ""
				for word in orig_msg.split(" "):
					if word in config["donttweet"]:
						newword = config["donttweet_swaps"][random.randint(0,len(config["donttweet_swaps"]))-1]
						final_msg += newword + " "
					else:
						final_msg += word + " "
				response = t.statuses.update(status=final_msg)
				await reaction.message.channel.send("https://twitter.com/" + config["twitter_name"] + "/status/" + response["id_str"])
				self.tweeted.append(reaction.message.id)
