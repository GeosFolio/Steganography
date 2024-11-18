import sys
import getopt
from PIL import Image
def main(argv):
    print("Running Program 1.")
    fileName = None
    bitsPerPixel = None
    try:
        opts, args = getopt.getopt(argv, "f:b:")
    except:
        print("Option error")
        sys.exit(1)
    for opt, arg in opts:
        if opt in ['-f']:
            fileName = arg
        elif opt in ['-b']:
            bitsPerPixel = int(arg)
    print(f'Filename: {fileName}\nBits Per Pixel: {bitsPerPixel}')
    if fileName is None:
        print("No fileName provided")
        sys.exit(1)
    if (bitsPerPixel > 24 or bitsPerPixel < 1 or bitsPerPixel is None):
        bitsPerPixel = int(input("Enter bits per pixel: (1-24)"))
    try:
        coverImage = Image.open(fileName)
        print(f'The Maximum Payload Size for {fileName} is: {coverImage.width * coverImage.height * bitsPerPixel} bits')
    except:
        print(f'Error opening image: {fileName}')
        sys.exit(1)
if __name__ == '__main__':
    main(sys.argv[1:])
