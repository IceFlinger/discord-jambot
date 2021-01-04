from botmodule import botmodule 
import logging
import traceback
import html
#from google.cloud import translate
import requests
import urllib.parse
import json

def translate(q, lang):
	qs = urllib.parse.urlencode({"q": q.encode("utf-8")})
	print(qs)
	r = requests.get("https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" + lang + "&dt=t&" + qs);
	print(r.content)
	return r.json()[0][0][0]

class moduleClass(botmodule):
	def default_config(self):
		return {"to": ["en"]}

	def on_init(self):
		self.logger = logging.getLogger("jambot.interpret")
		#self.g = translate.Client()

	async def on_message(self, client, config, message):
		if not message.author.id == client.user.id:
			for lang in config["to"]:
				#d = self.g.detect_language([message.content])
				#d = detect_language(message.content)
				#if d[0]["language"] != lang and d[0]["confidence"] == 1:
					#m = self.g.translate([message.content], target_language=lang)
				m = translate(message.content, lang)
				#if m[0]["translatedText"] != message.content:
				if m != message.content:
					#await message.channel.send("<" + message.author.name + ">: " + html.unescape(m[0]["translatedText"]))
					await message.channel.send("<" + message.author.name + ">: " + html.unescape(m))
