import json
import logging
import http.client
import urllib.parse
import urllib.error
import urllib.request
from telegram.ext import Updater
from telegram.ext import CommandHandler
from telegram.ext import MessageHandler, Filters
from py_ms_cognitive import PyMsCognitiveImageSearch


# Key for Vision API
subscription_key = 'YOUR_KEY'

# Region
uri_base = 'westus.api.cognitive.microsoft.com'

# Headers and params of Vision API
headers = {
    # Request headers.
    'Content-Type': 'application/json',
    'Ocp-Apim-Subscription-Key': 'YOUR_KEY',
}

params = urllib.parse.urlencode({
    # Request parameters. All of them are optional.
    'visualFeatures': 'Categories,Description,Color',
    'language': 'en',
})


# Setting token, updater and dispatcher
updater = Updater(token='YOUR_KEY')
dispatcher = updater.dispatcher
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


def start(bot, update):
    # Called when /start is sent
    bot.send_message(chat_id=update.message.chat_id,
                     text="Hello, ask me for some images and I will give you the image along with the description.")


def text_reply(bot, update):
    # Called when text is sent
    text = update.message.text
    # Reply caption
    message = ""
    # Tell user that the image is loading
    bot.send_message(chat_id=update.message.chat_id,
                     text="Searching for image...")
    search_service = PyMsCognitiveImageSearch(
        'YOUR_KEY', text)
    # First 5 results
    first_five_result = search_service.search(limit=5, format='json')
    url = first_five_result[0].json["contentUrl"]
    # Analyse and send caption
    body = "{'url':'" + url + "'}"
    try:
        # Execute the REST API call and get the response.
        conn = http.client.HTTPSConnection(
            'westus.api.cognitive.microsoft.com')
        conn.request("POST", "/vision/v1.0/analyze?%s" % params, body, headers)
        response = conn.getresponse()
        data = response.read()
        # Close the connection
        conn.close()
        # 'data' contains the JSON data. The following formats the JSON data for display.
        pseudo_json = data.decode('utf8').replace("'", '"')
        semi_json = json.loads(pseudo_json)
        JSON = json.dumps(semi_json, indent=2, sort_keys=True)
        caption = json.loads(JSON)["description"]["captions"]
        confidence = float(caption[0]["confidence"])
        text = caption[0]["text"]

        # If confidence is greater than or equal to 50%
        if confidence >= 0.5:
            message = "I see, " + text
        else:
            # If confidence is below 50%
            message = "I am not too sure, I think I see " + text

    except Exception as e:
        print(e)

    # Send the image requested
    bot.sendPhoto(chat_id=update.message.chat_id, photo=url)
    # Send a description of the image 
    bot.send_message(chat_id=update.message.chat_id, text=message)


start_handler = CommandHandler('start', start)
text_handler = MessageHandler(Filters.text, text_reply)

dispatcher.add_handler(start_handler)
dispatcher.add_handler(text_handler)
updater.start_polling()
# Blocks execution and allows ctrl + C to stop script
updater.idle()
