from botmodule import botmodule 
import sys
import requests
#Google module
class moduleClass(botmodule):
	def init_settings(self):
		self.set("apikey", "", "API key for google services",True)
		self.set("search_engine_id", "", "Search engine ID for google services",True)

	def default_config(self):
		return {"apikey": "",
				"search_engine_id": ""
		}

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		if cmd:
			command = cmd["cmd"]
			args = cmd["args"]
			if (command == "g") or (command == "google"):
				if args:
					try:
						msg = ""
						g_api_key = config["apikey"]
						search_engine_id = config["search_engine_id"]
						query = ' '.join(args)
						s = requests.Session()
						search = s.get("https://www.googleapis.com/customsearch/v1",
							params={
								"alt": "json",
								"key": g_api_key,
								"cx": search_engine_id,
								"q": query
							})
						results = search.json()
						msg = results["items"][0]["title"] + ": " + results["items"][0]["snippet"][:40] + "... " + results["items"][0]["link"]
						await message.channel.send(msg)
					except:
						msg = "Problem googling that"
						await message.channel.send(msg)
						for error in sys.exc_info():
							print(str(error))
						pass
				else:
					await message.channel.send("Please say what to search for.")
