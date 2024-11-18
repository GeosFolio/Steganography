import sys
import getopt
import os
from math import ceil
from cryptography.fernet import Fernet
from PIL import Image

def main(argv):
    # Handle Command Line Arguments
    print("Handling command line arguments...")
    fileWithData = None
    try:
        opts, args = getopt.getopt(argv, "f:")
    except:
        print("Option Error")
    for opt, arg in opts:
        if opt in ['-f']:
            fileWithData = arg
    print("Extracting image data...")
    if fileWithData is None:
        fileWithData = input("No filename provided. Please provide it now: ")
    try:
        imageWithPayload = Image.open(fileWithData)
    except:
        print(f"Error opening image. {fileWithData}")
    imageWidth, imageHeight = imageWithPayload.size
    imagePixelMap = imageWithPayload.load()
    END_OF_HEADER = (50*8)
    headerIndex = 0
    payloadIndex = 0
    endOfPayload = 0
    fileWidth = 0
    fileHeight = 0
    bitsPerPixel = 5
    mod = bitsPerPixel % 3
    div = ceil(bitsPerPixel / 3)
    header = ''
    payload = ''
    fileType = ''
    fileName = ''
    encrypted = False
    for x in range(imageWidth):
        for y in range(imageHeight):
            red, green, blue = imagePixelMap[x, y]
            red = format(red, '08b')
            green = format(green, '08b')
            blue = format(blue, '08b')
            if (x == 0 and y == 0):
                # Extract 5 bits for bits per pixel used during encoding
                print("Extracting bits per pixel information...")
                print(f"Red: {red} Green: {green} Blue: {blue}")
                bitsPerPixel = int(red[-2:] + green[-2:] + blue[-1:], 2)
                print(f"Bits per pixel: {bitsPerPixel}")
                mod = bitsPerPixel % 3
                div = ceil(bitsPerPixel / 3)
                print("Extracting header information...")
                continue
            elif (headerIndex < END_OF_HEADER):
                header = header + red[-div:]
                if mod == 1:
                    if (div > 1):
                        header = header + green[-(div-1):] + blue[-(div-1):]
                elif mod == 2:
                    header = header + green[-div:]
                    if (div > 1):
                        header = header + blue[-(div-1):]
                else:
                    header = header + green[-div:] + blue[-div:]
                headerIndex += bitsPerPixel
                print(f"Header index: {headerIndex} Bits per pixel: {bitsPerPixel} End of header: {END_OF_HEADER}")
                if headerIndex >= END_OF_HEADER:
                    shift = headerIndex - END_OF_HEADER
                    if shift > 0:
                        payload = payload + header[-shift:]
                        payloadIndex += shift
                        print(f"Header before shifting: {header}")
                        header = header[:-shift]
                        print(f"Header: {header}")
                    print(f"Done extracting header.")
                    headerInBytes = [int(header[i:i + 8], 2) for i in range(0, len(header), 8)]
                    print(f"Header in bytes: {headerInBytes}")
                    headerDecoded = bytes(headerInBytes).decode()
                    print(f"Decoded header: {headerDecoded}")
                    splitHeader = headerDecoded.split('$')
                    print(f"Split header: {splitHeader}")
                    endOfPayload = int(splitHeader[0])
                    fileWidth = int(splitHeader[1])
                    fileHeight = int(splitHeader[2])
                    fileName = splitHeader[3]
                    if splitHeader[4] == 'y':
                        encrypted = True
                    print("Extracting payload information...")
            elif (payloadIndex < endOfPayload):
                # Extract the payload
                payload = payload + red[-div:]
                if mod == 1:
                    if (div > 1):
                        payload = payload + green[-(div-1):] + blue[-(div-1):]
                elif mod == 2:
                    payload = payload + green[-div:]
                    if (div > 1):
                        payload = payload + blue[-(div-1):]
                else:
                    payload = payload + green[-div:] + blue[-div:]
                payloadIndex += bitsPerPixel
                print(f"Payload index: {payloadIndex} Bits per pixel: {bitsPerPixel} End of payload: {endOfPayload}")
                if payloadIndex >= endOfPayload:
                    print("Done extracting payload.")
                    shift = payloadIndex - endOfPayload
                    print(f"Shift: {shift}")
                    if shift > 0:
                        print("Shifting payload")
                        payload = payload[:-shift]
            else:
                break
    payloadDecoded = [int(payload[i:i + 8], 2) for i in range(0, len(payload), 8)]
    print(f"Decoded payload: {bytes(payloadDecoded)}")
    if encrypted:
        print("Encryption was used. Reading encryption key...")
        key = None
        with open('encryptionKey.key', 'rb') as keyFile:
            key = keyFile.read()
        keyFile.close()
        print("Initializing decrypter")
        fernet = Fernet(key)
        payloadDecoded = fernet.decrypt(bytes(payloadDecoded))
        print("Payload decrypted.")
        print(f"Decrypted payload: {payloadDecoded}")
    else:
        payloadDecoded = bytes(payloadDecoded)
    fileName, fileType = os.path.split(fileName)
    if (fileType == '.png'):
        image = Image.frombytes('RBG', (fileWidth, fileHeight), payloadDecoded)
        image.save(fileName + fileType)
    else:
        with open(fileName + fileType, 'wb') as payload:
            payload.write(payloadDecoded)
            
if __name__ == '__main__':
    main(sys.argv[1:])
    