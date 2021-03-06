"""

conversions.py

@author: derricw

Bunch of random conversion functions.

"""

from PIL import Image, ImageOps, ImageDraw, ImageFont
import numpy as np
from bisect import bisect
import random
import os
import cv2
import matplotlib.pyplot as plt
from misc import *

RESOURCE_DIR = os.path.join(os.path.dirname(__file__),'res')

GREYSCALE_RANDOM = [
    " ",
    ". ",
    ",-",
    "_ivc=!/|\\~",
    "gjezt*+",
    "2](YL)[T7Vf",
    "mdK4",
    "mdK4ZGbN",
    "DXY5P"
    "#%$"
    "W8KMA",

    ]

GREYSCALE_UNIFORM = [
    " ",
    ".",
    "'",
    "-",
    ":",
    ";",
    "!",
    "~",
    "*",
    "+",
    "e",
    "m",
    "6",
    "8",
    "g",
    "#",
    "W",
    "M",
    "@",
]

BINS = [15, 25, 45, 60, 75, 90, 100, 115, 135, 155, 170, 185, 205, 220, 235,
        245, 250]

ASPECTCORRECTIONFACTOR = 6.0/11.0  # because text pixels are rectangular


def image_to_ascii(img, scalefactor=0.2, invert=False, equalize=True):
    """
    Generates and ascii string from an image of some kind.

    Parameters
    ----------
    img : str, ndarray, PIL.Image
        Image to convert
    scalefactor : float
        ASCII chars per pixel
    invert : bool
        Invert luminance?
    equalize : bool
        Equalize histogram?

    Returns
    -------
    str

    Examples
    --------

    >>> ascii_img = image_to_ascii("http://i.imgur.com/l2FU2J0.jpg", scalefactor=0.3)
    >>> print(ascii_img)

    """
    if type(img) == str:
        img = open_pil_img(img)
        text = pil_to_ascii(img, scalefactor, invert, equalize)
    elif type(img) == np.ndarray:
        #text = numpy_to_ascii(img, scalefactor, invert, equalize)  #WHY IS THIS SLOWER?
        text = pil_to_ascii(numpy_to_pil(img), scalefactor, invert, equalize)
    else:
        try:
            pil_to_ascii(img, scalefactor, invert, equalize)
        except:
            raise TypeError("That image type doesn't work.  Try PIL, Numpy, or file path...")
    return text


def pil_to_ascii(img, scalefactor=0.2, invert=False, equalize=True):
    """
    Generates an ascii string from a PIL image.

    Parameters
    ----------
    img : PIL.Image
        PIL image to transform.
    scalefactor : float
        ASCII characters per pixel
    invert : bool
        Invert luminance?
    equalize : bool
        equalize histogram (for best results do this)

    Returns
    -------
    str

    Examples
    --------

    >>> from asciisciit.misc import open_pil_img
    >>> img = open_pil_img("http://i.imgur.com/l2FU2J0.jpg")
    >>> text_img = pil_to_ascii(img, scalefactor=0.3)
    >>> print(text_img)

    >>> from PIL import Image
    >>> img = Image.open("some_image.png")
    >>> text_img = pil_to_ascii(img)
    >>> print(text_img)

    """
    img = img.resize((int(img.size[0]*scalefactor), 
        int(img.size[1]*scalefactor*ASPECTCORRECTIONFACTOR)),
        Image.BILINEAR)
    img = img.convert("L")  # convert to mono
    if equalize:
        img = ImageOps.equalize(img)

    if invert:
        img = ImageOps.invert(img)

    text = "\n"

    ##TODO: custom LUT
    lut = GREYSCALE_UNIFORM

    #SLOW ##TODO: USE Image.point(lut) instead
    for y in range(0, img.size[1]):
        for x in range(0, img.size[0]):
            lum = img.getpixel((x, y))
            row = bisect(BINS, lum)
            character = lut[row]
            text += character
        text += "\n"

    return text


