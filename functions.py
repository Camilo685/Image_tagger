import os, filetype, shutil, pickle, json, stat, requests
from zipfile import ZipFile
from PIL import Image, ImageDraw

###Pickle structure###
#[exe_last_commit, display_icon_list, program_folder, tmp_folder, thumbs_folder, temp_thumbs_folder, icons_folder]
			
def save_load_file(file_name = "program_variables", to_dump = None, op_type = "wb"):
	dict_bool = True if len(file_name.split(".")) > 1 else False
	with open(file_name, op_type) as tmp_file:
		if "r" in op_type:
			return json.load(tmp_file) if dict_bool else pickle.load(tmp_file)
		else:
			if dict_bool:
				tmp = json.dumps(dict(sorted(to_dump.items())), indent = 4)
				tmp_file.write(tmp + "\n")
			else:
				pickle.dump(to_dump, tmp_file)
			
def write_load_json(op_type, json_name, to_dump = None):
	with open(json_name, op_type) as json_file:
		if op_type == "r":
			return json.load(json_file)
		else:
			tmp = json.dumps(dict(sorted(to_dump.items())), indent = 4)
			json_file.write(tmp + "\n")

def is_image(path_name = None, check = False):
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

def update_information(display_icon_list = None, icons_folder = None, update = False, from_script = False, exe_name = None):
	checkbox_icons = ["marked_checkbox", "unmarked_checkbox"]
	icon_list = is_image(path_name = icons_folder, check = True)
	missing_icons = []
	for icon_idx, icon in enumerate(display_icon_list + checkbox_icons):
		missing_bool = True
		for icon_file in icon_list:
			if icon == icon_file.split(".")[0]:
				missing_bool = False
				break
		if missing_bool:
			missing_icons.append(icon)
	
	if missing_icons or (update and not from_script):
		zip_url = "https://codeload.github.com/Camilo685/image_organizer/zip/refs/heads/main"
		zip_req = requests.get(zip_url)
		with open("tmp.zip",'wb') as zip_file:
			zip_file.write(zip_req.content)
	
		with ZipFile(os.getcwd() + "/tmp.zip", 'r') as zip_obj:
			zip_obj.extractall(path = os.getcwd())
		repo_dir = os.getcwd() + "/image_organizer-main"
		if missing_icons:
			icon_list = is_image(path_name = repo_dir + "/icons/", check = True)
			for icon_msn in missing_icons:
				for icon_file in icon_list:
					if icon_msn == icon_file.split(".")[0]:
						tmp_img = Image.open(repo_dir + "/icons/" + icon_file).convert("RGBA" if icon_file.split(".")[-1] == "png" else "RGB")
						width = 30 if tmp_img.size[0] > 30 else tmp_img.size[0]
						thumb(icon_file, width, source = repo_dir + "/icons/", target_folder = icons_folder)
						break
		if update and not from_script:
			os.remove(os.getcwd() + "/" + exe_name)
			shutil.move(repo_dir + "/" + exe_name, os.getcwd() + "/" + exe_name)
			os.chmod(os.getcwd() + "/" + exe_name, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
		shutil.rmtree(repo_dir)
	
def thumb(img_name, width, source = None, new_name = None, target_folder = None, height = -1, mask = False):
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
