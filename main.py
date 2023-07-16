import sys, os, functions, wx
from github import Github

###Pickle structure###
#[exe_last_commit, display_icon_list, program_folder, tmp_folder, thumbs_folder, temp_thumbs_folder, icons_folder]

def main():
	from_script = True
	executable_name = "image_organizer"
	#display_icon_list = ["previous.png", "play.png", "next.png", "pause.png", "stop.png"]
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
		to_dump += data[1:]
	except:
		app = wx.App()
		ok_folder = False
		while not ok_folder:
			with wx.DirDialog(parent = None, message = "Choose a folder to save your images...") as dirdialog:
				if dirdialog.ShowModal() == wx.ID_CANCEL:
					sys.exit("Closing the program")
				pathname = dirdialog.GetPath() + "/"
				try:
					with open("test", "w") as fp:
						None
				except:
					wx.GenericMessageDialog(parent = None, message = "Folder selected can't be written on, please select a diferent one", caption = "Warning!", style = wx.OK | wx.CENTRE).ShowModal()
				else:
					os.remove(os.getcwd() + "/test")
					pathname += "image_folder/"
					ok_folder = True
		to_dump.append(pathname)
		to_dump.append(pathname + ".temp_folder/")
		to_dump.append(os.getcwd() + "/.thumbs/img_thumbs/")
		to_dump.append(os.getcwd() + "/.thumbs/img_thumbs/.temp/")
		to_dump.append(os.getcwd() + "/.thumbs/icons/")
		app.Destroy()
		functions.save_load_file(to_dump = to_dump)
		update = True if not from_script else False
	else:
		if exe_last_commit and data[0] != exe_last_commit:
			update = True if not from_script else False
			functions.save_load_file(to_dump = to_dump)

	missing_icons = functions.update_information(display_icon_list = display_icon_list, icons_folder = to_dump[6], update = update, from_script = from_script, exe_name = executable_name)

	return update

if __name__ == "__main__":
	main()