def ascii_to_pil(text, font_size=10, bg_color=(20, 20, 20),
                 fg_color=(255, 255, 255), font_path=None):
    """
    Renders Ascii text to an Image of the appropriate size, using text of the
        specified font size.

    Parameters
    ----------
    text : str
        Ascii text to render.
    font_size : int (10)
        Font size for rendered image.
    bg_color : tuple (20,20,20)
        (R,G,B) values for image background.
    fg_color : tuple (255,255,255)
        (R,G,B) values for text color.
    font_path : str
        Use a custom font .ttf file.

    Returns
    -------
    PIL.Image

    Examples
    --------

    >>> ascii = AsciiImage("http://i.imgur.com/l2FU2J0.jpg", scalefactor=0.4)
    >>> pil = ascii_to_pil(ascii.data)
    >>> pil.show()

    """
    #font = ImageFont.load_default()
    if not font_path:
        font_path = os.path.join(RESOURCE_DIR, "Cousine-Regular.ttf")

    font = ImageFont.truetype(font_path, font_size)
    font_width, font_height = font.getsize(" ")  # shape of 1 char

    img_height, img_width = get_ascii_image_size(text)

    out_img = np.zeros((font_height*img_height, font_width*img_width, 3),
                       dtype=np.uint8)
    out_img[:, :, 0] += bg_color[0]
    out_img[:, :, 1] += bg_color[1]
    out_img[:, :, 2] += bg_color[2]

    img = Image.fromarray(out_img)
    draw = ImageDraw.Draw(img)

    for index, line in enumerate(text.split("\n")):
        y = (font_height)*index
        draw.text((0, y), line, fg_color, font=font)
    return img


def ascii_seq_to_gif(seq, output_path, fps=15.0, font_size=10):
    try:
        from images2gif import writeGif
    except ImportError as e:
        raise RuntimeError("Writing gifs requires images2gif library.\nTry 'pip install images2gif' %s" % e)

    images = []

    status = StatusBar(len(seq), text="Generating frames: ",)

    for index, ascii_img in enumerate(seq):
        if type(ascii_img) == str:
            #raw text
            text = ascii_img
        else:
            #AsciiImage instance
            text = ascii_img.data
        images.append(ascii_to_pil(text, font_size=font_size))
        status.update(index)

    status.complete()

    duration = 1.0/fps

    writeGif(output_path, images, duration)


def numpy_to_ascii(img, scalefactor=0.2, invert=False, equalize=True):
    """
    Generates and ascii string from a numpy image.

    SLOW FOR SOME REASON SO I DONT USE IT.

    """
    size = img.shape 

    img=cv2.resize(img, (int(size[1]*scalefactor), 
        int(size[0]*scalefactor*ASPECTCORRECTIONFACTOR)))

    img = cv2.cvtColor(img,cv2.cv.CV_RGB2GRAY)

    if equalize:
        img=cv2.equalizeHist(img)

    if not invert:
        img = 255-img

    text="\n"

    lut = GREYSCALE_UNIFORM

    #SLOW REWRITE USING ONLY NUMPY
    for y in range(img.shape[0]):
        for x in range(img.shape[1]):
            lum=img[y,x]
            row=bisect(BINS,lum)
            character=lut[row]
            text+=character
        text+="\n"

    return text


def image_to_numpy(path):
    """
    Image file to numpy matrix.
    """
    img = open_pil_img(path)
    return np.array(img, dtype=np.uint8)

def numpy_to_pil(nparray):
    """
    Numpy matrix to PIL Image.
    """
    return Image.fromarray(nparray)


def gif_to_numpy(gif_path):
    """
    Converts a GIF into a numpy movie.
    """
    gif = open_pil_img(gif_path)
    length = get_length_of_gif(gif)

    size = gif.size
    
    status = StatusBar(length, "Reading frames: ")

    frames = []
    frame_count = 0
    while gif:
        new_img = Image.new("RGBA",size)
        new_img.paste(gif)
        frames.append(new_img)
        frame_count += 1
        try:
            gif.seek(frame_count)
        except EOFError:
            break
        status.update(frame_count)

    status.complete()

    assert(length==len(frames))

    final_frame_count = len(frames)
    frame1 = np.array(frames[0])
    shape = frame1.shape
    matrix = np.zeros((final_frame_count,shape[0],shape[1],shape[2]), dtype=np.uint8)
    for i, frame in enumerate(frames):
        img = np.asarray(frame)
        matrix[i] = img
    return matrix

def figure_to_numpy(mpl_figure):
    """
    Converts a matplotlib figure to numpy matrix.
    """
    mpl_figure.tight_layout(pad=0.1)
    mpl_figure.canvas.draw()
    data = np.fromstring(mpl_figure.canvas.tostring_rgb(), dtype=np.uint8, sep='')
    data = data.reshape(mpl_figure.canvas.get_width_height()[::-1]+ (3,))
    return data

def figure_to_ascii(mpl_figure):
    """
    Converts a matplotlib figure to ascii image.
    """
    npy_fig = figure_to_numpy(mpl_figure)
    return image_to_ascii(npy_fig, scalefactor=0.15, invert=False, equalize=False)


if __name__ == '__main__':
    pass
