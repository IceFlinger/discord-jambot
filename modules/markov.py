from botmodule import botmodule 


class moduleClass(botmodule):

	def default_config(self):
		return {"replyrate": 0.01,
		"learning": False
		"pingreply": True
		"maxchain": 20
		"sanity": 0.5
		"cooldown": 2
		"maxdepth": 5
		}

	async def on_connect(self, client, config):
		await client.db_query("CREATE TABLE IF NOT EXISTS markov (hash text DEFAULT '', word text DEFAULT '', prefreq text int DEFAULT 0, postfreq int DEFAULT 0, UNIQUE(hash, word))")
		await client.db_commit()

	async def learn_sentence(self, client, config, msg):
		words = msg.split()
		