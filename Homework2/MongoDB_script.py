import pymongo
import string
import random

my_client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = my_client["mydatabase"]

users_collection = mydb['users']
photos_collection = mydb['images']
users_photos_proxy = mydb['users_images']

names = open('usernames.txt').read().split("\n")
id = 1
for name in names:
    api_key = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(20))
    users_collection.insert_one({ '_id': id, 'username': name, 'api_key': api_key})
    id += 1