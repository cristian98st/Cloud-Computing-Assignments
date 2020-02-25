from flask import Flask
from flask import request
from PIL import Image, ImageDraw, ImageFont
import urllib
import requests
import json, base64
from io import BytesIO

app = Flask(__name__)

@app.route("/getImage", methods=["GET"])
def generateImage():
    if 'image' in request.args:
        if 'text' in request.args:
            image_url = request.args['image']
            text = request.args['text']
            search_space = False
            for i in range(len(text)):
                if i >= 50 and i%50 == 0:
                    search_space = True
                if search_space == True and text[i] == ' ':
                    text = text[:i] + "\n" + text[i:]
                    search_space = False

            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            draw = ImageDraw.Draw(image)
            print(text)
            fnt = ImageFont.truetype('/Library/Fonts/arial.ttf', 40)
            width, height = image.size
            shadowcolor = 'black'
            draw.text((10-1, height/2), text, font=fnt, fill=shadowcolor)
            draw.text((10+1, height/2), text, font=fnt, fill=shadowcolor)
            draw.text((10, height/2-1), text, font=fnt, fill=shadowcolor)
            draw.text((10, height/2+1), text, font=fnt, fill=shadowcolor)

            draw.text((10, height/2), text, (255, 255, 255),font=fnt)

            draw.text((width - width/3 -1, height - 50), "-Kanye West", font=fnt, fill=shadowcolor)
            draw.text((width - width/3 +1, height - 50), "-Kanye West", font=fnt, fill=shadowcolor)
            draw.text((width - width/3, height - 50 -1), "-Kanye West", font=fnt, fill=shadowcolor)
            draw.text((width - width/3, height - 50 +1), "-Kanye West", font=fnt, fill=shadowcolor)

            draw.text((width - width/3, height - 50), "-Kanye West", (255, 255, 255), font=fnt)

            # image.save(text[5] + ".jpg")

            # filename = text[5] + ".jpg"
            # print(filename)
            buffered = BytesIO()
            image.save(buffered, format="JPEG")

            meme_url = "https://api.imgur.com/3/upload"

            payload = {
                'image' : base64.b64encode(buffered.getvalue())
            }

            headers = {
                'Authorization': "Client-ID 29fedc3beca2ffc"
                }

            response = json.loads(requests.request("POST", meme_url, data=payload, headers=headers).text)

            print("KKSKKSKSK")
            print(response['data']['link'])
            return response['data']['link']
app.run()
