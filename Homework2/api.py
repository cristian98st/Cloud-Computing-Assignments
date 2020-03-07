from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import pymongo
import json
import random, string

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = my_client["mydatabase"]
users = mydb['users']
images = mydb['images']


class RequestHandler(BaseHTTPRequestHandler):
    user_id = -1

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _valid_auth(self):
        auth_key = self.headers['ApiKey']
        query = {'api_key': auth_key}
        result = users.find(query)
        try:
            self.user_id = result[0]['_id']
            return True
        except:
            return False

    def send_code(self, status_code, message = ""):
        self.send_response(status_code)
        self.end_headers()
        self.send_error(status_code, message)

    def do_GET(self):
        if not self._valid_auth():
            self.send_code(401)
        else:
            try:
                response = dict()

                if self.path == '/user' or self.path == "/user/":
                    length = int(self.headers["Content-Length"])
                    body = json.loads(self.rfile.read(length))
                    query = {'username': body['username']}
                    result = users.find(query)
                    response['id'] = result[0]['_id']
                    response['username'] = body['username']

                elif self.path == '/users/' or self.path == '/users':
                    result = users.find()
                    users_list = list()
                    for user in result:
                        users_list.append(
                            {'ID': user['_id'], 'username': user['username']})
                    response['users'] = users_list

                elif self.path == '/user/images' or self.path == '/user/images/':
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))

                    query = {'username': body['username']}
                    result = users.find(query)
                    response['id'] = result[0]['_id']
                    response['username'] = result[0]['username']

                    images_list = list()
                    query = {'user_id': result[0]['_id']}
                    result = images.find(query)
                    for r in result:
                        images_list.append({'img_link': r['img_url']})
                    response['images'] = images_list

                else:
                    self.send_code(404)

                self._set_headers()
                self.wfile.write(json.dumps(response).encode())

            except Exception as e:
                print(e.__class__)
                if e.__class__ == IndexError:
                    self.send_code(404)
                elif e.__class__ == KeyError:
                    self.send_code(400)
                else:
                    self.send_code(500)

    def do_POST(self):
        response = dict()
        try:
            # endpoints that do not require authentication
            if self.path == '/register' or self.path == '/register/':
                length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(length))
                query = {'username': body['username']}
                result = users.find(query)
                if users.count_documents(query) > 0:
                    self.send_code(409, message = "Somenone is already using this username.")
                else:
                    id = int(users.find().sort([('_id', -1)]).limit(1)[0]['_id']) + 1
                    api_key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20)) 
                    users.insert_one({'_id': id, 'username': body['username'], 'api_key': api_key})
                    response['id'] = id
                    response['username'] = body['username']
                    response["api_key"] = api_key

            # endpoints that do require authentication
            elif not self._valid_auth():
                self.send_code(401)
            else:  
                if self.path == '/upload_image' or self.path == '/upload_image/':
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_url = generateImage(body['img_url'], body['text'], body['author'])
                    print(img_url)
                    images.insert_one({"user_id": self.user_id, "img_url": img_url})
                    response['image_url'] = img_url

            self._set_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            print(e.__class__)
            if e.__class__ == IndexError:
                self.send_code(404)
            elif e.__class__ == KeyError:
                self.send_code(400)
            else:
                self.send_code(500)


def run(server_class=HTTPServer, handler_class=RequestHandler, addr="127.0.0.1", port=8080):
    server_address = (addr, port)
    http = server_class(server_address, handler_class)

    print(f"Server started on {addr}:{port}")
    http.serve_forever()

def generateImage(image_url, text, author):
    import requests
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    import base64

    author = "-" + author
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
    fnt = ImageFont.truetype('/Library/Fonts/arial.ttf', 40)
    width, height = image.size
    shadowcolor = 'black'
    draw.text((10-1, height/2), text, font=fnt, fill=shadowcolor)
    draw.text((10+1, height/2), text, font=fnt, fill=shadowcolor)
    draw.text((10, height/2-1), text, font=fnt, fill=shadowcolor)
    draw.text((10, height/2+1), text, font=fnt, fill=shadowcolor)

    draw.text((10, height/2), text, (255, 255, 255),font=fnt)

    draw.text((width - width/3 -1, height - 50), author, font=fnt, fill=shadowcolor)
    draw.text((width - width/3 +1, height - 50), author, font=fnt, fill=shadowcolor)
    draw.text((width - width/3, height - 50 -1), author, font=fnt, fill=shadowcolor)
    draw.text((width - width/3, height - 50 +1), author, font=fnt, fill=shadowcolor)

    draw.text((width - width/3, height - 50), author, (255, 255, 255), font=fnt)

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

    return response['data']['link']

if __name__ == "__main__":
    run()