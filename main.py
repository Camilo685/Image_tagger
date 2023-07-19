import sys, os, functions, wx
from github import Github

windows = False
from_script = True

def main():
	executable_name = "image_organizer" if not windows else "image_organizer.exe"
	display_icon_list = ["previous", "play", "next", "pause"]	
	exe_last_commit = ""

	try:
		if not from_script:
			g = Github()
			repo = g.get_repo("Camilo685/Image_tagger")
			exe_commits = repo.get_commits(path = executable_name)
			exe_last_commit = exe_commits[0].commit.committer.date
	except:
		None

	to_dump = [exe_last_commit, display_icon_list]
	update = False
	
	try:
		data = functions.save_load_file(op_type = "rb")
		to_dump += data[2:]
	except:
		app = wx.App()
		ok_folder = False
		while not ok_folder:
			with wx.DirDialog(parent = None, message = "Choose a folder to save your images...") as dirdialog:
				if dirdialog.ShowModal() == wx.ID_CANCEL:
					sys.exit("Closing the program")
				pathname = dirdialog.GetPath() + "/"
				try:
					with open(pathname + "test", "w") as fp:
						None
				except:
					wx.GenericMessageDialog(parent = None, message = "Folder selected can't be written on, please select a diferent one", caption = "Warning!", style = wx.OK | wx.CENTRE).ShowModal()
				else:
					os.remove(pathname + "/test")
					pathname += "image_folder/"
					ok_folder = True
		to_dump.append(pathname)
		to_dump.append(pathname + ".temp_folder/")
		to_dump.append(os.getcwd() + "/.thumbs/img_thumbs/")
		to_dump.append(os.getcwd() + "/.thumbs/img_thumbs/.temp/")
		to_dump.append(os.getcwd() + "/.thumbs/icons/")
		app.Destroy()
		folders = [fld_nm for fld_nm in to_dump[2:]]

		for folder in folders:
			if not os.path.isdir(folder):
				os.makedirs(folder)

		functions.save_load_file(to_dump = to_dump)
		update = True if not from_script else False
	else:
		change = False
		if exe_last_commit and data[0] != exe_last_commit:
			update = True if not from_script else False
			change = True
		if data[4] != (os.getcwd() + "/.thumbs/img_thumbs/"):
			data[4] = os.getcwd() + "/.thumbs/img_thumbs/"
			data[5] = os.getcwd() + "/.thumbs/img_thumbs/.temp/"
			data[6] = os.getcwd() + "/.thumbs/icons/"
			change = True
		if change:
			functions.save_load_file(to_dump = to_dump)

	missing_icons = functions.update_information(display_icon_list = display_icon_list, icons_folder = to_dump[6], update = update, from_script = from_script, exe_name = executable_name)

	return update

if __name__ == "__main__":
	main()
