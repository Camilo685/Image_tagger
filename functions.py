import os, filetype, shutil
from git import Repo
from PIL import Image, ImageDraw

#display_icon_list = ["previous.png", "play.png", "next.png", "pause.png", "stop.png"]
display_icon_list = ["previous", "play", "next", "pause"]
checkbox_icons = ["marked_checkbox", "unmarked_checkbox"]
program_folder = os.path.abspath("image_folder/") + "/"
icons_folder = os.path.abspath(".thumbs/icons/") + "/"

repo_name = "https://github.com/Camilo685/Image_tagger"
main_script_name = "Image_organizer.py"
functions_script = "functions.py"

to_retrieve = [[0, display_icon_list], [1, program_folder], [2, icons_folder], [3, main_script_name], [4, functions_script]]

def retrieve_variables(variable_id):
	for variable in to_retrieve:
		if variable[0] == variable_id:
			return variable[1]

def is_image(path_name = program_folder, check = False):
	images_selected = []
	for fl_nm in os.listdir(path_name):
		if os.path.isfile(path_name + fl_nm):
			ext = filetype.guess(path_name + fl_nm)
			if ext and "image" in ext.mime:
				splt_fl_nm = fl_nm.split(".")
				tmp_nm = ""
				if len(splt_fl_nm) > 2:
					for x in splt_fl_nm[:-1]:
						tmp_nm = tmp_nm + x
					tmp_nm = tmp_nm + "." + splt_fl_nm[-1]
					os.rename(path_name + fl_nm, path_name + tmp_nm)
				if not check:					
					images_selected.append([tmp_nm if tmp_nm else fl_nm, False])
				else:
					images_selected.append(tmp_nm if tmp_nm else fl_nm)
	return images_selected

def check_icons():
	print("functions")
	icon_list = is_image(path_name = icons_folder, check = True)
	mssng = []
	for icon_idx, icon in enumerate(display_icon_list + checkbox_icons):
		mis_bool = True
		for icon_file in icon_list:
			if icon == icon_file.split(".")[0]:
				mis_bool = False
				break
		if mis_bool:
			mssng.append(icon)
	return mssng

def update_information(missing_icons = None, to_update = None):
	repo_dir = os.getcwd() + "/temp_repo"
	Repo.clone_from(repo_name, repo_dir)
	if missing_icons:
		icon_list = is_image(path_name = repo_dir + "/icons/", check = True)
		for icon_msn in missing_icons:
			for icon_file in icon_list:
				if icon_msn == icon_file.split(".")[0]:
					tmp_img = Image.open(repo_dir + "/icons/" + icon_file).convert("RGBA" if icon_file.split(".")[-1] == "png" else "RGB")
					width = 30 if tmp_img.size[0] > 30 else tmp_img.size[0]
					thumb(icon_file, width, source = repo_dir + "/icons/", target_folder = icons_folder)
					break
	if to_update:
		for script in to_update:
			os.remove(os.getcwd() + script)
			shutil.move(repo_dir + "/" + script, os.getcwd() + "/" + script)
	shutil.rmtree(repo_dir)
	
def thumb(img_name, width, source = program_folder, new_name = None, target_folder = None, height = -1, mask = False):
	if height == -1:
		height = width
	image_type = img_name.split(".")[-1]
	image = Image.open(source + img_name).convert("RGBA" if image_type == "png" else "RGB")		
	image.thumbnail((width, height))
	
	if mask:
		if not image_type == "png":
			draw = ImageDraw.Draw(image, "RGBA")
			draw.rectangle(((0, 0), (width, height)), fill=(236, 100, 75, 127))
		else:
			tmp_draw = Image.new('RGBA', image.size, (255,255,255,0))
			draw = ImageDraw.Draw(tmp_draw)
			draw.rectangle(((0, 0), image.size), fill=(236, 100, 75, 127))
			image = Image.alpha_composite(image, tmp_draw)
	
	if target_folder:
		image.save(target_folder + (new_name if new_name else img_name))
	else:
		return image
