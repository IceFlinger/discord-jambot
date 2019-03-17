from botmodule import botmodule 
from random import choice
import pycurl
import sys
import random
import re
import time
import string
import threading
import math

from io import BytesIO
#Markov chain jambot-discord module
#By ice at scrub club discord

def mangle_line(line):
	links = re.findall(r'(https?://\S+)', line) 
	f = string.ascii_letters + string.digits + "():<>[].,!?/-^%$#@ "
	line = ' '.join(w for w in line.split() if w not in links) #Remove URLs
	line = ' '.join(w for w in line.split() if w[0] not in "[\"(") #Remove timestamp type stuff and quotes
	line = ' '.join(w for w in line.split() if w[-1] not in "\;\"%") #Remove broken words
	line = ' '.join(w for w in line.split() if not len(w)>26) #Remove long stuff
	#line = ''.join(c for c in line if c in f) #Filter whole string with f chars
	return line

class moduleClass(botmodule):
	def default_config(self):
		return {"replyrate":0.01,
		"learning":False,
		"mentionreplyrate":1,
		"maxchain":20,
		"sanity":50,
		"cooldown":2,
		"triggers": "jambot"
		"table_id": "jambot"
		}

	async def on_connect(self, client, config):
		self.tablename = "markov_" + config["table_id"]
		query = "CREATE TABLE IF NOT EXISTS " + self.tablename + " (word1 text DEFAULT '', word2 text DEFAULT '', word3 text DEFAULT '', freq int DEFAULT 0, UNIQUE(word1, word2, word3))"
		await client.db_query(query)
		await client.db_commit()
		self.nickreply = False
		self.lastmsg = 0

	def select_context(self, config, contexts):
		newpairs = {}
		for pair in contexts:
			key = (pair[0].lower(), pair[1].lower())
			if key in newpairs:
				newpairs[key] += pair[2]
			else:
				newpairs[key] = pair[2]
		#print(newpairs)
		sort = sorted(newpairs, key=newpairs.get, reverse=True)
		for pair in sort:
			roll = random.randint(1,100)
			if roll <= config["sanity"]:
				return pair
		return sort[-1]

	async def single_word_contexts(self, client, config, word):
		exist_contexts = []
		single_contexts = []
		results = await client.db_query("SELECT word1, word2, word3, freq FROM contexts3 WHERE (LOWER(word1) LIKE LOWER(?) OR LOWER(word2) LIKE LOWER(?) OR LOWER(word3) LIKE LOWER(?)) GROUP BY word1, word2, word3 ORDER BY sum(freq) DESC", (word, word, word))
		for context in results
			single_contexts.append(context)
		for context in single_contexts:
			if context[0].lower() == word.lower() or context[1].lower() == word.lower():
				exist_contexts.append((context[0], context[1], context[3]))
			if context[1].lower() == word.lower() or context[2].lower() == word.lower():
				exist_contexts.append((context[1], context[2], context[3]))
		return exist_contexts

	async def build_sentence(self, client, config, message):
		phrase = []
		try:
			chainlength = 0
			exist_contexts = [] #look for words in the trigger sentence that we know already
			words = message.content.split()
			own_nick = "<@" + client.user.id + ">"
			sender = "<@" + message.author.id + ">"
			for word in config["triggers"]:
				if word in message.clean_content.lower():
					own_nick = word
			for i in range(len(words)):
				if words[i].lower() == own_nick.lower():
					words[i] = "#nick"
			if len(words) == 3 and words[0] == "#nick":
				for context in await client.db_query("SELECT word1, word2, freq FROM contexts3 WHERE (LOWER(word1) LIKE LOWER(?) AND LOWER(word2) LIKE LOWER(?)) GROUP BY word1, word2 ORDER BY sum(freq)", (words[1], words[2])):
					exist_contexts.append(context)
				for context in await client.db_query("SELECT word2, word3, freq FROM contexts3 WHERE (LOWER(word2) LIKE LOWER(?) AND LOWER(word3) LIKE LOWER(?)) GROUP BY word2, word3 ORDER BY sum(freq)", (words[1], words[2])):
					exist_contexts.append(context)
				if len(exist_contexts) == 0: #we didn't find that exact pair's context, so check for each word individually
					exist_contexts+=await self.single_word_contexts(client, config, words[1])
					exist_contexts+=await self.single_word_contexts(client, config, words[2])
			elif len(words) == 2 and words[0] == "#nick":
				exist_contexts+=await self.single_word_contexts(client, config, words[1])
			else:
				for word1, word2 in zip(words[:-1], words[1:]):
					#for context in self.db_query("SELECT * FROM contexts WHERE (LOWER(word1) LIKE LOWER(?) AND LOWER(word2) LIKE LOWER(?)) OR (LOWER(word2) LIKE LOWER(?) AND LOWER(word3) LIKE LOWER(?)) GROUP BY word1, word2, word3 ORDER BY sum(freq)", (word1, word2, word1, word2)):
					#	exist_contexts.append(context)
					for context in await client.db_query("SELECT word1, word2, freq FROM contexts3 WHERE (LOWER(word1) LIKE LOWER(?) AND LOWER(word2) LIKE LOWER(?)) GROUP BY word1, word2 ORDER BY sum(freq)", (word1, word2)):
						exist_contexts.append(context)
					for context in await client.db_query("SELECT word2, word3, freq FROM contexts3 WHERE (LOWER(word2) LIKE LOWER(?) AND LOWER(word3) LIKE LOWER(?)) GROUP BY word2, word3 ORDER BY sum(freq)", (word1, word2)):
						exist_contexts.append(context)
			if exist_contexts:
				phrase_seed = self.select_context(config, exist_contexts)
				#print(phrase_seed)
				if phrase_seed[0] == "#nick":
					phrase.append(sender)
				else:
					phrase.append(phrase_seed[0])
				if phrase_seed[1] == "#nick":
					phrase.append(sender)
				else:
					phrase.append(phrase_seed[1])
				current_pair = phrase_seed
				while current_pair[1] != None: #begin building sentence forewards from seed word
					next_contexts = await client.db_query("SELECT * FROM contexts3 WHERE (LOWER(word1) LIKE LOWER(?)) AND (LOWER(word2) LIKE LOWER(?)) ORDER BY freq DESC", current_pair)
					if len(next_contexts) == 0:
						break
					next_link = next_contexts[-1]
					for context in next_contexts:
						roll = random.randint(1,100)
						if roll <= config["sanity"]:
							next_link = context
					if next_link[2] == "#nick":
						phrase.append(sender)
					else:
						phrase.append(next_link[2])
					if len(phrase) > config["maxchain"]:
						current_pair = (next_link[1], None)
					else:
						current_pair = (next_link[1], next_link[2])
				#print(phrase, end=" ",flush=True)
				current_pair = phrase_seed
				while current_pair[0] != None: #begin building sentence backwards from seed word
					next_contexts = await self.db_query("SELECT * FROM contexts3 WHERE (LOWER(word2) LIKE LOWER(?)) AND (LOWER(word3) LIKE LOWER(?)) ORDER BY freq DESC", current_pair)
					if len(next_contexts) == 0:
						break
					next_link = next_contexts[-1]
					for context in next_contexts:
						roll = random.randint(1,100)
						if roll <= config["sanity"]:
							next_link = context
					if next_link[0] == "#nick":
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
		if sentence[0] == " ":
			sentence = sentence[1:]
		if sentence != "":
			await message.channel.send(sentence)

	async def learn_sentence(self, client, config, message):
		try:
			#print(words)
			words = message.content.split()
			if len(words)>2:
				named = False
				own_nick = "<@" + client.user.id + ">"
				sender = "<@" + message.author.id + ">"
				for word in config["triggers"]:
					if word in message.clean_content.lower():
						own_nick = word
				for word in range(len(words)):
					if words[word].lower() in own_nick.lower():
						named = True
						words[word]="#nick"
				index = 0
				if not (named and len(words)<5):
					if (len(words) > 3):
						await client.db_query("INSERT OR IGNORE INTO contexts3 (word2, word3) VALUES (?, ?)", (words[0], words[1]))
						await client.db_query("UPDATE contexts3 SET freq = freq + 1 WHERE word2=? AND word3=? AND word1 is ''", (words[0], words[1]))
					while index < len(words)-2:
						word1 = words[index]
						word2 = words[index+1]
						word3 = words[index+2]
						await client.db_query("INSERT OR IGNORE INTO contexts3 (word1, word2, word3) VALUES (?, ?, ?)", (word1, word2, word3))
						await client.db_query("UPDATE contexts3 SET freq = freq + 1 WHERE word1=? AND word2=? AND word3=?", (word1, word2, word3))
						index += 1
					if (len(words) > 3):
						await client.db_query("INSERT OR IGNORE INTO contexts3 (word1, word2) VALUES (?, ?)", (words[-2], words[-1]))
						await client.db_query("UPDATE contexts3 SET freq = freq + 1 WHERE word1=? AND word2=? AND word3 is ''", (words[-2], words[-1]))
		except:
			raise

	async def on_message(self, client, config, message):
		cmd = await client.get_cmd(message)
		if cmd:
			async with message.channel.typing():
				await self.do_command(client, config, message)
		else:
			msg = " "
			own_nick = "<@" + client.user.id + ">"
			sender = "<@" + message.author.id + ">"
			thisbot = True
			lametrig = False
			msg = mangle_line(message.content)
			for word in config["triggers"]:
				if word in message.clean_content.lower():
					own_nick = word
			roll = config["replyrate"]>random.random()
			nickroll = config["mentionreplyrate"]>random.random()
			for word in config["triggers"]:
				named = (own_nick.lower() in msg.lower()) or (word.lower() in msg.lower())
			cooled = time.time()>(self.lastmsg+config["cooldown"])
			if (roll or (nickroll and named)) and cooled:
				#t = threading.Thread(target=self.build_sentence, args=(c, e, msg, sender))
				#t.daemon = True
				#t.start()
				async with message.channel.typing():
					await self.build_sentence(client, config, msg)
				self.lastmsg = time.time()
			if thisbot and config["learning"] and not lametrig:
				try:
					await self.learn_sentence(client, config, msg)
					self.db_commit()
				except:
					pass

	def do_command(self, client, config, message):
		cmd = await client.get_cmd(message)
		command = cmd["command"]
		args = cmd["args"]
		admin = cmd["admin"]
		if command=="feed" and admin and args:
			print("Downloading: " + args[0])
			await message.channel.send("Downloading: " + args[0])
			textbytes = BytesIO()
			try:
				textconn = pycurl.Curl()
				textconn.setopt(textconn.URL, args[0])
				textconn.setopt(textconn.WRITEDATA, textbytes)
				textconn.perform()
				textconn.close()
				text = textbytes.getvalue().decode('iso-8859-1').split('\n')
				linecount = 0
				print("Learning...")
				await message.channel.send("Learning")
				try:
					multi = 1
					if len(args)>1:
						multi = int(args[1])
					for line in text:
						line = mangle_line(line)
						await self.learn_sentence(client, config, line)
						linecount += 1
						if ((linecount%1000)==0):
							print(str(linecount/1000).split(".")[0] + "k lines, ", end="" , flush=True)
					await client.db_commit()
				except:
					await message.channel.send("Interrupted while learning from file (Something else accessing DB?)")
					raise
				try:
					print("Learned from " + str(linecount) + " lines")
					await message.channel.send("Learned from " + str(linecount) + " lines")
					await client.db_commit()
					print("Commited to DB")
				except:
					pass
			except:
				await message.channel.send("Couldn't download file.")
				raise
		elif command=="words":
			words = await client.db_query("SELECT COUNT(*) FROM (SELECT DISTINCT LOWER(word1) FROM contexts3)")[0][0]
			contexts = await db_query("SELECT sum(freq) FROM contexts3")[0][0]
			message.channel.send("Currently have " + str(words) + " words and " + str(contexts)  + " contexts.")
		elif command=="known" and args:
			for word in args[:8]:
				contexts = await client.db_query("SELECT sum(freq) FROM contexts3 WHERE LOWER(word1) LIKE LOWER(?) OR LOWER(word2) LIKE LOWER(?) OR LOWER(word3) LIKE LOWER(?)", (word, word, word))[0][0]
				if contexts != None:
					await message.channel.send("I know " + word + " in " + str(contexts)  + " contexts.")
				else:
					await message.channel.send("I don't know " + word)
		elif command=="clean" and admin:
			contexts = await client.db_query("SELECT sum(freq) FROM contexts3")[0][0]
			await message.channel.send("Used to have " + str(contexts)  + " contexts.")
			await client.db_query("UPDATE contexts SET freq = cast((freq+1)/2 as int)")
			contexts = await client.db_query("SELECT sum(freq) FROM contexts3")[0][0]
			await client.db_commit()
			await message.channel.send("Now have " + str(contexts)  + " contexts.")
