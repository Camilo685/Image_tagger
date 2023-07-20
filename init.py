import sys
from main import main
from Image_organizer import main as image_organizer_main

if __name__ == "__main__":
	if main():
		os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
	image_organizer_main()
