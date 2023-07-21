import sys, os
from main import main
from Image_organizer import main as image_organizer_main

if __name__ == "__main__":
	if not len(sys.argv) > 1:
		update_b, exe_n = main()
		if update_b:
			os.execv(sys.executable, [sys.executable, os.getcwd() + "/" + exe_n] + ["(old)" + exe_n])
	else:
		os.remove(os.getcwd() + "/" + sys.argv[-1])
	image_organizer_main()
