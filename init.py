import sys
from main import main
from Image_organizer import main as image_organizer_main

if __name__ == "__main__":
	tmp = sys.executable
	if main():
		os.execl(tmp, tmp, * sys.argv)
	image_organizer_main()
