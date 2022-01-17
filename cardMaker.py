import base64
import io
from pickletools import optimize
import urllib.request
from datetime import datetime, timedelta
from os import remove
from sys import argv, exit, platform

import drawerFunctions as df
import requests
from bs4 import BeautifulSoup as bs
from PIL import Image, ImageDraw


def coverAndLenght(song, artist):

    song = song.replace(' ', '+')
    artist = artist.replace(' ', '+')


    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    url = "https://www.last.fm/music/%s/_/%s"%(artist, song)
    site = requests.get(url, headers=headers)
    site = bs(site.text)
    lenght = site.find_all('dd', {'class' : "catalogue-metadata-description"})[0].contents[0].replace('\n','').replace(' ','')
    b = site.find_all('p', {"class" : "source-album-stats"})
    c = [each.contents[0].replace(' ', '').replace('\n', '').replace(',', '') for each in b]
    c = [int(each) for each in c]
    d = c.index(max(c))
    e = site.find_all('span', {"class" : "cover-art"})[d].contents[1].attrs['src']
    urllib.request.urlretrieve(e, "cover.jpg")

    return "cover.jpg", lenght



def main(song, artist):
    cover, lenght = coverAndLenght(song, artist)
    #cover, lenght = "cover.jpg", "06:43"#coverAndTime(artist, song)


    # Opening cover art
    w, h = 1000,500
    coverB, _ = df.openImage(cover)
    coverB, _ = df.resizeToFit(coverB, h)
    coverB = coverB.convert("RGBA")
    coverD = ImageDraw.Draw(coverB)

    
    # Detect dominant color (of edges)
    coverBCopy = coverB.copy().convert("RGBA")
    coverDCopy = ImageDraw.Draw(coverBCopy)
    w, h = coverB.width//10, coverB.width//10
    coverDCopy.rectangle([0,h,coverB.width,coverB.height-h], fill = (0,0,0,0))
    w, h = 1000,500
    background = tuple(df.computeDominant2(coverBCopy))

    # Creating gradient
    gradientB, gradientD = df.backgroundPNG(*coverB.size)

    myRange = coverB.width
    steps = 255/(myRange)
    alpha = 256
    gradientD.rectangle([0,0,15,coverB.height], fill=(*background, 255), width = 1)
    for i in range(15, int(myRange)):
        gradientD.line([i,0,i,coverB.height], fill=(*background, int(alpha)), width = 1)
        alpha-=steps


    # Combining cover + gradient + all canvas
    coverB = df.pasteItem(coverB, gradientB, 0, 0)
    canvasB, canvasD = df.backgroundPNG(w, h, tuple(background))
    canvasB = df.pasteItem(canvasB, coverB, w-coverB.width//3*2, h-coverB.height)

    # Rounding the edges of the canvas
    canvasB = df.roundCorners(canvasB, 58)

    # Defining font color
    luminance = df.calculateLuminance(canvasB)
    font_color = "#FFFFFF" if luminance<=50 else "#000000"
    second_font_color = "#cbcbcb" if luminance <=50 else "#323232"
    # Writing song title
    if platform == "linux":
        font_path = "/usr/share/fonts/Arialbd.ttf"
    elif platform == "win32":
        font_path = "C:\\Windows\Fonts\Arialbd.ttf"
    font = df.fontDefiner(font_path, 60)
    x, y = 54, 115
    df.drawText(x, y, canvasD, song, font_color, font)

    # Writing artist with less opacity
    if platform == "linux":
        font_path = "/usr/share/fonts/Arial.ttf"
    elif platform == "win32":
        font_path = "C:\\Windows\Fonts\Arial.ttf"

    font = df.fontDefiner(font_path, 50)
    x, y = 54, 196
    df.drawText(54, 196, canvasD, artist, second_font_color, font)

    # Draw 2 triangles, flipped
    triangleB, triangleD = df.backgroundPNG(35*20, 51*20)
    triangleD.polygon([0,0,0,triangleB.height,triangleB.width,triangleB.height//2],
        fill=font_color)
    triangleB, triangleD = df.resize(triangleB, 35, 51)
    canvasB = df.pasteItem(canvasB, triangleB, 475, 282)
    triangleB = df.rotate(triangleB, 180)
    canvasB = df.pasteItem(canvasB, triangleB, 219, 282)

    # Pause button line
    pauseB, pauseD = df.backgroundPNG(15*20, 75*20, font_color)
    pauseB = df.roundCorners(pauseB, 5*20)

    # Pasting them for pause button
    pauseB, pauseD = df.resize(pauseB, 15, 75)
    canvasB = df.pasteItem(canvasB, pauseB, 336, 270)
    canvasB = df.pasteItem(canvasB, pauseB, 373, 270)

    # Using pause lines for previous and next song
    pauseB, pauseD = df.resize(pauseB, 7, 45)
    canvasB = df.pasteItem(canvasB, pauseB, 219-pauseB.width//2, 307-pauseB.height//2)
    canvasB = df.pasteItem(canvasB, pauseB, 511-pauseB.width//2, 307-pauseB.height//2)

    # Writing time signature
    # Adding a 0 to minutes if missing
    font = df.fontDefiner(font_path, 30)

    # Converting 42% of the total in elapsed
    # From lenght to seconds to datetime to lenght again
    lenght = datetime.strptime(lenght, "%M:%S")
    real = "0"+str(lenght.minute) if len(str(lenght.minute)) == 1 else str(lenght.minute)
    real += ":" + str(lenght.second)
    df.drawText(950, 443, canvasD, real, font_color, font, "rt")

    lenght = timedelta(hours=lenght.hour, minutes=lenght.minute, seconds=lenght.second)
    lenght = lenght.total_seconds()/100*42/60
    lenght = str(lenght).split(".")
    minutes = lenght[0] if len(lenght[0]) == 2 else "0" + lenght[0]
    seconds = str(int(60 * float("0."+lenght[1])))
    seconds = seconds if len(seconds) == 2 else "0" + seconds
    #lenght = timedelta(seconds=lenght)
    
    real = minutes + ":" + seconds
    df.drawText(50, 443, canvasD, real, font_color, font)


    #lenght2 = datetime.strptime(lenght, "%M:%S")


    # Drawing all line for song duration
    lineB, _ = df.backgroundPNG(900*20, 5*20, font_color)
    lineB = df.roundCorners(lineB, 4*20)
    lineB = df.setOpacity(lineB, 50)
    lineB, _ = df.resize(lineB, 900, 5)
    canvasB = df.pasteItem(canvasB, lineB, 50, 419)

    # Drawing elapsed time of song
    lineB, _ = df.backgroundPNG(383*20, 5*20, font_color)
    lineB = df.roundCorners(lineB, 4*20)
    lineB, _ = df.resize(lineB, 383, 5)
    canvasB = df.pasteItem(canvasB, lineB, 50, 419)

    heart = b'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'
    heartB = Image.open(io.BytesIO(base64.b64decode(heart))).convert('RGBA')

    if font_color != '#FFFFFF':
        #heartB = df.deleteOpaque(heartB)
        heartB = df.resizeToFit(heartB, heartB.width*20,resample=Image.ANTIALIAS)[0].convert("RGBA")
        heartB = df.fillWithColor(heartB, font_color)
        heartB = df.resizeToFit(heartB, heartB.width//20, resample=Image.ANTIALIAS)[0]
    canvasB = df.pasteItem(canvasB, heartB, 78, 282)

    remove(cover)
    
    return image


if __name__ == "__main__":
    if len(argv) < 4 or len(argv) > 4:
        print("Error in parsing arguments\nUse python cardMaker.py \"song\" \"artist\" \"path\\filename without extension\"")
        exit(1)
    image = main(*argv[1:])
    image.save(argv[:-1]+".png", optimize=True)
