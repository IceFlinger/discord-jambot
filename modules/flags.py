from botmodule import botmodule 
import requests
from lxml import html
import random
import logging
import time
import io
import hashlib
from PIL import Image, ImageOps

class moduleClass(botmodule):

	def default_config(self):
		return {"downloads": {"example":{ "cache": True, "web_folder": "https://example.com/images/"}},
		"uploads": {"example":
		{"local_folder": "/srv/www/images",
		"raw_folder": "/backup/unconverted",
		"max_filesize": 4000000,
		"resize": False,
		"resize_w": 500,
		"resize_h": 192,
		"resize_tolerence": 0.8}}
		}

	async def on_ready(self, client, config):
		self.cached = {}
		self.cached_list = {}
		for download in config["downloads"]:	
			self.cached[download] = False
			self.cached_list[download] = []

	def upload_flag(self, client, config, message):
		cmd = client.get_cmd(message)
		key = cmd["cmd"]
		self.cached[key] = False
		try:
			urls = []
			if len(message.attachments) > 0:
				for link in message.attachments:
					urls.append((link.url, link.filename.split('.')[0]))
			#append args
			messages = []
			for urlp in urls:
				filename = urlp[1]
				url = urlp[0]
				r = requests.get(url, stream=True)
				size = 0
				ctt = io.BytesIO()
				for chunk in r.iter_content(2048):
					size += len(chunk)
					ctt.write(chunk)
					if size > config["uploads"][key]["max_filesize"]:
						r.close()
						messages.append("That file is too big")
				content = ctt.getvalue()
				img_in = Image.open(io.BytesIO(content))
				hash = hashlib.md5()
				hash.update(content)
				i = hash.hexdigest()
				if img_in.format == "GIF" and not config["uploads"][key]["resize"]:
					img_in.save(config["uploads"][key]["local_folder"] + i + '.gif', 'GIF', save_all=True, optimize=False)
					if key in config["downloads"]:
						messages.append("<" + config["downloads"][key]["web_folder"] + i + ".gif>")
				else:
					if config["uploads"][key]["raw_folder"]:
						img_in.save(config["uploads"][key]["raw_folder"] + filename + '-' + i + '.png', 'PNG')
					img_out = img_in
					if config["uploads"][key]["resize"]:
						x = config["uploads"][key]["resize_w"]
						y = config["uploads"][key]["resize_h"]
						img_out = img_in.resize((x,y), Image.ANTIALIAS)
					img_out.save(config["uploads"][key]["local_folder"] + i + '.png', 'PNG')
					if key in config["downloads"]:
						messages.append("<" + config["downloads"][key]["web_folder"] + i + ".png>")
			return messages
		except:
			logging.error(traceback.print_exc())
		return ["Problem flagging that"]

	async def on_message(self, client, config, message):
		cmd = client.get_cmd(message)
		uploaded = False
		if cmd:
			#redo logic here/check args for upload case
			if config["uploads"] != None and (len(cmd["args"]) > 0 or len(message.attachments) > 0):
				for upload in config["uploads"]:
					if cmd["cmd"] == upload:
						replies = []
						async with message.channel.typing():
							replies =  self.upload_flag(client, config, message)
							uploaded = True
						await message.channel.send(" ".join(replies))
			if not uploaded:
				for download in config["downloads"]:
					if cmd["cmd"] == download:
						async with message.channel.typing():
							if (not self.cached[download]) or (not config["downloads"][download]["cache"]):
								r = requests.get(config["downloads"][download]["web_folder"])
								d = html.fromstring(r.content)
								imglist = d.xpath('//a[@href]/@href')
								imglist = imglist[5:] #first 4 links are random index shit, lazy way to skip (add check for image extension)
								self.cached_list[download] = imglist
								self.cached[download] = True
							else:
								imglist  = self.cached_list[download] 
							imgid = random.randint(0,len(imglist)-1)
						await message.channel.send(config["downloads"][download]["web_folder"] + imglist[imgid])
