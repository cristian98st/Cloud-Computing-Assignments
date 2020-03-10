from http.server import HTTPServer
from http.server import BaseHTTPRequestHandler
import pymongo
import json
import random, string

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = my_client["mydatabase"]
users = mydb['users']
images = mydb['images']
proxy_collection = mydb['users_images']


class RequestHandler(BaseHTTPRequestHandler):
    user_id = -1
    paths_list = ['/user', '/user/', '/users', '/users/', 'user/images', '/user/images/', '/register', '/register/', '/image/upload', '/image/upload/', 'image/modify', 'image/modify/', '/image/modify/text', '/image/modify/text/', '/image/modify/image', '/image/modify/image/', '/delete/image', '/delete/image/', '/delete/user', '/delete/user/']

    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def _valid_auth(self):
        auth_key = self.headers['ApiKey']
        query = {'api_key': auth_key}
        result = users.find(query)
        try:
            self. user_id = result[0]['_id']
            return True
        except:
            return False

    def send_code(self, status_code, message = ""):
        self.send_response(status_code)
        self.end_headers()
        self.send_error(status_code, message)

    def do_GET(self):
        try:
            response = dict()

            if self.path == '/user' or self.path == "/user/":
                length = int(self.headers["Content-Length"])
                body = json.loads(self.rfile.read(length))
                query = {'username': body['username']}
                result = users.find(query)
                response['id'] = result[0]['_id']
                response['username'] = body['username']
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())

            elif self.path == '/users/' or self.path == '/users':
                result = users.find()
                users_list = list()
                for user in result:
                    users_list.append(
                        {'ID': user['_id'], 'username': user['username']})
                response['users'] = users_list
                self._set_headers()
                self.wfile.write(json.dumps(response).encode())

            elif self.path == '/user/images' or self.path == '/user/images/':
                length = int(self.headers['Content-Length'])
                body = json.loads(self.rfile.read(length))

                query = {'username': body['username']}
                result = users.find(query)
                response['id'] = result[0]['_id']
                response['username'] = result[0]['username']


                images_list = list()
                query = {'user_id': result[0]['_id']}
                result = proxy_collection.find(query)
                for r in result:
                    img_id = r['img_id']
                    query = {'_id': img_id}
                    result2 = images.find(query)
                    images_list.append({'img_id': img_id, 'img_link': result2[0]['img_url']})
                response['images'] = images_list

                self._set_headers()
                self.wfile.write(json.dumps(response).encode())
            else:
                if self.path in self.paths_list:
                    self.send_code(405)
                else:
                    self.send_code(404)


        except Exception as e:
            print(e.__class__)
            if e.__class__ == IndexError:
                self.send_code(404)
            elif e.__class__ == KeyError or e.__class__ == TypeError:
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
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())

            # endpoints that do require authentication
            elif not self._valid_auth():
                self.send_code(401)
            else:  
                if self.path == '/image/upload' or self.path == '/image/upload/':
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_url = generateImage(body['img_url'], body['text'], body['author'])

                    image_id = 1
                    if images.count_documents({}) > 0:
                        image_id = int(images.find().sort([('_id', -1)]).limit(1)[0]['_id']) + 1
                    images.insert_one({"_id": image_id, "img_url": img_url, "original_img": body['img_url'], "text": body['text'], "author": body['author']})

                    
                    proxy_collection.insert_one({"user_id": self.user_id, "img_id": image_id})
                    response['image_id'] = image_id
                    response['image_url'] = img_url
                    self._set_headers()
                    self.wfile.write(json.dumps(response).encode())
                else:
                    if self.path in self.paths_list:
                        self.send_code(405)
                    else:
                        self.send_code(404)

        except Exception as e:
            print(e.__class__)
            if e.__class__ == IndexError:
                self.send_code(404)
            elif e.__class__ == KeyError:
                self.send_code(400)
            else:
                self.send_code(500)

    def do_PUT(self):
        if not self._valid_auth():
            self.send_code(401)
        else:
            try:
                response = dict()
                if self.path == "/image/modify/" or self.path == "/image/modify":
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_id = int(body['img_id'])
                    new_text = body['text']
                    new_author = body['author']
                    new_img = body['img_url']

                    query = {'img_id': img_id}
                    result = proxy_collection.find(query)
                    if int(result[0]['user_id']) != int(self.user_id):
                        self.send_code(403)
                    else:
                        query = {'_id': img_id}
                        new_img_url = generateImage(new_img, new_text, new_author)
                        new_values = {'$set': {'text': new_text, 'author': new_author, 'img_url': new_img_url, 'original_img': new_img}}
                        images.update_one(query, new_values)

                        self._set_headers()
                else:
                    if self.path in self.paths_list:
                        self.send_code(405)
                    else:
                        self.send_code(404)

            except Exception as e:
                print(e.__class__)
                if e.__class__ == IndexError:
                    self.send_code(404)
                elif e.__class__ == KeyError:
                    self.send_code(400)
                else:
                    self.send_code(500)


    def do_PATCH(self):
        if not self._valid_auth():
            self.send_code(401)
        else:
            try:
                response = dict()
                if self.path == "/image/modify/text" or self.path == "/image/modify/text/":
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_id = int(body['img_id'])
                    new_text = body['text']
                    new_author = body['author']

                    query = {'img_id': img_id}
                    result = proxy_collection.find(query)
                    if int(result[0]['user_id']) != int(self.user_id):
                        self.send_code(403)
                    else:
                        query = {'_id': img_id}
                        original_img = images.find(query)[0]['original_img']
                        new_img_url = generateImage(original_img, new_text, new_author)
                        new_values = {'$set': {'text': new_text, 'author': new_author, 'img_url': new_img_url}}
                        images.update_one(query, new_values)

                        self._set_headers()

                elif self.path == "/image/modify/image" or self.path == "/image/modify/image/":
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_id = int(body['img_id'])
                    new_image = body['image_url']

                    query = {'img_id': img_id}
                    result = proxy_collection.find(query)
                    if int(result[0]['user_id']) != int(self.user_id):
                        self.send_code(403)
                    else:
                        query = {'_id': img_id}
                        result = images.find(query)[0]
                        text = result['text']
                        author = result['author']
                        new_img_url = generateImage(new_image, text, author)
                        new_values = {'$set': {'original_img': new_image, 'img_url': new_img_url}}
                        images.update_one(query, new_values)

                        self._set_headers()
                else:
                    if self.path in self.paths_list:
                        self.send_code(405)
                    else:
                        self.send_code(404)

            except Exception as e:
                print(e.__class__)
                if e.__class__ == IndexError:
                    self.send_code(404)
                elif e.__class__ == KeyError:
                    self.send_code(400)
                else:
                    self.send_code(500)

    def do_DELETE(self):
        if not self._valid_auth():
            self.send_code(401)
        else:
            try:
                response = dict()
                if self.path == "/delete/user" or self.path == "/delete/user/":
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    username = body['username']

                    query = {'user_id': self.user_id}
                    result = users.find({"_id": self.user_id})[0]
                    if result['username'] != username:
                        self.send_code(403)
                    else:
                        users.delete_one({'_id': self.user_id})
                        result = proxy_collection.find(query)
                        for r in result:
                            query2 = {'_id': r['img_id']}
                            images.delete_one(query2)
                        proxy_collection.delete_many(query)

                        self._set_headers()

                if self.path == '/delete/image' or self.path == 'delete/image':
                    length = int(self.headers['Content-Length'])
                    body = json.loads(self.rfile.read(length))
                    img_id = body['img_id']

                    query = {'img_id': img_id}
                    result = proxy_collection.find(query)[0]
                    if result['user_id'] != self.user_id:
                        self.send_code(403)
                    else:
                        proxy_collection.delete_one(query)
                        query = {'_id': img_id}
                        result = images.delete_one(query)

                        self._set_headers()

                else:
                    if self.path in self.paths_list:
                        self.send_code(405)
                    else:
                        self.send_code(404)
                        
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