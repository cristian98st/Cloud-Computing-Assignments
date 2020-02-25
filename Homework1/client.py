from tkinter import *
from PIL import Image, ImageTk
import requests, json
import io
import base64
from urllib.request import urlopen

def clicked_generate():
    print("clicked")
    api_url = "http://127.0.0.1:7777/generateMeme"
    response = json.loads(requests.request("GET", api_url).text)
    url = response['img']

    image_byt = urlopen(url).read()
    data_stream = io.BytesIO(image_byt)
    pil_image = Image.open(data_stream)

    w, h = pil_image.size
    wpercent = (w/float(pil_image.size[0]))
    hsize = int((float(pil_image.size[1])*float(wpercent)))
    img = pil_image.resize((w,hsize), Image.ANTIALIAS)
    tk_image = ImageTk.PhotoImage(img, width = wpercent, height = hsize)
    new_window = Toplevel()

    label = Label(new_window, image=tk_image)
    label.grid(row=0, column=0)  
    new_window.mainloop()

def clicked_log():
    api_url = "http://127.0.0.1:7777/metrics"
    response = requests.request("GET", api_url).text
    new_window = Toplevel()
    label = Text(new_window, height=40, width=100)
    label.insert(1.0, response)
    label.grid(row=1, column=1)
    new_window.mainloop()

window = Tk()

window.title("API")
window.geometry("400x400")

generate = Button(window, text="Generate", command=clicked_generate)
generate.grid(column=1, row=1)

log = Button(window, text="Log", command=clicked_log)
log.grid(column=2, row=1)

window.mainloop()
