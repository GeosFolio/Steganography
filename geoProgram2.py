import sys
import getopt
import random
import os
from cryptography.fernet import Fernet
from PIL import Image
from math import ceil
from io import BytesIO

class binaryDistributor:
    def __init__(self, binaryList):
        self.i = 0
        self.binaryList = binaryList
        self.capacity = len(binaryList)
    def isEmpty(self):
        return (self.i >= self.capacity)
    def getCapacity(self):
        return self.capacity
    def getNextChars(self, n):
        if ((self.i + n) <= self.capacity):
            nextChars = self.binaryList[self.i:self.i+n]
            self.i += n
            print(f"Encoding Next Chars: {nextChars}")
            return nextChars
        else:
            remainingChars = self.capacity - self.i
            requiredPadding = n - remainingChars
            nextChars = self.binaryList[self.i:]
            self.i += remainingChars
            #pad 0's
            if requiredPadding > 0:
                for p in range(requiredPadding):
                    print("Padding a 0")
                    nextChars = nextChars + '0'
            return nextChars

def main(argv):
    # Handle Command Line Arguments
    print("Handling command line arguments...")
    fileName = None
    bitsPerPixel = None
    payloadFileName = None
    crypt = False
    encrypted = 'n'
    try:
        opts, args = getopt.getopt(argv, "f:b:p:n")
    except:
        print("Option Error")
        sys.exit(1)
    for opt, arg in opts:
        if opt in ['-f']:
            fileName = arg
        elif opt in ['-b']:
            bitsPerPixel = int(arg)
        elif opt in ['-p']:
            payloadFileName = arg
        elif opt in ['-n']:
            crypt = True
            encrypted = 'y'
    if (bitsPerPixel > 24 | bitsPerPixel < 1 | bitsPerPixel is None):
        bitsPerPixel = int(input("Enter bits per pixel: (1-24)"))
    if (fileName is None):
        fileName = input("Filename not provided. Please provide it now: ")
    if (payloadFileName is None):
        payloadFileName = input("Payload file name not provided. Please provide it now: ")
    # Handle Cover image
    print("Accessing cover image...")
    mod = bitsPerPixel % 3
    div = ceil(bitsPerPixel / 3)
    coverWidth = 0
    coverHeight = 0
    try:
        #print(f"Opening Cover Image {fileName}")
        coverImage = Image.open(fileName)
        coverWidth, coverHeight = coverImage.size
        coverPixelMap = coverImage.load()
        embeddedImage = Image.new(mode="RGB", size=(coverWidth, coverHeight))
        embeddedPixelMap = embeddedImage.load()
    except:
        print("Error opening coverImage")
        sys.exit(1)
    
    # Construct Payload Here
    print("Constructing payload...")
    out = BytesIO()
    payloadInBytes = None
    payloadFileWidth = 0
    payloadFileHeight = 0
    if (".png" in payloadFileName):
        # Handle Payload as png file
        with Image.open(payloadFileName) as payload:
            payloadFileWidth, payloadFileHeight = payload.size
            payload.save(out, format="png")
        payloadInBytes = out.getvalue()
    else:
        # Handle Payload as non-image file
        with open(payloadFileName, "rb") as payload:
            payloadInBytes = payload.read()
    #print(f"Payload in bytes: {payloadInBytes}")
    if crypt:
        print("Optional encryption selected. Encrypting payload...")
        key = Fernet.generate_key()
        print(f"Encryption key: {key} Successfully created...")
        with open('encryptionKey.key', 'wb') as filekey:
            filekey.write(key)
        filekey.close()
        fernet = Fernet(key)
        payloadInBytes = fernet.encrypt(payloadInBytes)
        print(f"The encrypted payload: {payloadInBytes}")
    print("Encoding payload in base 2...")
    payloadEncodedBase2 = "".join([format(n, '08b') for n in payloadInBytes])
    #print(f"Payload encoded base 2: {payloadEncodedBase2}")

    # Payload Header: payloadFileType/size of embedded message/dimensions/
    print("Creating payload header...")
    PAD_LENGTH = 50
    if (len(payloadFileName) > 15):
        print("Payload file name longer than 15 characters. Swapping name with 'payload'")
        payloadFileName = 'payload' + os.path.splitext(payloadFileName)[1]
    header = f'{len(payloadEncodedBase2)}${payloadFileWidth}${payloadFileHeight}$' + \
            payloadFileName + '$' + encrypted + '$'
    requiredPadding = PAD_LENGTH - len(header)
    print(f"Required padding for header: {requiredPadding}")
    padding = ''
    for p in range(requiredPadding):
        padding = padding + f'{p%2}'
    padding = ''.join(random.sample(padding, len(padding)))
    header = header + padding[:-1] + '$'
    print("Padded header: " + header)
    print(f"Length of str header: {len(header)}")
    encodedHeader = str.encode(header)
    encodedHeaderBase2 = "".join([format(h, '08b') for h in encodedHeader])
    print(f"Encoded header: {encodedHeaderBase2}")

    # Create Binary Distributor
    print("Creating Binary Distributor...")
    bd = binaryDistributor(encodedHeaderBase2 + payloadEncodedBase2)
    bitsToBeSent = len(payloadEncodedBase2) + len(encodedHeaderBase2)
    availableBits = coverWidth * coverHeight * bitsPerPixel
    if bitsToBeSent > availableBits:
        print(f"Bits to be sent: {bitsToBeSent} Available bits: {availableBits}")
        print("Selected payload is too large for selected cover image." \
              + "Please increase the chosen bits per pixel or select a larger cover image")
        sys.exit(1)
    for x in range(coverWidth):
        for y in range(coverHeight):
            if (x == 0 and y == 0):
                # encode bits per pixel into first pixel
                print("Encoding bits per pixel into first pixel...")
                print(f"Bits per pixel: {bitsPerPixel}")
                encodedBitsPerPixel = format(bitsPerPixel, '05b')
                print(f"Encoded bits per pixel: {encodedBitsPerPixel}")
                red, green, blue = coverPixelMap[x, y]
                print(f'Red: {red} Green: {green} Blue: {blue}')
                red = format(red, '08b')[:-2] + encodedBitsPerPixel[0:2]
                green = format(green, '08b')[:-2] + encodedBitsPerPixel[2:4]
                blue = format(blue, '08b')[:-1] + encodedBitsPerPixel[-1:]
                print("Bits per pixel embedded in RGB")
                print(f'Red: {red} Green: {green} Blue: {blue}')
                embeddedPixelMap[x, y] = (int(red, 2), int(green, 2), int(blue, 2))
                print("Embedding payload into cover image...")
                continue
            if bd.isEmpty():
                embeddedPixelMap[x, y] = coverPixelMap[x, y]
                continue
            red, green, blue = coverPixelMap[x, y]
            red = format(red, '08b')
            green = format(green, '08b')
            blue = format(blue, '08b')
            print(f"Before Embedding: Red {red} Green {green} Blue {blue}")
            red = red[:-div] + bd.getNextChars(div)
            if mod == 1:
                # mod 1 means change r (g-(div-1)) (b-(div-1))
                if (div > 1):
                    if not bd.isEmpty():
                        green = green[:-(div-1)] + bd.getNextChars(div-1)
                    if not bd.isEmpty():
                        blue = blue[:-(div-1)] + bd.getNextChars(div-1)
            elif mod == 2:
                # mod 2 means change r g (b-(div-1))
                if not bd.isEmpty():
                    green = green[:-div] + bd.getNextChars(div)
                if (div > 1):
                    if not bd.isEmpty():
                        blue = blue[:-(div-1)] + bd.getNextChars(div-1)
            else:
                # mod 0 means change r g b
                if not bd.isEmpty():
                    green = green[:-div] + bd.getNextChars(div)
                if not bd.isEmpty():
                    blue = blue[:-div] + bd.getNextChars(div)
            print(f"After Embedding: Red {red} Green {green} Blue {blue}")
            embeddedPixelMap[x, y] = (int(red, 2), int(green, 2), int(blue, 2))
    embeddedImage.save("EmbeddedImage.png")
    
if __name__ == '__main__':
    main(sys.argv[1:])