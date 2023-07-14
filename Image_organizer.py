import wx, os, json, shutil, send2trash, random, uuid
import wx.lib.statbmp as wxbmp
import pathlib
import functions
from PIL import Image, ImageDraw
from pubsub import pub

###Shared variables###
display_icon_list = functions.retrieve_variables(0)
program_folder = functions.retrieve_variables(1)
icons_folder = functions.retrieve_variables(2)
print("updated2")
######################
tmp_folder = os.path.abspath("image_folder/.temp_folder/") + "/"
thumbs_folder = os.path.abspath(".thumbs/img_thumbs/") + "/"
temp_thumbs_folder = os.path.abspath(".thumbs/img_thumbs/.temp/") + "/"
folders = [program_folder, tmp_folder, icons_folder, thumbs_folder, temp_thumbs_folder]
image_dataset_name = "dataset_test"
tag_dataset_name = "tag_dataset"

for folder in folders:
	if not os.path.isdir(folder):
		os.makedirs(folder)
	
def tag_count(tag_list, working_tag_list = None, add = True):
	ret = True
	if working_tag_list == None:
		ret = False
		global complete_tag_dataset
		working_tag_list = complete_tag_dataset
	for tag in tag_list:
		if tag in working_tag_list.keys():
			if add:
				working_tag_list[tag] += 1
			else:
				if working_tag_list[tag] - 1 == 0:
					del working_tag_list[tag]
				else:
					working_tag_list[tag] -= 1
		else:
			working_tag_list[tag] = 1
	if ret:
		return working_tag_list

def write_load_json(op_type, json_name, to_dump = None):
	with open("{}.json".format(json_name), op_type) as json_file:
		if op_type == "r":
			data = json.load(json_file)
			return data
		else:
			tmp = json.dumps(dict(sorted(to_dump.items())), indent = 4)
			json_file.write(tmp + "\n")

def add_to_data(img_selected, images_source, original_tag_box, review_bool = False):
	if img_selected[1]:
		img_name = img_selected[0]
		complete_dataset[img_name]["Box_tags"].clear()
		complete_dataset[img_name]["Empty_tags"].clear()				
	else:		
		img_split = img_selected[0].split(".")
		unique_name_bool = False
		tmp_key = [dict_key.split(".")[0] + "." for dict_key in complete_dataset.keys()]
		while not unique_name_bool:
			img_name = uuid.uuid4().hex + "."			
			if img_name not in tmp_key:
				unique_name_bool = True				
				img_name = img_name + img_split[-1]
		n_nm_split = img_name.split(".")
		shutil.move(images_source + img_selected[0], program_folder + img_name)
		if images_source != program_folder:			
			shutil.move(temp_thumbs_folder + img_split[0] + "_100." + img_split[-1], thumbs_folder + n_nm_split[0] + "_100." + n_nm_split[-1])
			shutil.move(temp_thumbs_folder + img_split[0] + "_100_msk." + img_split[-1], thumbs_folder + n_nm_split[0] + "_100_msk." + n_nm_split[-1])
			shutil.move(temp_thumbs_folder + img_split[0] + "_200." + img_split[-1], thumbs_folder + n_nm_split[0] + "_200." + n_nm_split[-1])
			shutil.move(temp_thumbs_folder + img_split[0] + "_200_msk." + img_split[-1], thumbs_folder + n_nm_split[0] + "_200_msk." + n_nm_split[-1])
		
		complete_dataset[img_name] = {"Box_tags" : {}, "Empty_tags" : []}
	
	for new_entries in original_tag_box:
		if len(original_tag_box[new_entries]) > 1:
			try:
				complete_dataset[img_name]["Box_tags"][original_tag_box[new_entries][0]] += [original_tag_box[new_entries][1]]
			except:
				complete_dataset[img_name]["Box_tags"][original_tag_box[new_entries][0]] = [original_tag_box[new_entries][1]]
		else:
			complete_dataset[img_name]["Empty_tags"].append(original_tag_box[new_entries][0])
	if review_bool:
		img_selected[0] = img_name
		img_selected[1] = True
		return img_selected
	else:
		return

def img_to_bmp(img, select_mask = False, alpha = False):
	wd, ht = img.size	
	return (wx.Bitmap.FromBufferRGBA(wd, ht, img.tobytes())) if alpha else (wx.Bitmap.FromBuffer(wd, ht, img.tobytes()))
	
def check_mask(img_list, deleted_imgs = False, images_source = None, width = 100):
	src = tmp_folder if deleted_imgs else images_source if images_source else program_folder
	thb_fd = thumbs_folder if not images_source else temp_thumbs_folder
	
	for img in img_list:
		splt = img.split(".")
		if not os.path.exists(thb_fd + splt[0] + "_" + str(width) + "_msk." + splt[-1]):
			functions.thumb(img, width, new_name = splt[0] + "_" + str(width) + "_msk." + splt[-1], source = src, target_folder = thb_fd, mask = True)
			functions.thumb(img, width, new_name = splt[0] + "_" + str(width) + "." + splt[-1], source = src, target_folder = thb_fd)
			width = int(width / 2 if width == 200 else width * 2)
			functions.thumb(img, width, new_name = splt[0] + "_" + str(width) + "_msk." + splt[-1], source = src, target_folder = thb_fd, mask = True)
			functions.thumb(img, width, new_name = splt[0] + "_" + str(width) + "." + splt[-1], source = src, target_folder = thb_fd)

def split_name(name, images_source = None, mask = False, wd = 200):
	thb_scr = temp_thumbs_folder if images_source else thumbs_folder
	splt_nm = name.split(".")
	name = thb_scr + splt_nm[0] + "_" + str(wd) + "_msk." + splt_nm[-1] if mask else thb_scr + splt_nm[0] + "_" + str(wd) + "." + splt_nm[-1]
	return name
	
def tag_loop(key, unique = True):
	###Gets the tags for the image###
	tmp_lst = []
	for tag_key in complete_dataset[key]["Box_tags"].keys():
		if unique:
			if not tag_key in tmp_lst:
				tmp_lst.append(tag_key)
		else:
			###Appends however many there are of the same tag###
			for x in range(0, len(complete_dataset[key]["Box_tags"][tag_key])):
				tmp_lst.append(tag_key)
	for tag_key in complete_dataset[key]["Empty_tags"]:
		if unique:
			if not tag_key in tmp_lst:
				tmp_lst.append(tag_key)
		else:
			tmp_lst.append(tag_key)
	return tmp_lst

class OpenImageDialog(wx.FileDialog):
	def __init__(self, message, parent = None, defaultDir = ""):
		super().__init__(parent = parent, message = message, defaultDir = defaultDir, wildcard = "All Images|*.jpeg;*.jpg;*.png;*.bmp|JP(E)G|*.jpeg;*.jpg|PNG|*.png|BMP|*.bmp", style = wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
		
class OpenDirectoryDialog(wx.DirDialog):
	def __init__(self, message, parent = None, defaultPath = ""):
		super().__init__(parent = parent, message = message, defaultPath = defaultPath, style = wx.DD_DIR_MUST_EXIST)
		
class MyList(wx.ListCtrl):
	def __init__(self, col_info, height = 400, parent = None, style = wx.LC_REPORT | wx.LC_HRULES):
		super().__init__(parent = parent, size = (-1, height), style = style)

		self.image_list = wx.ImageList(16, 16)

		unmarked_checkbox_bitmap = wx.Bitmap(wx.Image(icons_folder + "unmarked_checkbox.png"), wx.BITMAP_TYPE_ANY)
		marked_checkbox_bitmap = wx.Bitmap(wx.Image(icons_folder + "marked_checkbox.png"), wx.BITMAP_TYPE_ANY)
		
		self.image_list.Add(unmarked_checkbox_bitmap)
		self.image_list.Add(marked_checkbox_bitmap)
		self.SetImageList(self.image_list, wx.IMAGE_LIST_SMALL)

		for index, col_name in enumerate(col_info):
			self.InsertColumn(col = index, heading = col_name[0], format = wx.LIST_FORMAT_CENTER, width = col_name[2])
			if col_name[1]:
				self.SetColumnImage(index, 0)

class GeneralMessage(wx.GenericMessageDialog):
	def __init__(self, message, yes_lb = "", no_lb = "", parent = None, caption = "Warning!", style = wx.OK | wx.CENTRE):
		super().__init__(parent = parent, message = message, caption = caption, style = style)
		
		if yes_lb:
			self.SetYesNoLabels(yes_lb, no_lb)
		
class GeneralRichMessage(wx.RichMessageDialog):
	def __init__(self, message, chk_box_msg, parent = None, caption = "Warning!", style = wx.OK | wx.CANCEL | wx.CENTER):
		super().__init__(parent = parent, message = message, caption = caption, style = style)
		
		self.ShowCheckBox(chk_box_msg)

class MainFrame(wx.Frame):    
	def __init__(self):
		super().__init__(parent=None, title='Image tagger', style= wx.CAPTION | wx.MINIMIZE_BOX | wx.CLOSE_BOX, name = "MainFrame")
		
		pub.subscribe(self.general_tag_listener, "general_tag_listener")
		
		self.general_tags = []
		self.cancel_bool = False
		
		main_panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		add_box = wx.StaticBox(main_panel, wx.ID_ANY, "Add")
		add_box_sizer = wx.StaticBoxSizer(add_box, wx.VERTICAL)
		
		add_folder = wx.Button(main_panel, -1, label = "Open folder...", name = "add_folder")
		add_folder.Bind(wx.EVT_BUTTON, self.on_add_image)
		add_image = wx.Button(main_panel, -1, label = "Open image(s)...", name = "add_image")
		add_image.Bind(wx.EVT_BUTTON, self.on_add_image)
		
		add_box_sizer.Add(add_folder, 0, wx.ALL, 5)
		add_box_sizer.Add(add_image, 0, wx.EXPAND | wx.ALL, 5)
		
		display_box = wx.StaticBox(main_panel, wx.ID_ANY, "Display")
		display_box_sizer = wx.StaticBoxSizer(display_box, wx.VERTICAL)
		
		self.search_img = wx.Button(main_panel, -1, "Search images")
		self.search_img.Bind(wx.EVT_BUTTON, self.on_search)
		self.random_img = wx.Button(main_panel, -1, "Open random image")
		self.random_img.Bind(wx.EVT_BUTTON, self.on_random)
		
		global complete_dataset
		global complete_tag_dataset

		try:
			complete_dataset = write_load_json("r", image_dataset_name)
		except:
			write_load_json("w", image_dataset_name, to_dump = {})
			complete_dataset = write_load_json("r", image_dataset_name)
		
		try:
			complete_tag_dataset = write_load_json("r", tag_dataset_name)
		except:
			write_load_json("w", tag_dataset_name, to_dump = {})
			complete_tag_dataset = write_load_json("r", tag_dataset_name)
		
		self.check_img_data_exits()
		
		icon_list = functions.is_image(path_name = icons_folder, check = True)
		
		for icon_idx, icon in enumerate(display_icon_list):
			for icon_file in icon_list:
				if icon in icon_file:
					display_icon_list[icon_idx] = [icon, wx.Bitmap(wx.Image(icons_folder + icon_file, wx.BITMAP_TYPE_ANY))]
					break
		
		self.check_empty()
		
		display_box_sizer.Add(self.search_img, 0, wx.EXPAND | wx.ALL, 5)
		display_box_sizer.Add(self.random_img, 0, wx.EXPAND | wx.ALL, 5)
		
		main_sizer.Add(add_box_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		main_sizer.Add(display_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
		
		main_panel.SetSizer(main_sizer)
		main_sizer.Fit(self)
		self.Center()
		self.Show()
	
	def check_img_data_exits(self):
		#Check if there are images not saved in the program folder#
		tmp_list = functions.is_image(check = True)
		deleted = False
		added = False
		
		del_item = [img_key for img_key in complete_dataset.keys() if img_key not in tmp_list]
		if del_item:
			deleted = True
			for dl_itm in del_item:
				print(dl_itm)
				tag_count(tag_loop(dl_itm, unique = False), add = False)
				del complete_dataset[dl_itm]
		for n_s_img in tmp_list:
			if n_s_img not in complete_dataset.keys():
				added = True						
				add_to_data([n_s_img, False], program_folder, {0 : ["?"]})
				tag_count(["?"])

		if added or deleted:
			write_load_json("w", image_dataset_name, to_dump = complete_dataset)
			write_load_json("w", tag_dataset_name, to_dump = complete_tag_dataset)
		
		tmp_list = tmp_list if not added else functions.is_image(check = True)
		
		check_mask(tmp_list)
			
		thb_list = functions.is_image(path_name = thumbs_folder, check = True)
		
		if len(thb_list)/4 != len(tmp_list):
			for sv_img in tmp_list:
				for thmb in thb_list.copy():
					if sv_img.split(".")[0] == thmb.split("_")[0]:
						thb_list.remove(thmb)
			for del_thmb in thb_list:
				os.remove(thumbs_folder + del_thmb)
		
	def check_empty(self):
		if not len(complete_dataset) > 0:
			self.search_img.Disable()
			self.random_img.Disable()
		else:
			self.search_img.Enable()
			self.random_img.Enable()
		
	def on_search(self, event):
		SearchFrame(parent = self)
		self.Hide()
		self.Bind(wx.EVT_SHOW, self.on_show)
		
	def on_random(self, event):
		img_keys = []
		for key in complete_dataset.keys():
			img_keys.append([key, True])
		DisplayFrame(img_keys, to_edit_bool = False, parent = self, random_img = True)
		self.Hide()
		self.Bind(wx.EVT_SHOW, self.on_show)

	def on_add_image(self, event):
		event_object = event.GetEventObject()
		images_selected = []
		pathname = ""
		until_cancel = True
		wrn_msg = "Selected folder is already included in the program, please choose a different one"
		if event_object.GetName() == "add_folder":
			while until_cancel:
				with OpenDirectoryDialog("Choose a folder...", parent = self) as dirdialog:
					if dirdialog.ShowModal() == wx.ID_CANCEL:
						return
					pathname = dirdialog.GetPath() + "/"
					if pathname == program_folder:
						GeneralMessage(wrn_msg, parent = self).ShowModal()
					else:
						until_cancel = False
			images_selected = functions.is_image(pathname)			
		else:
			while until_cancel:
				with OpenImageDialog("Choose image(s)...", parent = self) as imgdialog:
					if imgdialog.ShowModal() == wx.ID_CANCEL:
						return
					selected_lst = imgdialog.GetPaths()
					pathname = os.path.abspath(os.path.dirname(selected_lst[0])) + "/"
					if pathname == program_folder:
						GeneralMessage(wrn_msg, parent = self).ShowModal()
					else:
						until_cancel = False
						for image in selected_lst:						
							image_split = image.split("/")
							images_selected.append([image_split[-1], False])
							
		if images_selected:
			self.on_new_image(pathname, images_selected)
		else:
			GeneralMessage("Selected folder is doesn't have images", parent = self).ShowModal()
			return
		
	def on_new_image(self, pathname, images_selected):
		first_it = True
		self.current_tags = []			
		for key in complete_tag_dataset.keys():
			self.current_tags.append(key)
		while not self.cancel_bool:
			if first_it:
				msg = "Would you like to add a general tag to the image(s) selected?"
				first_it = False
			else:
				msg = "Would you like to add another tag?"
			answer = GeneralMessage(msg, parent = self, caption = "General tag", style = wx.CANCEL | wx.YES_NO | wx.CENTRE).ShowModal()
			if answer == wx.ID_YES:
				TagDialog(self, 4, descriptive_tags = self.general_tags).ShowModal()
			elif answer == wx.ID_NO:
				self.cancel_bool = True
			else: 
				return

		check_mask(list(list(zip(*images_selected.copy()))[0]), images_source = pathname)
		DisplayFrame(images_selected, to_edit_bool = True, images_source = pathname, parent = self, general_tags = self.general_tags)
		self.Hide()
		self.Bind(wx.EVT_SHOW, self.on_show)
		
	def general_tag_listener(self, tag, tag_type):
		if tag_type == 4:
			self.general_tags.append(tag)
		else:
			self.cancel_bool = True
	
	def on_show(self, event):
		self.check_empty()
		self.Unbind(wx.EVT_SHOW, handler = self.on_show)
		self.general_tags = []
		self.cancel_bool = False
		
class Minuature_frame(wx.Dialog):    
	def __init__(self, parent, to_show, deleted_imgs = False, images_source = None):
		super().__init__(parent, title = 'Minuatures', style = wx.CAPTION | wx.CLOSE_BOX)

		self.mini_listener_name = "recover_discard_listener"
		
		self.main_panel = wx.Panel(self)
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.miniature_box_grid = wx.GridSizer(cols = 5, vgap = 5, hgap = 5)
		
		self.main_sizer.Add(self.miniature_box_grid, 0, wx.ALL, 5)
		
		self.current_page = 0
		self.page_distribution = []
		self.mini_bmp_list = []
		self.deleted_imgs = deleted_imgs
		self.to_show = to_show.copy()
		self.selected_img = []
		self.images_source = images_source
		
		pg_count = 0
		if len(self.to_show) > 15:
			for n_pg in range(0, (int(len(self.to_show) / 15) + 1) if len(self.to_show) % 15 != 0 else (int(len(self.to_show) / 15))):
				self.page_distribution.append([])
		else:
			self.page_distribution.append([])

		while pg_count < len(self.page_distribution):
			self.page_distribution[pg_count] = (self.to_show[15 * pg_count: 15 * (pg_count + 1)]) if pg_count + 1 != len(self.page_distribution) else (self.to_show[15 * pg_count:])
			pg_count += 1

		self.page_population()
		
		self.recover_discard_img = wx.Button(self.main_panel, -1, label = "Recover image(s)" if self.deleted_imgs else "Discard image(s)", name = "recover_discard_img")
		self.recover_discard_img.Bind(wx.EVT_BUTTON, self.on_recover_discard)
		self.recover_discard_img.Disable()
		
		self.next_page = wx.Button(self.main_panel, -1, label = "Next page", name = "next_page")
		self.next_page.Bind(wx.EVT_BUTTON, self.next_prev)
			
		self.prev_page = wx.Button(self.main_panel, -1, label = "Previous page", name = "prev_page")
		self.prev_page.Bind(wx.EVT_BUTTON, self.next_prev)
		self.prev_page.Disable()
			
		self.btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		self.btn_sizer.Add(self.prev_page, 0, wx.ALL, 5)
		self.btn_sizer.AddStretchSpacer()
		self.btn_sizer.Add(self.recover_discard_img, 0, wx.ALL, 5)
		self.btn_sizer.AddStretchSpacer()
		self.btn_sizer.Add(self.next_page, 0, wx.ALL, 5)
		
		self.main_sizer.Add(self.btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
		
		if not len(self.page_distribution) > 1:
			self.next_page.Disable()

		self.main_panel.SetSizer(self.main_sizer)
		self.main_sizer.Fit(self)
		self.main_panel.Layout()
		self.Centre()
		
	def on_recover_discard(self, event):
		msg = "R" if self.deleted_imgs else "D"
		pub.sendMessage(self.mini_listener_name, op = msg, img_names = self.selected_img)
		self.Close()
	
	def open_img(self, event):
		pointer = (self.current_page * 15) + int(event.GetEventObject().GetName())
		pub.sendMessage(self.mini_listener_name, selected = pointer)
		self.Close()
	
	def select_img(self, event):
		idx = int(event.GetEventObject().GetName())
		for bmp in self.mini_bmp_list:
			if idx == bmp[0]:
				name = bmp[1]
				break
		if not wx.GetKeyState(wx.WXK_CONTROL):
			if self.selected_img:
				self.deselect_img(None)
		if name in self.selected_img:
			self.selected_img.remove(name)
			event.GetEventObject().SetBitmap(wx.Bitmap(wx.Image(split_name(name, images_source = self.images_source if not self.to_show[idx][-1] else None, wd = 100))))
			if not self.selected_img:
				self.main_panel.Unbind(wx.EVT_LEFT_UP, handler = self.deselect_img)
				self.recover_discard_img.Disable()
		else:
			self.selected_img.append(name)
			event.GetEventObject().SetBitmap(wx.Bitmap(wx.Image(split_name(name, images_source = self.images_source if not self.to_show[idx][-1] else None, mask = True, wd = 100))))
		
		if len(self.selected_img) == 1:
			self.main_panel.Bind(wx.EVT_LEFT_UP, self.deselect_img)
			self.recover_discard_img.Enable()
		
	def deselect_img(self, event):
		for slt_img in self.selected_img:
			for bmp in self.mini_bmp_list:
				if slt_img == bmp[1]:
					bmp[-1].SetBitmap(wx.Bitmap(wx.Image(split_name(bmp[1], images_source = self.images_source if not self.to_show[bmp[0]][-1] else None, wd = 100))))
					break
		self.selected_img.clear()
		self.recover_discard_img.Disable()
		self.main_panel.Unbind(wx.EVT_LEFT_UP, handler = self.deselect_img)
	
	def page_population(self):
		if self.page_distribution:
			self.to_show = self.page_distribution[self.current_page].copy()
			
		for idx, mini in enumerate(self.to_show):			
			if mini[0] in self.selected_img:
				mini_static_bitmap = wxbmp.GenStaticBitmap(self.main_panel, -1, bitmap = wx.Bitmap(wx.Image(split_name(mini[0], images_source = self.images_source if not mini[-1] else None, mask = True, wd = 100), wx.BITMAP_TYPE_ANY)), name = str(idx))
			else:
				mini_static_bitmap = wxbmp.GenStaticBitmap(self.main_panel, -1, bitmap = wx.Bitmap(wx.Image(split_name(mini[0], images_source = self.images_source if not mini[-1] else None, wd = 100), wx.BITMAP_TYPE_ANY)), name = str(idx))
			if not self.deleted_imgs:
				mini_static_bitmap.Bind(wx.EVT_LEFT_DCLICK, self.open_img)
			mini_static_bitmap.Bind(wx.EVT_LEFT_UP, self.select_img)			
			self.mini_bmp_list.append([idx, mini[0], mini_static_bitmap])
			self.miniature_box_grid.Add(mini_static_bitmap, 0, wx.ALIGN_CENTER)
		
	def next_prev(self, event):
		self.miniature_box_grid.Clear()
		for bitmap in self.mini_bmp_list:
			bitmap[-1].Destroy()
			
		self.mini_bmp_list.clear()
		
		if event.GetEventObject().GetName() == "next_page":
			self.current_page += 1
		else:
			self.current_page -= 1
			
		self.page_population()
		
		if self.current_page > 0:
			self.prev_page.Enable()
		else:
			self.prev_page.Disable()
		if self.current_page + 1 >= len(self.page_distribution):
			self.next_page.Disable()
		else:
			self.next_page.Enable()		
		
		self.main_sizer.Fit(self)
		self.main_panel.Layout()
			
class SearchFrame(wx.Frame):    
	def __init__(self, parent = None):
		super().__init__(parent = parent, title = 'Search images', style = wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE & ~(wx.RESIZE_BORDER), name = "SearchFrame")
		
		####Main panel and sizer####		
		self.sf_main_panel = wx.Panel(self)
		main_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		############################
		
		####Variables####	
		pub.subscribe(self.show_listener, "show_listener")
			
		global complete_dataset
		global complete_tag_dataset
		
		self.selected_bool = False
		self.x_1, self.y_1, self.x_2, self.y_2 = -1, -1, -1, -1
		self.last_added = []
		self.grid_szr_info = []
		self.offset_info = [0, 0, 0, 0, 0, 0]
		
		self.dataset = []
		self.include_exclude_list = [[],[]]
		self.checkbox_state = []
		self.current_static_bitmaps = []
		self.clicked_images = []
		self.page_distribution = []
		self.current_page = 0
		self.delete_message_bool = False
		
		#################	

		####Load tags and dataset####
		self.load_dataset(first_load = True)
		self.temp_tag_list = self.copy_tag_list()	

		##############################

		####Initial state of checkboxes####
		for tag in complete_tag_dataset.keys():
			self.checkbox_state.append([tag, 0, 0])
			
		###################################
		
		####Grid panel####
		
		self.grid_panel = wx.Panel(self.sf_main_panel)		
		self.grid_panel.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)

		images_box = wx.StaticBox(self.grid_panel, wx.ID_ANY, "Preview")
		images_box_sizer = wx.StaticBoxSizer(images_box, wx.VERTICAL)
		
		self.images_box_grid = wx.GridSizer(cols = 5, vgap = 5, hgap = 5)
		
		self.next_pg_btn = wx.Button(self.grid_panel, -1, label = "Next page", name = "next_pg_btn")
		self.next_pg_btn.Bind(wx.EVT_BUTTON, self.next_prev_btn)
		
		self.prev_pg_btn = wx.Button(self.grid_panel, -1, label = "Previous page", name = "prev_pg_btn")
		self.prev_pg_btn.Bind(wx.EVT_BUTTON, self.next_prev_btn)
		self.prev_pg_btn.Disable()
		
		nx_pv_sizer = wx.BoxSizer(wx.HORIZONTAL)
		nx_pv_sizer.Add(self.prev_pg_btn, 0, wx.EXPAND | wx.ALL, 5)
		nx_pv_sizer.AddStretchSpacer()
		nx_pv_sizer.Add(self.next_pg_btn, 0, wx.EXPAND | wx.ALL, 5)
		
		images_box_sizer.Add(self.images_box_grid, 0, wx.EXPAND | wx.ALL, 5)
		images_box_sizer.Add(nx_pv_sizer, 0, wx.EXPAND | wx.ALL, 5)
		
		self.grid_panel.SetSizer(images_box_sizer)

		######################
		
		####Create and load tag list####

		col_info = [["Include", False, 95], ["Tags", False, 120], ["Exclude", False, 95]]
		self.tag_selection_list = MyList(col_info, parent = self.sf_main_panel)
		self.tag_selection_list.Bind(wx.EVT_LEFT_UP, handler = self.checkbox_clicked)
		del col_info
		
		self.tag_population()
		
		#######################

		####Add search textbox and checkboxes####
		
		self.search_t = wx.TextCtrl(self.sf_main_panel)
		self.Bind(wx.EVT_TEXT, self.search_txt)
		
		checkbox_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.include_all = wx.CheckBox(self.sf_main_panel, label = "Include all tags", name = "Include_all")
		self.include_all.Bind(wx.EVT_CHECKBOX, self.check_all)
		
		self.exclude_all = wx.CheckBox(self.sf_main_panel, label = "Exclude all tags", name = "Exclude_all")
		self.exclude_all.Bind(wx.EVT_CHECKBOX, self.check_all)
		
		checkbox_sizer.Add(self.include_all, 0, wx.ALL, 5)
		checkbox_sizer.AddStretchSpacer()
		checkbox_sizer.Add(self.exclude_all, 0, wx.ALL, 5)
		
		#########################################
		
		####Add open, edit, delete and debug buttons####
		
		open_edit_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.open_btn = wx.Button(self.sf_main_panel, -1, label = "Display image(s)", name = "Open_image")
		self.open_btn.Bind(wx.EVT_BUTTON, self.on_open_edit)
		self.open_btn.Disable()
		
		self.edit_btn = wx.Button(self.sf_main_panel, -1, label = "Edit image(s)", name = "Edit_image")
		self.edit_btn.Bind(wx.EVT_BUTTON, self.on_open_edit)
		self.edit_btn.Disable()
		
		open_edit_sizer.Add(self.open_btn, 0, wx.ALL, 5)
		open_edit_sizer.AddStretchSpacer()
		open_edit_sizer.Add(self.edit_btn, 0, wx.ALL, 5)
		
		self.delete_img = wx.Button(self.sf_main_panel, -1, label = "Delete image(s)", name = "Delete_image")
		self.delete_img.Bind(wx.EVT_BUTTON, self.on_delete)
		self.delete_img.Disable()
		
		self.debug = wx.Button(self.sf_main_panel, -1, label = "Debug", name = "Debug")
		self.debug.Bind(wx.EVT_BUTTON, self.debugger)
		
		tag_box = wx.StaticBox(self.sf_main_panel, wx.ID_ANY, "Search...")
		tag_box_sizer = wx.StaticBoxSizer(tag_box, wx.VERTICAL)
		
		tag_box_sizer.Add(self.search_t, 0, wx.EXPAND | wx.ALL, 5)
		tag_box_sizer.Add(checkbox_sizer, 0, wx.EXPAND | wx.ALL, 5)
		tag_box_sizer.Add(self.tag_selection_list, 0, wx.EXPAND | wx.ALL, 5)
		tag_box_sizer.Add(open_edit_sizer, 0, wx.EXPAND | wx.ALL, 5)
		tag_box_sizer.Add(self.delete_img, 0, wx.EXPAND | wx.ALL, 5)
		tag_box_sizer.Add(self.debug, 0, wx.EXPAND | wx.ALL, 5)
		
		################################################
		
		main_sizer.Add(tag_box_sizer, 0, wx.ALL, 5)
		main_sizer.Add(self.grid_panel, 0, wx.EXPAND | wx.ALL, 5)		
		
		self.sf_main_panel.SetSizer(main_sizer)
		self.sf_main_panel.Layout()
		
		self.Bind(wx.EVT_CLOSE, self.on_close)
		
		self.Show()
		self.Center()
		###Makes the window's size fixed###
		self.SetMinSize(wx.DisplaySize())
		###For some reason the image's info doesn't load properly if call immediatly###
		wx.CallLater(100, self.grid_population)
	
	def debugger(self, event):
#		print("Current tags")
#		print(self.temp_tag_list)
#		print("\n")
#		print("Include exclude list")
#		print(self.include_exclude_list)
#		print("\n")
#		print("Checkbox state")
#		print(self.checkbox_state)
#		print("\n")
#		print("Dataset")
#		print(self.dataset)
#		print("\n")
		print("Tag dataset")
		print(complete_tag_dataset)
		print("\n")		
#		print("Current bitmap")
#		print(self.current_static_bitmaps)
#		print("\n")
#		print("Images selected")
#		print(self.clicked_images)
#		print("\n")
#		print("Deleted images")
#		print(self.deleted_from_dataset)
#		print("\n")
	
	def next_prev_btn(self, event):
		if event.GetEventObject().GetName() == "next_pg_btn":
			self.current_page += 1
		else:
			self.current_page -= 1
			
		self.grid_population(page_change = True)
		
		if self.current_page > 0:
			self.prev_pg_btn.Enable()
		else:
			self.prev_pg_btn.Disable()
		if self.current_page + 1 >= len(self.page_distribution):
			self.next_pg_btn.Disable()
		else:
			self.next_pg_btn.Enable()
	
	def on_delete(self, event):
		if not self.delete_message_bool:
			delete_msg = GeneralRichMessage(message = "The image will be send to the recicled bin", chk_box_msg = "Don't show this message again", parent = self)
			answer = delete_msg.ShowModal()
			if delete_msg.IsCheckBoxChecked():
				self.delete_message_bool = True
			if answer == wx.ID_CANCEL:
				return
		###Deletes clicked images and their respective thumbs and tag info
		for to_del in self.clicked_images:
			img_name = self.dataset[to_del][0]
			tag_count(tag_loop(img_name, unique = False), add = False)
			del complete_dataset[img_name]
			send2trash.send2trash(program_folder + img_name)
			splt_nm = img_name.split(".")
			os.remove(thumbs_folder + splt_nm[0] + "_100." + splt_nm[-1])
			os.remove(thumbs_folder + splt_nm[0] + "_100_msk." + splt_nm[-1])
			os.remove(thumbs_folder + splt_nm[0] + "_200." + splt_nm[-1])
			os.remove(thumbs_folder + splt_nm[0] + "_200_msk." + splt_nm[-1])

		write_load_json("w", image_dataset_name, to_dump = complete_dataset)	
		write_load_json("w", tag_dataset_name, to_dump = complete_tag_dataset)
		self.load_dataset(deleted = self.clicked_images)
		self.grid_population()
	
	def copy_tag_list(self):
		return [tag for tag in complete_tag_dataset.keys()]
	
	def load_dataset(self, first_load = False, deleted = None, changes = None):
		if first_load:
			self.dataset.clear()
			for key in complete_dataset.keys():
				tmp_lst = tag_loop(key)
				self.dataset.append([key, tmp_lst])			
		else:
			###Delete empty tag checkboxes###
			chk_del_count = 0
			for cbidx, checkbox in enumerate(self.checkbox_state.copy()):
				if checkbox[0] not in complete_tag_dataset.keys():
					cbidx = cbidx - chk_del_count
					del self.checkbox_state[cbidx]
					chk_del_count += 1
					
					try:
						self.include_exclude_list[0].remove(checkbox[0])
					except:
						None
					try:
						self.include_exclude_list[1].remove(checkbox[0])
					except:
						None
			
			###Delete deleted entries from the dataset###
			if deleted:			
				for del_img in deleted:
					del self.dataset[del_img]
			
			###Reloads tag info from altered images###
			if changes:
				for mdf_image in changes:
					self.dataset[mdf_image][1] = tag_loop(self.dataset[mdf_image][0])
				
				###Adds new tag checkboxes###
				tmp_chk_b_list = list(list(zip(*self.checkbox_state.copy()))[0])
				for tag_key in complete_tag_dataset.keys():
					if tag_key not in tmp_chk_b_list:
						self.checkbox_state.append([tag_key, 0, 0])
												
			self.search_txt(None)
		
	def append_all(self, current_image_list, current_image):
		###Appends all dataset entries###
		tmp_cnt = 0
		for pg_num in self.page_distribution:
			for img_id in pg_num:
				image_name = self.dataset[img_id][0]
				current_image_list.append([image_name, True, img_id])
				if img_id == current_image:
					current_image = tmp_cnt
				tmp_cnt += 1
					
		return current_image_list, current_image
	
	def on_open_edit(self, event):
		to_edit_bool = False
		current_image_list = []
		current_image = 0
		####For double_clicked events####
		if event.GetEventType() == 10035:
			current_image_list, current_image = self.append_all(current_image_list, int(event.GetEventObject().GetName()))
		else:
			###For button events###
			if event.GetEventObject().GetName() == "Edit_image":
				to_edit_bool = True
			if not len(self.clicked_images) > 1:
				current_image_list, current_image = self.append_all(current_image_list, self.clicked_images[0])
			else:
				self.clicked_images.sort()
				for clk_img in self.clicked_images:
					current_image_list.append([self.dataset[clk_img][0], True, clk_img])
		DisplayFrame(current_image_list, to_edit_bool = to_edit_bool, parent = self, current_image = current_image)
		self.Hide()		
	
	def show_listener(self, changes, deleted):
		self.load_dataset(deleted = deleted, changes = changes)
		self.grid_population()
		self.Show()
		self.Center()
		
	def grid_population(self, page_change = False):
		if self.selected_bool and not page_change:
			self.on_deselected(None)
		
		###Deletes bitmaps from memory###
		for bitmap in self.current_static_bitmaps:
			bitmap[-1].Destroy()
			
		self.current_static_bitmaps.clear()		
		self.images_box_grid.Clear()
		self.grid_szr_info.clear()
		self.offset_info = [0, 0, 0, 0, 0, 0]
		
		temp_index_list = []
		if not page_change:
			self.page_distribution.clear()
			self.current_page = 0
			###No filters so adds all images as possibilities###
			if not self.include_exclude_list[0] and not self.include_exclude_list[1]:
				for index, data in enumerate(self.dataset):
					temp_index_list.append(index)
			else:
				for img_data in self.dataset:
					break_bool = False
					###Filter images that have the desired tag###
					for tag_to_include in self.include_exclude_list[0]:
						if not tag_to_include in img_data[1]:
							break_bool = True
							break
					if not break_bool:
						###Filter filtered images that don't have the undesired tag###
						for tag_to_exclude in self.include_exclude_list[1]:
							if tag_to_exclude in img_data[1]:
								break_bool = True
								break
					if not break_bool:
						temp_index_list.append(self.dataset.index(img_data))
			###Adds number of pages grouping filtered images by 15###
			pg_count = 0
			if len(temp_index_list) > 15:
				for n_pg in range(0, (int(len(temp_index_list) / 15) + 1) if len(temp_index_list) % 15 != 0 else (int(len(temp_index_list) / 15))):
					self.page_distribution.append([])
			else:
				self.page_distribution.append([])
			
			###Adds images to the pages###
			while pg_count < len(self.page_distribution):
				self.page_distribution[pg_count] = (temp_index_list[15 * pg_count: 15 * (pg_count + 1)]) if pg_count + 1 != len(self.page_distribution) else (temp_index_list[15 * pg_count:])
				pg_count += 1
			temp_index_list.clear()
			temp_index_list = self.page_distribution[self.current_page]
			
			if not len(self.page_distribution) > 1:
				self.next_pg_btn.Disable()
			else:
				self.next_pg_btn.Enable()
			
		else:
			temp_index_list = self.page_distribution[self.current_page]
		
		###For info on the displayed images, grouping images by 5###
		for x in range(0, (int(len(temp_index_list) / 5) + 1) if len(temp_index_list) % 5 != 0 else (int(len(temp_index_list) / 5))):
			self.grid_szr_info.append([])
			
		for index in temp_index_list:
			###Checks if the image was selected previously###
			if index not in self.clicked_images:
				bmp = wx.Bitmap(wx.Image(split_name(self.dataset[index][0])))
			else:
				bmp = wx.Bitmap(wx.Image(split_name(self.dataset[index][0], mask = True)))
			###Max size of the batch of images, grid determines the row height and column width by this###
			w, h = bmp.GetSize()
			if w > self.offset_info[0]:
				self.offset_info[0] = w
			if h > self.offset_info[1]:
				self.offset_info[1] = h
			###Creates a static bitmap to by displayed###
			temp_static_bitmap = wxbmp.GenStaticBitmap(self.grid_panel, -1, bitmap = bmp, name = str(index))
			temp_static_bitmap.Bind(wx.EVT_LEFT_DCLICK, self.on_open_edit)
			temp_static_bitmap.Bind(wx.EVT_LEFT_UP, self.OnImageClicked)
			###For the purpose of erasing the static images later###
			self.current_static_bitmaps.append([index, temp_static_bitmap])
			self.images_box_grid.Add(temp_static_bitmap, 0, wx.ALIGN_CENTER)
		self.sf_main_panel.Layout()
		self.grid_info()
	
	def grid_info(self):
		if self.grid_szr_info:
			tmp_count = 0
			for count, s_bmp in enumerate(self.current_static_bitmaps):
				###Determines the left top and right bottom corners of the image###
				x1, y1 = s_bmp[-1].GetPosition()
				x2, y2 = s_bmp[-1].GetSize()
				x2, y2 = x1 + x2, y1 + y2
				###To add to the corresponding row###
				if count > 0 and count % 5 == 0:
					tmp_count += 1
				self.grid_szr_info[tmp_count].append([x1, y1, x2, y2])
			
			temp_h = [self.grid_szr_info[0][x][1] for x in range(0, len(self.grid_szr_info[0]))]
			self.offset_info[3] = min(temp_h)
			
			temp_w = [self.grid_szr_info[y][0][0] for y in range(0, len(self.grid_szr_info))]
			self.offset_info[2] = min(temp_w)

			self.offset_info[4] = self.images_box_grid.GetVGap()
			self.offset_info[5] = self.images_box_grid.GetHGap()
	
	def checkbox_clicked(self, event):
		x, y  = event.GetPosition()
		include_bool = False
		exclude_bool = False
		if 0 < x and 21 > x:
			include_bool = True
			
		elif 215 < x and 236 > x:
			exclude_bool = True
		###If a checkbox was clicked###
		if include_bool or exclude_bool:			
			tag_index = self.tag_selection_list.GetFocusedItem()
			tag_text = self.tag_selection_list.GetItemText(tag_index, 1)
			for check_box in self.checkbox_state:
				if check_box[0] == tag_text:
					include = True if include_bool else False						
					check_box = self.inc_exc_list(tag_text, check_box, include = include)
					self.tag_selection_list.SetItem(tag_index, 0, "", check_box[1])
					self.tag_selection_list.SetItem(tag_index, 2, "", check_box[2])
					break
			self.include_exclude_list[0].sort()
			self.include_exclude_list[1].sort()
			self.grid_population()
			self.check_if_all()

	def inc_exc_list(self, tag_text, checkbox, include = True):
		###Updates the checkbox state in the checkbox list###
		checkbox[1 if include else 2] = 1 if not checkbox[1 if include else 2] else 0
		checkbox[2 if include else 1] = 0
		rm_idx = -1
		###Adds tag to the include or exclude list###
		if checkbox[1 if include else 2]:
			if tag_text not in self.include_exclude_list[0 if include else 1]:
				self.include_exclude_list[0 if include else 1].append(tag_text)
				rm_idx = 0 if not include else 1
		else:
			rm_idx = 1 if not include else 0
		###Removes tag###	
		if tag_text in self.include_exclude_list[rm_idx]:
			self.include_exclude_list[rm_idx].remove(tag_text)
		return checkbox
			
	def tag_population(self):
		###Repopulates the tag list with tags that fit the search value###
		self.tag_selection_list.DeleteAllItems()
		for tag_index, tag in enumerate(self.temp_tag_list):
			for item in self.checkbox_state:
				if item[0] == tag:
					self.tag_selection_list.InsertItem(tag_index, "", item[1])
					self.tag_selection_list.SetItem(tag_index, 1, item[0])
					self.tag_selection_list.SetItem(tag_index, 2, "", item[2])
					break

	def OnImageClicked(self, event):
		idx = int(event.GetEventObject().GetName())
		
		if not wx.GetKeyState(wx.WXK_CONTROL):
			if self.clicked_images:
				self.on_deselected(None)
		
		###The user un-clicked an image###		
		if idx in self.clicked_images:
			event.GetEventObject().SetBitmap(wx.Bitmap(wx.Image(split_name(self.dataset[idx][0]))))
			self.clicked_images.remove(idx)
			if not self.clicked_images:
				self.on_deselected(None)
		else:
			###The user clicked an image###
			self.clicked_images.append(idx)
			event.GetEventObject().SetBitmap(wx.Bitmap(wx.Image(split_name(self.dataset[idx][0], mask = True))))
		
		###Does this the first time an image is clicked###
		if len(self.clicked_images) == 1:
			self.selected_bool = True
			self.delete_img.Enable()
			self.open_btn.Enable()
			self.edit_btn.Enable()			
			self.sf_main_panel.Bind(wx.EVT_LEFT_UP, self.on_deselected)
			self.grid_panel.Bind(wx.EVT_LEFT_UP, self.on_deselected)
		
	def on_deselected(self, event):
		###Unselects all images###
		self.selected_bool = False
		self.open_btn.Disable()
		self.edit_btn.Disable()
		self.delete_img.Disable()
		
		for clk_img in self.clicked_images:
			for crr_s_bm in self.current_static_bitmaps:
				if clk_img == crr_s_bm[0]:
					crr_s_bm[-1].SetBitmap(wx.Bitmap(wx.Image(split_name(self.dataset[clk_img][0]))))
					break
		self.clicked_images.clear()
		self.sf_main_panel.Unbind(wx.EVT_LEFT_UP, handler = self.on_deselected)
		self.grid_panel.Unbind(wx.EVT_LEFT_UP, handler = self.on_deselected)

	def search_txt(self, event):
		###Starts with all tags and eliminates if the tag is in the include-exclude list or the text is not on the tag###
		self.temp_tag_list = self.copy_tag_list()
		for tag in self.temp_tag_list.copy():
			if self.search_t.GetValue() not in tag or tag in self.include_exclude_list[0] or tag in self.include_exclude_list[1]:
				self.temp_tag_list.remove(tag)

		self.temp_tag_list.sort()
		self.temp_tag_list = self.include_exclude_list[0] + self.include_exclude_list[1] + self.temp_tag_list
		self.tag_population()
		self.check_if_all()
		
	def check_all(self, event):
		checkbox_value = event.GetEventObject().GetValue()
		checkbox_name = event.GetEventObject().GetName()
		current_search_tag = self.search_t.GetValue()
		include = True if checkbox_name == "Include_all" else False
		
		for tag in self.temp_tag_list:
			for checkbox in self.checkbox_state:
				if checkbox[0] == tag and (not checkbox[1 if include else 2] if checkbox_value else checkbox[1 if include else 2]):
					checkbox = self.inc_exc_list(tag, checkbox, include = include)
		
		if checkbox_value:
			chk_bx = self.exclude_all if checkbox_name == "Include_all" else self.include_all
			chk_bx.SetValue(False)
		
		self.tag_population()
		self.grid_population()

	def check_if_all(self):
		###Checks if the check-all checkbox should be ticked###
		if self.temp_tag_list:
			tmp_chk = 0 if len(self.temp_tag_list) == len(self.include_exclude_list[0]) else 1 if len(self.temp_tag_list) == len(self.include_exclude_list[1]) else -1
			
			if tmp_chk != -1:
				self.include_all.SetValue(True if tmp_chk == 0 else False)
				self.exclude_all.SetValue(True if tmp_chk == 1 else False)
			else:
				self.include_all.SetValue(False)
				self.exclude_all.SetValue(False)

	def on_left_down(self, event):
		if [event.GetEventType()] == wx.EVT_LEFT_DOWN.evtType:
			self.x_1, self.y_1 = event.GetPosition()
			
			self.grid_panel.Bind(wx.EVT_MOTION, self.mouse_drag)
			self.grid_panel.Bind(wx.EVT_LEFT_UP, self.on_left_up)
			
			if not wx.GetKeyState(wx.WXK_CONTROL):
				self.on_deselected(None)
		event.Skip()
	
	def mouse_drag(self, event):
		self.x_2, self.y_2 = event.GetPosition()

		if not self.x_1 == self.x_2 and not self.y_1 == self.y_2:
			self.OnPaint()	
		event.Skip()
	
	def on_left_up(self, event):
		self.grid_panel.Refresh()
		self.x_1, self.y_1, self.x_2, self.y_2 = -1, -1, -1, -1	
		self.last_added.clear()
		self.grid_panel.Unbind(wx.EVT_MOTION, handler = self.mouse_drag)
		self.grid_panel.Unbind(wx.EVT_LEFT_UP, handler = self.on_left_up)
		if self.clicked_images:
			self.sf_main_panel.Bind(wx.EVT_LEFT_UP, self.on_deselected)
			self.grid_panel.Bind(wx.EVT_LEFT_UP, self.on_deselected)
		else:
			self.on_deselected(None)
		
	def OnPaint(self):
		dc = wx.ClientDC(self.grid_panel)
		color = wx.Colour(189, 195, 199, 100)
		dc.SetPen(wx.Pen((238, 238, 238)))
		dc.SetBrush(wx.Brush(color))
		dc.DrawRectangle(self.x_1, self.y_1, self.x_2 - self.x_1, self.y_2 - self.y_1)
		
		if self.grid_szr_info:
			self.drag_select()
	
	def drag_select(self):
		max_w, max_h, org_x, org_y, v_gap, h_gap = self.offset_info
		max_w_off = max_w + v_gap
		max_h_off = max_h + h_gap
		row_index = []
		col_index = []
		image_index = []
		row_length = len(self.grid_szr_info[0])
		
		###Check if the user is selecting from left to right and top to bottom###
		x1, x2, inv_x = (self.x_1, self.x_2, False) if self.x_1 < self.x_2 else (self.x_2, self.x_1, True)
		y1, y2, inv_y = (self.y_1, self.y_2, False) if self.y_1 < self.y_2 else (self.y_2, self.y_1, True)
		
		col_range_1 = int((x1 - org_x) / max_w_off)
		col_range_2 = int((x2 - org_x) / max_w_off) + 1
		row_range_1 = int((y1 - org_y) / max_h_off)
		row_range_2 = int((y2 - org_y) / max_h_off) + 1
		
		###Where to start looking for selected images in the grid###
		col_index = [idx_c for idx_c in range(col_range_1, col_range_2)]
		row_index = [idx_r for idx_r in range(row_range_1, row_range_2)]
		
		img_slt = []
		for h_idx in row_index:
			for w_idx in col_index:
				try:
					img_cord = self.grid_szr_info[h_idx][w_idx]
					###See if the user's selection box and the image's coordinates are overlapping###
					if max(0, min(x2, img_cord[2]) - max(x1, img_cord[0])) > 0 and max(0, min(y2, img_cord[3]) - max(y1, img_cord[1])):
						img_slt.append(((h_idx + 1) * row_length) - (row_length - w_idx))
				except:
					###In case the overlapping space doesn't have an assigned image###
					break
		
		###Check if there are changes###
		if not len(img_slt) == len(self.last_added):
			if len(img_slt) > len(self.last_added):
				self.add_to_clicked(img_slt, self.last_added)
			else:
				self.add_to_clicked(self.last_added, img_slt)
		
		self.last_added = img_slt.copy()
		
		if self.clicked_images:
			self.selected_bool = True
			self.open_btn.Enable()
			self.edit_btn.Enable()
			self.delete_img.Enable()						
		else:
			self.on_deselected(None)
		
	def add_to_clicked(self, to_it_list, to_check_list):
		for img_ix in to_it_list:
			if not img_ix in to_check_list:
				ix = self.current_static_bitmaps[img_ix][0]
				if ix in self.clicked_images:							
					self.clicked_images.remove(ix)
					self.current_static_bitmaps[img_ix][-1].SetBitmap(wx.Bitmap(wx.Image(split_name(self.dataset[ix][0]))))
				else:
					self.clicked_images.append(ix)
					self.current_static_bitmaps[img_ix][-1].SetBitmap(wx.Bitmap(wx.Image(split_name(self.dataset[ix][0], mask = True))))
	
	def on_close(self, event):
		self.GetParent().Show()
		self.Destroy()

class DisplayFrame(wx.Frame):
	def __init__(self, images_selected, to_edit_bool = False, images_source = None, parent = None, current_image = 0, general_tags = None, random_img = False):
		super().__init__(parent = parent, title = 'Display', style = wx.CAPTION | wx.MINIMIZE_BOX | wx.CLOSE_BOX, name = "DisplayFrame")
		
		####Message between frames####
		pub.subscribe(self.tag_listener, "tag_listener")
		pub.subscribe(self.mini_listener, "recover_discard_listener")

		####Main panel and sizer
		self.main_panel = wx.Panel(self)
		self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

		############# Variables #############
		self.images_source = images_source		
		self.current_image = current_image
		self.img_selected = images_selected
		self.general_tags = general_tags
		self.random = random_img
		
		global complete_dataset
		global complete_tag_dataset
		
		if self.random:
			self.current_image = random.randint(0, len(self.img_selected) - 1)
		
		###For undo-redo purposes###
		self.change_counter = 0
		self.reset_bool = False
		self.undo_list = []
		self.redo_list = []
		
		self.b_alpha = False
		self.editing_bool = False
		self.current_process = -1
		
		self.temp_tag_box_coor = []
		self.img_data_id = 0
		self.current_tag_boxes = {}
		self.current_tag_count = {}
		self.to_delete_img_list = []
		self.tag_list_content = []
		
		self.changes = []
		self.deleted = []
		
		self.display_option = 4
		
		self.delete_message_bool = False
		
		###For slide show###
		self.delay_value = 5000
		self.slide_timer = wx.Timer(self)
		self.Bind(wx.EVT_TIMER, lambda event: self.change_image(), self.slide_timer)	

		#####################################	

		############# ctrl box #############

		ctrl_box = wx.StaticBox(self.main_panel, wx.ID_ANY, "Controls")
		ctrl_box_sizer = wx.StaticBoxSizer(ctrl_box, wx.HORIZONTAL)		
		
		self.button_icon_list = display_icon_list.copy()
		
		control_buttons_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.multi_imgs = False if len(self.img_selected) == 1 else True
		
		for icon_index, icon in enumerate(self.button_icon_list):
			if not "pause" in icon[0]:
				btn = wx.BitmapButton(self.main_panel, bitmap = icon[1], name = icon[0])
				btn.Bind(wx.EVT_BUTTON, self.control_buttons)
				if not self.multi_imgs:
					btn.Disable()
				if "previous" in icon[0]:
					self.prev_btn_idx = icon_index
				elif "next" in icon[0]:
					self.nxt_btn_idx = icon_index
				else:
					self.play_btn_idx = icon_index
					if to_edit_bool:					
						btn.Disable()						
				control_buttons_sizer.Add(btn, 0, wx.ALL, 5)
				self.button_icon_list[icon_index] += [btn]
				
		display_sizer = wx.BoxSizer(wx.VERTICAL)
		display_description = wx.StaticText(self.main_panel, label = "Display options")
		
		self.display_choice = wx.Choice(self.main_panel, size = (-1, 30), choices = ["Clean image", "Display tag names", "Display boxes", "Display everything"], name = "display_description")
		self.display_choice.SetSelection(2)
		self.display_choice.Bind(wx.EVT_CHOICE, self.choice_selection)
		display_sizer.Add(display_description, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
		display_sizer.Add(self.display_choice, 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, 5)
		
		delay_sizer = wx.BoxSizer(wx.VERTICAL)
		delay_description = wx.StaticText(self.main_panel, label = "Slide show delay")
		self.delay_choice = wx.Choice(self.main_panel, size = (-1, 30), choices = ["3s", "5s", "15s"], name = "delay_description")
		self.delay_choice.SetSelection(1)
		self.delay_choice.Bind(wx.EVT_CHOICE, self.choice_selection)
		delay_sizer.Add(delay_description, 0, wx.ALIGN_CENTER | wx.BOTTOM, 5)
		delay_sizer.Add(self.delay_choice, 0, wx.ALIGN_CENTER | wx.RIGHT | wx.LEFT, 5)
										
		self.to_edit_checkbox = wx.CheckBox(self.main_panel, label = "Edit image", name = "to_edit_checkbox")
		if to_edit_bool:
			self.to_edit_checkbox.SetValue(True)
		self.to_edit_checkbox.Bind(wx.EVT_CHECKBOX, self.edit_controls)
		
		self.random_checkbox = wx.CheckBox(self.main_panel, label = "Random image", name = "random_checkbox")
		self.random_checkbox.Bind(wx.EVT_CHECKBOX, self.random_image)
		if not self.multi_imgs:
			self.random_checkbox.Disable()
		elif self.random:
			self.random_checkbox.SetValue(True)
		
		ctrl_box_sizer.Add(control_buttons_sizer, 0, wx.ALL, 5)
		ctrl_box_sizer.Add(display_sizer, 0)
		ctrl_box_sizer.Add(delay_sizer, 0)
		ctrl_box_sizer.Add(self.to_edit_checkbox, 0, wx.ALIGN_CENTER)
		ctrl_box_sizer.Add(self.random_checkbox, 0, wx.ALIGN_CENTER)

		########################################
		
		############# img box #############
		
		img_box = wx.StaticBox(self.main_panel, wx.ID_ANY, "Image")
		img_box_sizer = wx.StaticBoxSizer(img_box, wx.VERTICAL)
		
		self.img = wx.Image(240,240)
		self.s_bmp = wxbmp.GenStaticBitmap(self.main_panel, -1, bitmap = wx.Bitmap(self.img))
		
		img_box_sizer.Add(self.s_bmp, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		img_box_sizer.Add(ctrl_box_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		
		###################################	

		############# Tag box #############
		
		self.tag_box = wx.StaticBox(self.main_panel, wx.ID_ANY, "")
		self.tag_box_sizer = wx.StaticBoxSizer(self.tag_box, wx.VERTICAL)
		
		col_info = [["Tag", False, 200]]
		self.tag_list = MyList(col_info, height = 270, parent = self.main_panel)
		self.tag_list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_focus)
		self.tag_list.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.on_focus)
		
		edit_tag_box_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.edit_tag = wx.Button(self.main_panel, -1, label = "Edit tag", name = "Edit_tag")
		self.edit_tag.Bind(wx.EVT_BUTTON, self.edit_tag_btn)
		self.edit_box = wx.Button(self.main_panel, -1, label = "Edit box", name = "Edit_box")
		self.edit_box.Bind(wx.EVT_BUTTON, self.on_press)
		
		edit_tag_box_sizer.Add(self.edit_tag, 0, wx.ALL, 5)
		edit_tag_box_sizer.AddStretchSpacer()
		edit_tag_box_sizer.Add(self.edit_box, 0, wx.ALL, 5)
		
		self.delete_tag = wx.Button(self.main_panel, -1, label = "Delete tag", name = "Delete_tag")
		self.delete_tag.Bind(wx.EVT_BUTTON, self.on_delete_tag)
		
		self.add_descriptive_tag = wx.Button(self.main_panel, -1, label = "Add descriptive tag...", name = "Add_descriptive_tag")
		self.add_descriptive_tag.Bind(wx.EVT_BUTTON, self.on_press)
		
		self.debug = wx.Button(self.main_panel, -1, label = "Debug", name = "Debug")
		self.debug.Bind(wx.EVT_BUTTON, self.debugger)
		
		self.all_images = wx.Button(self.main_panel, -1, label = "Show images selected", name = "image_list")
		self.all_images.Bind(wx.EVT_BUTTON, self.show_all)
		
		self.deleted_images = wx.Button(self.main_panel, -1, label = "Show deleted images", name = "deleted_list")
		self.deleted_images.Bind(wx.EVT_BUTTON, self.show_all)
		self.deleted_images.Disable()
		
		self.delete_img = wx.Button(self.main_panel, -1, label = "Delete image", name = "delete_img")
		self.delete_img.Bind(wx.EVT_BUTTON, self.on_delete_image)
		
		self.save_btn = wx.Button(self.main_panel, -1, label = "Save", name = "Save")
		self.save_btn.Bind(wx.EVT_BUTTON, self.save_to_dataset)
		
		self.delete_tag.Disable()
		self.edit_tag.Disable()
		self.edit_box.Disable()
		
		self.tag_box_sizer.Add(self.tag_list, 0, wx.EXPAND | wx.ALL, 5)
		self.tag_box_sizer.Add(edit_tag_box_sizer, 0, wx.EXPAND | wx.ALL, 5)
		self.tag_box_sizer.Add(self.add_descriptive_tag, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.delete_tag, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.save_btn, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.debug, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.all_images, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.deleted_images, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		self.tag_box_sizer.Add(self.delete_img, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
		
		###################################
		
		############# edit box #############
		
		self.edit_btn_box = wx.StaticBox(self.main_panel, wx.ID_ANY, "Add/Edit")
		self.edit_box_sizer = wx.StaticBoxSizer(self.edit_btn_box, wx.VERTICAL)
		
		self.add_tag_btn = wx.Button(self.main_panel, -1, label = "Add tag...", name = "Add")
		self.add_tag_btn.Bind(wx.EVT_BUTTON, self.on_press)
		
		self.undo_btn = wx.Button(self.main_panel, -1, label = "Undo", name = "Undo")
		self.undo_btn.Bind(wx.EVT_BUTTON, self.undo_redo)
		self.redo_btn = wx.Button(self.main_panel, -1, label = "Redo", name = "Redo")
		self.redo_btn.Bind(wx.EVT_BUTTON, self.undo_redo)
		
		self.edit_box_sizer.Add(self.add_tag_btn, 0, wx.ALL, 5)
		self.edit_box_sizer.Add(self.undo_btn, 0, wx.EXPAND | wx.ALL, 5)
		self.edit_box_sizer.Add(self.redo_btn, 0, wx.EXPAND | wx.ALL, 5)
		
		####################################
		
		############# Load image data #############
		
		self.load_img_data()

		########################################
		
		self.Bind(wx.EVT_CLOSE, self.on_close)
		
		self.disable_enable(_init = True)
		self.edit_controls(None)
		
		self.main_sizer.Add(self.tag_box_sizer, 0, wx.ALL, 5)
		self.main_sizer.Add(img_box_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
		self.main_sizer.Add(self.edit_box_sizer, 0, wx.ALL, 5)
		
		self.main_panel.SetSizer(self.main_sizer)
		self.main_panel.Layout()
		self.main_sizer.Fit(self)
		self.Centre()
		self.Show()
	
	def show_all(self, event):
		if event.GetEventObject().GetName() == "image_list":
			mnt_frame = Minuature_frame(self, self.img_selected, images_source = self.images_source).ShowModal()
		else:
			mnt_frame = Minuature_frame(self, self.to_delete_img_list, deleted_imgs = True, images_source = self.images_source).ShowModal()
		
	def mini_listener(self, selected = -1, op = "P", img_names = None):
		if not selected == -1:
			if not self.current_image == selected:
				self.current_image = selected
				self.change_image(only_reset = True)
		else:
			if op == "D":
				discard_current = False
				for img in img_names:
					for idx, slt_img in enumerate(self.img_selected.copy()):
						if img == slt_img[0]:
							if img == self.img_selected[self.current_image][0]:
								self.discard_changes(yes_lb = "Save", no_lb = "Discard changes", style = wx.YES_NO | wx.CENTER)
								discard_current = True
							if self.current_image >= idx:
								if self.current_image != 0:
									self.current_image -= 1
							self.img_selected.remove(slt_img)
							break
				if not self.img_selected:
					self.on_close(None)
				elif discard_current:
					self.change_image(only_reset = True)
			elif op == "R":
				for img in img_names:
					for rcv_img in self.to_delete_img_list.copy():
						src_dir = program_folder if rcv_img[1] else self.images_source
						if img == rcv_img[0]:
							self.img_selected.append(rcv_img)
							self.to_delete_img_list.remove(rcv_img)
							shutil.move(tmp_folder + rcv_img[0], src_dir + rcv_img[0])
							if rcv_img[1]:
								img_split = rcv_img[0].split(".")
								shutil.move(temp_thumbs_folder + img_split[0] + "_100." + img_split[-1], thumbs_folder + img_split[0] + "_100." + img_split[-1])
								shutil.move(temp_thumbs_folder + img_split[0] + "_100_msk." + img_split[-1], thumbs_folder + img_split[0] + "_100_msk." + img_split[-1])
								shutil.move(temp_thumbs_folder + img_split[0] + "_200." + img_split[-1], thumbs_folder + img_split[0] + "_200." + img_split[-1])
								shutil.move(temp_thumbs_folder + img_split[0] + "_200_msk." + img_split[-1], thumbs_folder + img_split[0] + "_200_msk." + img_split[-1])
				
				if not self.to_delete_img_list:
					self.deleted_images.Disable()
		
	def random_image(self, event):
		self.random = self.random_checkbox.GetValue()
	
	def on_delete_image(self, event):
		#Double checks that the user wants to delete the image selected#
		if not self.delete_message_bool:
			delete_msg = delete_msg = GeneralRichMessage(message = "The image will be send to the recicled bin", chk_box_msg = "Don't show this message again", parent = self)
			answer = delete_msg.ShowModal()
			if delete_msg.IsCheckBoxChecked():
				self.delete_message_bool = True
			if answer == wx.ID_CANCEL:
				return
		
		#Checks where the image is stored#
		src_dir = program_folder if self.img_selected[self.current_image][1] else self.images_source
		#Adds the image information for possible recovery#
		self.to_delete_img_list.append(self.img_selected[self.current_image])
		
		if self.img_selected[self.current_image][1]:
			img_split = self.img_selected[self.current_image][0].split(".")
			shutil.move(thumbs_folder + img_split[0] + "_100." + img_split[-1], temp_thumbs_folder + img_split[0] + "_100." + img_split[-1])
			shutil.move(thumbs_folder + img_split[0] + "_100_msk." + img_split[-1], temp_thumbs_folder + img_split[0] + "_100_msk." + img_split[-1])
			shutil.move(thumbs_folder + img_split[0] + "_200." + img_split[-1], temp_thumbs_folder + img_split[0] + "_200." + img_split[-1])
			shutil.move(thumbs_folder + img_split[0] + "_200_msk." + img_split[-1], temp_thumbs_folder + img_split[0] + "_200_msk." + img_split[-1])
		
		#Deletes the image superficial information from the image list selection#
		del self.img_selected[self.current_image]
		#Moves the image to the program temp folder#
		shutil.move(src_dir + self.to_delete_img_list[-1][0], tmp_folder + self.to_delete_img_list[-1][0])
		#Check if there are more images to display, moves pointer to the previous image and loads the image#
		#If there are no more images closes the display#
		if self.img_selected:
			if self.current_image >= len(self.img_selected):
				self.current_image = len(self.img_selected) - 1
			self.change_image(only_reset = True)
		else:
			self.on_close(None)
		#Enable the button to see deleted images#
		self.deleted_images.Enable()
	
	def deleted_entries(self):
		#Check if there were images deleted#
		if self.to_delete_img_list:
			dict_changes = False
			#Checks if any of the deleted images were saved in the dataset#
			for deleted_image in self.to_delete_img_list:
				if deleted_image[1]:
					if self.GetParent().GetName() == "SearchFrame":
						self.deleted.append(deleted_image[-1])
					dict_changes = True
					#Substract each tag from the tag count#
					tag_count(tag_loop(deleted_image[0], unique = False), add = False)
					del complete_dataset[deleted_image[0]]
				send2trash.send2trash(tmp_folder + deleted_image[0])
			#Rewrites the dataset, if there were changes to it#
			if dict_changes:
				write_load_json("w", image_dataset_name, to_dump = complete_dataset)
				write_load_json("w", tag_dataset_name, to_dump = complete_tag_dataset)
		for temp_thumb in os.listdir(temp_thumbs_folder):
			os.remove(temp_thumbs_folder + temp_thumb)
		
	def choice_selection(self, event):
		choice_object = event.GetEventObject()
		choice_idx = choice_object.GetSelection()
		#Timer options#
		if choice_object.GetName() == "delay_description":
			if choice_idx == 0:
				self.delay_value = 3000
			elif choice_idx == 1:
				self.delay_value = 5000
			else:
				self.delay_value = 15000
			if self.slide_timer.IsRunning():
				self.slide_timer.Start(self.delay_value)
		#Redraw options#
		else:
			if choice_idx == 0:
				self.display_option = 3
			elif choice_idx == 1:
				self.display_option = 6
			elif choice_idx == 2:
				self.display_option = 4
			else:
				self.display_option = 5
			self.img_draw(self.display_option)
	
	def edit_controls(self, event):
		dis_ena_lst = [[],[]]
		if self.to_edit_checkbox.GetValue():
			self.random_checkbox.SetValue(False)
			self.random_image(None)
			if self.slide_timer.IsRunning():
				self.slide_timer.Stop()
				self.button_icon_list[self.play_btn_idx][-1].SetName("play")
				self.button_icon_list[self.play_btn_idx][-1].SetBitmap(self.button_icon_list[self.play_btn_idx][1])
				dis_ena_lst[0] += [self.delay_choice]
				dis_ena_lst[1] += [self.button_icon_list[self.prev_btn_idx][-1], self.button_icon_list[self.nxt_btn_idx][-1]]
			dis_ena_lst[0] += [self.button_icon_list[self.play_btn_idx][-1], self.random_checkbox]
			self.tag_box_sizer.ShowItems(True)
			self.edit_box_sizer.ShowItems(True)
		else:
			if not self.discard_changes():
				self.to_edit_checkbox.SetValue(True)
				return
			self.change_image(only_reset = True)
			if self.multi_imgs:	
				dis_ena_lst[1] += [self.button_icon_list[self.play_btn_idx][-1], self.delay_choice, self.random_checkbox]
			self.tag_box_sizer.ShowItems(False)
			self.edit_box_sizer.ShowItems(False)
		self.disable_enable(to_disable = dis_ena_lst[0], to_enable = dis_ena_lst[1], _init = True if self.to_edit_checkbox.GetValue() else False)
		self.main_panel.Layout()
		self.main_sizer.Fit(self)
		self.Centre()
		
	def discard_changes(self, message = "Current image has unsaved changes!", caption = "Warning!", yes_lb = "Save and go to display mode", no_lb = "Discard and go to display mode", style = wx.YES_NO | wx.CANCEL | wx.CENTER):
		if not self.change_counter == 0:
			answer = GeneralMessage(message = message, caption = caption, yes_lb = yes_lb, no_lb = no_lb, parent = self, style = style).ShowModal()
			if answer == wx.ID_CANCEL:
				return False
			elif answer == wx.ID_YES:
				self.save_to_dataset(None)
		return True
		
	def on_close(self, event):
		if event == None:
			GeneralMessage(message = "There are no more images to display/edit", parent = self, caption = "Exiting", style = wx.OK).ShowModal()
		else:
			if self.images_source:
				message = ""
				save_current = False
				save_all = False
				if not self.img_selected[self.current_image][1]:
					message = "Current image is not saved"
				elif self.change_counter != 0:
					message = "Current image has unsaved changes!"
				if message:
					answer = GeneralMessage(message = message, yes_lb = "Save", no_lb = "Discard", parent = self, style = wx.YES_NO | wx.CANCEL | wx.CENTER).ShowModal()
					if answer == wx.ID_CANCEL:
						return 
					elif answer == wx.ID_YES:
						save_current = True
					
				unsaved_bool = False
				for img in self.img_selected:
					if img[0] != self.img_selected[self.current_image][0]:
						if not img[1]:
							unsaved_bool = True
							break
				if unsaved_bool:
					answer = GeneralMessage(message = "Would you like to add the unsaved images to the dataset?", caption = "Unsaved images!", yes_lb = "Save", no_lb = "Discard", parent = self, style = wx.YES_NO | wx.CENTER).ShowModal()
					if answer == wx.ID_YES:
						save_all = True
				if save_current or save_all:
					self.save_to_dataset(None, save_current = save_current, save_all = save_all)
			else:
				if not self.discard_changes():
					return

		self.deleted_entries()
		if self.GetParent().GetName() == "SearchFrame":
			pub.sendMessage("show_listener", changes = self.changes, deleted = self.deleted)
		else:	
			self.GetParent().Show()
		self.Destroy()
		
	def control_buttons(self, event):
		dis_ena_lst = [[],[]]			
		if event.GetEventObject().GetName() == "play":
			event.GetEventObject().SetBitmap(self.button_icon_list[-1][-1])
			event.GetEventObject().SetName("pause")
			self.slide_timer.Start(self.delay_value)
			dis_ena_lst[0] += [self.button_icon_list[self.prev_btn_idx][-1], self.button_icon_list[self.nxt_btn_idx][-1]]
		elif event.GetEventObject().GetName() == "pause":
			event.GetEventObject().SetBitmap(self.button_icon_list[self.play_btn_idx][1])
			event.GetEventObject().SetName("play")
			self.slide_timer.Stop()
			dis_ena_lst[1] += [self.button_icon_list[self.prev_btn_idx][-1], self.button_icon_list[self.nxt_btn_idx][-1]]
		else:
			msg, forward_bool = ("next", True) if event.GetEventObject().GetName() == "next" else ("previous", False)			
			if not self.discard_changes(yes_lb = "Save and go to {}".format(msg), no_lb = "Discart and go to {}".format(msg)):
				return
			self.change_image(forward_bool = forward_bool)
			dis_ena_lst[0] += [self.button_icon_list[self.prev_btn_idx][-1], self.button_icon_list[self.nxt_btn_idx][-1]]
			dis_ena_lst[1] += [self.button_icon_list[self.prev_btn_idx][-1], self.button_icon_list[self.nxt_btn_idx][-1]]
		self.disable_enable(to_disable = dis_ena_lst[0], to_enable = dis_ena_lst[1])
	
	def change_image(self, only_reset = False, forward_bool = True):
		self.change_counter = 0
		self.reset_bool = False
		self.undo_list.clear()
		self.redo_list.clear()
		self.temp_tag_box_coor.clear()
		self.img_data_id = 0		
		self.current_tag_boxes.clear()
		self.current_tag_count.clear()
		self.tag_list_content.clear()
		
		if not only_reset:
			if not self.random:
				if forward_bool:
					self.current_image = self.current_image + 1 if not self.current_image + 1 == len(self.img_selected) else 0
				else:
					self.current_image = len(self.img_selected) - 1 if self.current_image == 0 else self.current_image - 1
			else:
				rnd_chk = self.current_image
				while rnd_chk == self.current_image:
					self.current_image = random.randint(0, len(self.img_selected) - 1)
		self.load_img_data()
		self.disable_enable(_init = True)

	def save_to_dataset(self, event, save_current = True, save_all = False):
		global complete_tag_dataset
		if save_current:		
			corr_list = False
			if not self.img_selected[self.current_image][1]:
				images_source = self.images_source
				corr_list = True
			else:
				images_source = program_folder
				img_idx = self.img_selected[self.current_image][-1]
				if self.GetParent().GetName() == "SearchFrame":
					if img_idx not in self.changes:
						self.changes.append(img_idx)
			img_current_data = self.current_tag_boxes if self.current_tag_boxes else {0: ["?"]}
			if not self.current_tag_boxes:
				self.current_tag_count = tag_count(["?"], working_tag_list = self.current_tag_count)
			if corr_list:
				corrected_dt = add_to_data(self.img_selected[self.current_image], images_source, img_current_data, review_bool = True)
				self.img_selected[self.current_image][0] = corrected_dt[0]
				self.img_selected[self.current_image][1] = corrected_dt[1]	
			else:
				add_to_data(self.img_selected[self.current_image], images_source, img_current_data)
					
		if save_all:
			images_source = self.images_source
			for new_img in self.img_selected:
				if not new_img[1]:
					if not new_img[0] == self.img_selected[self.current_image][0]:
						tmp_dic = {i: [t] for i, t in enumerate(self.general_tags)} if self.general_tags else {0: ["?"]}
						self.current_tag_count = tag_count(self.general_tags if self.general_tags else ["?"], working_tag_list = self.current_tag_count)
						add_to_data(new_img, images_source, tmp_dic)
		write_load_json("w", image_dataset_name, to_dump = complete_dataset)
		write_load_json("w", tag_dataset_name, to_dump = self.current_tag_count)
		complete_tag_dataset = self.current_tag_count.copy()
			
		self.change_counter = 0
		self.reset_bool = True
		self.redo_list.clear()
		self.disable_enable()
		
	def disable_enable(self, to_disable = None, to_enable = None, _init = False):
		if not to_disable:
			to_disable = []
		if not to_enable:
			to_enable = []
		if _init:
			to_disable += [x for x in [self.edit_tag, self.edit_box, self.delete_tag]]
			to_enable += [x for x in [self.tag_list, self.add_descriptive_tag, self.add_tag_btn]]
			self.tag_list.SetItemState(self.tag_list.GetFocusedItem(), 0, wx.LIST_STATE_SELECTED)
		
		for widget in to_disable:
			widget.Disable()
		for widget in to_enable:
			widget.Enable()
			
		self.img_draw(self.display_option)
		
		self.undo_btn.Disable()
		self.redo_btn.Disable()
		self.save_btn.Disable()
			
		if self.current_process == -1:
			if self.undo_list:
				self.undo_btn.Enable()
			if self.redo_list:
				self.redo_btn.Enable()
			if not self.change_counter == 0:
				self.save_btn.Enable()

	def load_img_data(self):
		img_name = self.img_selected[self.current_image][0]
		self.current_tag_count = complete_tag_dataset.copy()
		if self.img_selected[self.current_image][1]:
			for tag_name in complete_dataset[img_name]["Box_tags"]:
				for box in complete_dataset[img_name]["Box_tags"][tag_name]:
					self.current_tag_boxes[self.img_data_id] = ([tag_name, box])
					self.img_data_id += 1

			for empty_tag in complete_dataset[img_name]["Empty_tags"]:
				self.current_tag_boxes[self.img_data_id] = ([empty_tag])
				self.img_data_id += 1

			self.img = functions.thumb(self.img_selected[self.current_image][0], 1000, height = 580)
		else:
			if self.general_tags:
				tmp = []
				for empty_tag in self.general_tags:
					self.current_tag_boxes[self.img_data_id] = ([empty_tag])
					tmp.append(empty_tag)						
					self.img_data_id += 1
				self.current_tag_count = tag_count(tmp, working_tag_list = self.current_tag_count)
			
			self.img = functions.thumb(self.img_selected[self.current_image][0], 1000, source = self.images_source, height = 580)
		self.b_alpha = True if self.img_selected[self.current_image][0].split(".")[-1] == "png" else False
		self.s_bmp.SetBitmap(img_to_bmp(self.img, alpha = self.b_alpha))

		self.temp_img = self.img.copy()

		self.tag_list_content = [[self.current_tag_boxes[id_key][0], id_key] for id_key in self.current_tag_boxes.keys()]
		self.tag_list_population()

		if self.current_tag_boxes:
			self.img_draw(self.display_option)
		
		self.main_panel.Layout()
		self.main_sizer.Fit(self)
		self.Centre()
	
	def tag_list_population(self):
		self.tag_list.DeleteAllItems()
		for tag_cnt in self.tag_list_content:
			self.tag_list.InsertItem(self.tag_list.GetItemCount(), tag_cnt[0])

	def debugger(self, event):
		print("Current image's data")
		print(self.current_tag_boxes)
		print("\n")
#		print("Current tag list")
#		print(self.tag_list_content)
#		print("\n")
#		print("Full data length")
#		print(len(complete_dataset))
#		print("\n")
		print("Image list")
		print(self.img_selected)
		print("\n")
#		print("Undo list")
#		print(self.undo_list)
#		print("\n")
#		print("Redo list")
#		print(self.redo_list)
#		print("\n")
#		print("Complete tag dataset")
#		print(complete_tag_dataset)
#		print("\n")
		print("Working tag dataset")
		print(self.current_tag_count)
		print("\n")
#		print("Images deleted")
#		print(self.to_delete_img_list)
#		print("\n")
#		print("Current image index")
#		print(self.current_image)
#		print("\n")

	def on_focus(self, event):
	########10180 for listctrl selected event, 10181 for deselected########
		if 10180 == event.GetEventType():
			focus_id = self.tag_list_content[self.tag_list.GetFocusedItem()][-1]
			if len(self.current_tag_boxes[focus_id]) > 1:
				self.disable_enable(to_enable = [self.edit_tag, self.edit_box, self.delete_tag])
				self.img_draw(self.display_option, selected_index = focus_id)
			else:
				self.disable_enable(to_disable = [self.edit_box], to_enable = [self.edit_tag, self.delete_tag])
		else:
			self.disable_enable(to_disable = [self.edit_tag, self.edit_box, self.delete_tag])
			self.img_draw(self.display_option)
		
	def on_delete_tag(self, event):
		self.change_counter += 1
		delete_id = self.tag_list.GetFocusedItem()
		self.undo_list.append([self.tag_list_content[delete_id][-1], self.current_tag_boxes[self.tag_list_content[delete_id][-1]], "D"])
		self.redo_list.clear()
		self.current_tag_count = tag_count([self.current_tag_boxes[self.tag_list_content[delete_id][-1]][0]], working_tag_list = self.current_tag_count, add = False)
		del self.current_tag_boxes[self.tag_list_content[delete_id][-1]]
		del self.tag_list_content[delete_id]
		self.tag_list_population()
		self.disable_enable(_init = True)
		if len(self.undo_list[-1][1]) > 1:
			self.img_draw(self.display_option)		
			
	def edit_tag_btn(self, event):
		self.current_process = 1
		event.GetEventObject().SetLabel("Cancel")			
		self.disable_enable(to_disable = [self.add_tag_btn, self.edit_box, self.delete_tag, self.add_descriptive_tag])
		edit_id = self.tag_list_content[self.tag_list.GetFocusedItem()][-1]
		if not len(self.current_tag_boxes[edit_id]) > 1:
			descriptive_tags = [self.current_tag_boxes[key][0] for key in self.current_tag_boxes.keys() if len(self.current_tag_boxes[key]) == 1]
			self.tag_name(self.current_process, descriptive_tags = descriptive_tags, current_tag = self.current_tag_boxes[edit_id][0])
		else:
			self.tag_name(self.current_process, current_tag = self.current_tag_boxes[edit_id][0])

	def tag_listener(self, tag, tag_type):
		if self.current_process == 1:
			self.edit_tag.SetLabel("Edit tag")
		elif self.current_process == 2:
			self.add_tag_btn.SetLabel("Add tag...")
		else:
			self.add_descriptive_tag.SetLabel("Add descriptive tag...")
		if tag_type != self.current_process:
			self.img_draw(self.display_option)
		else:
			self.redo_list.clear()
			self.change_counter += 1
			if tag_type == 2 or tag_type == 3:
				self.current_tag_count = tag_count([tag], working_tag_list = self.current_tag_count)
				self.current_tag_boxes[self.img_data_id] = [tag, self.temp_tag_box_coor[0] + self.temp_tag_box_coor[1]] if tag_type == 2 else [tag]
				self.undo_list.append([self.img_data_id, self.current_tag_boxes[self.img_data_id], "C"])
				self.tag_list_content.append([tag, self.img_data_id])
				self.img_data_id += 1
			else:
				edit_id = self.tag_list_content[self.tag_list.GetFocusedItem()][-1]
				self.undo_list.append([edit_id, [self.current_tag_boxes[edit_id][0]], "T"])
				self.current_tag_count = tag_count([tag], working_tag_list = self.current_tag_count)
				self.current_tag_count = tag_count([self.current_tag_boxes[edit_id][0]], working_tag_list = self.current_tag_count, add = False)
				self.current_tag_boxes[edit_id][0] = tag
				self.tag_list_content[self.tag_list.GetFocusedItem()][0] = tag
			self.tag_list_population()
		self.bind_unbind(False)
		self.current_process = -1
		self.disable_enable(_init = True)

	def undo_redo(self, event):
		undo_bool = True if event.GetEventObject().GetName() == "Undo" else False
		self.change_counter = (self.change_counter - 1 if not self.reset_bool else self.change_counter + 1) if undo_bool else (self.change_counter + 1 if not self.reset_bool else self.change_counter - 1)
		op = self.undo_list[-1][-1] if undo_bool else self.redo_list[-1][-1]
		self.undo_redo_delete(op, undo_bool = undo_bool)
		self.disable_enable()

	def undo_redo_delete(self, op, undo_bool = True):
		append_list = self.redo_list if undo_bool else self.undo_list
		substract_list = self.undo_list if undo_bool else self.redo_list
		
		append_list.append(substract_list[-1].copy())
		
		if (op == "C" and undo_bool) or (op == "D" and not undo_bool):
			self.current_tag_count = tag_count([append_list[-1][1][0]], working_tag_list = self.current_tag_count, add = False)
			del self.current_tag_boxes[append_list[-1][0]]
			t_l_idx = self.find_tag_list_idx(append_list[-1][0])
			del self.tag_list_content[t_l_idx]
		elif (op == "C" and not undo_bool) or (op == "D" and undo_bool):
			self.current_tag_count = tag_count([append_list[-1][1][0]], working_tag_list = self.current_tag_count)
			self.current_tag_boxes[append_list[-1][0]] = append_list[-1][1].copy()
			self.tag_list_content.append([append_list[-1][1][0], append_list[-1][0]])
		elif op == "T":
			tmp_tg = substract_list[-1][1][0]
			append_list[-1][1][0] = self.current_tag_boxes[substract_list[-1][0]][0]
			self.current_tag_count = tag_count([append_list[-1][1][0]], working_tag_list = self.current_tag_count, add = False)
			self.current_tag_count = tag_count([tmp_tg], working_tag_list = self.current_tag_count)
			self.current_tag_boxes[substract_list[-1][0]][0] = tmp_tg
			t_l_idx = self.find_tag_list_idx(append_list[-1][0])
			self.tag_list_content[t_l_idx][0] = tmp_tg
		elif "B" == substract_list[-1][-1]:
			append_list[-1][1] = self.current_tag_boxes[substract_list[-1][0]][1]
			self.current_tag_boxes[substract_list[-1][0]][1] = substract_list[-1][1]
			self.img_draw(self.display_option)
		
		substract_list.pop(-1)
		
		if op != "B":
			self.tag_list_population()
			
		if ((op == "C" or op == "D") and len(append_list[-1][1]) > 1) or op == "B":
			self.img_draw(self.display_option)
	
	def find_tag_list_idx(self, idx):
		for x, y in enumerate(self.tag_list_content):
			if y[-1] == idx:
				t_l_idx = x
				break
		return t_l_idx

	def on_press(self, event):
		if event.GetEventObject().GetName() == "Edit_box":
			if event.GetEventObject().GetLabel() == "Edit box":				
				self.editing_bool = True
				event.GetEventObject().SetLabel("Cancel")
				self.bind_unbind(True)
				self.disable_enable(to_disable = [self.add_tag_btn, self.edit_tag, self.delete_tag, self.tag_list, self.add_descriptive_tag])				
				self.display_option = 4
				self.display_choice.SetSelection(2)
				self.img_draw(self.display_option, edit_index = self.tag_list_content[self.tag_list.GetFocusedItem()][-1])
			else:
				self.editing_bool = False
				event.GetEventObject().SetLabel("Edit box")
				self.bind_unbind(False)
				self.disable_enable(_init = True)
				self.img_draw(self.display_option)

		elif event.GetEventObject().GetName() == "Add":
			if event.GetEventObject().GetLabel() == "Add tag...":
				event.GetEventObject().SetLabel("Cancel")
				self.bind_unbind(True)
				self.disable_enable(to_disable = [self.edit_box, self.edit_tag, self.delete_tag, self.tag_list, self.add_descriptive_tag])
				self.display_option = 4
				self.display_choice.SetSelection(2)
				self.img_draw(self.display_option)
			else:
				event.GetEventObject().SetLabel("Add tag...")
				self.bind_unbind(False)
				self.disable_enable(_init = True)
				self.img_draw(self.display_option)
		else:
			if event.GetEventObject().GetLabel() == "Add descriptive tag...":
				self.current_process = 3
				event.GetEventObject().SetLabel("Cancel")
				self.disable_enable(to_disable = [self.edit_box, self.edit_tag, self.delete_tag, self.tag_list, self.add_tag_btn])
				descriptive_tags = [self.current_tag_boxes[key][0] for key in self.current_tag_boxes.keys() if not len(self.current_tag_boxes[key]) > 1]
				self.tag_name(self.current_process, descriptive_tags = descriptive_tags)
				

	def bind_unbind(self, active):
		if active:
			self.Bind(wx.EVT_CHAR_HOOK, self.key_event)
			self.s_bmp.Bind(wx.EVT_LEFT_DOWN, self.tag_creation)
			self.s_bmp.Bind(wx.EVT_LEFT_UP, self.tag_creation)
		else:
			self.Unbind(wx.EVT_CHAR_HOOK, handler = self.key_event)
			self.s_bmp.Unbind(wx.EVT_LEFT_DOWN, handler = self.tag_creation)
			self.s_bmp.Unbind(wx.EVT_LEFT_UP, handler = self.tag_creation)
			self.s_bmp.Unbind(wx.EVT_MOTION, handler = self.mouse_movement)

	def key_event(self, event):
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			if self.add_tag_btn.GetLabel() == "Cancel":
				self.add_tag_btn.SetLabel("Add tag...")
				self.current_process = -1
			elif self.edit_box.GetLabel() == "Cancel":
				self.editing_bool = False
				self.edit_box.SetLabel("Edit box")
			self.bind_unbind(False)
			self.disable_enable(_init = True)
			self.temp_tag_box_coor.clear()
			self.img_draw(self.display_option)
		event.Skip()

	def tag_creation(self, event):
		x, y = event.GetPosition()
		if [event.GetEventType()] == wx.EVT_LEFT_DOWN.evtType:			
			if not self.temp_tag_box_coor:
				self.temp_tag_box_coor.append([x, y])
				self.s_bmp.Bind(wx.EVT_MOTION, self.mouse_movement)
		else:
			if not x == self.temp_tag_box_coor[0][0] and not y == self.temp_tag_box_coor[0][-1]:
				x, y = self.check_boundaries(x, y)
				self.temp_tag_box_coor.append([x, y])
			if len(self.temp_tag_box_coor) > 1:
				self.img_draw(2, self.temp_tag_box_coor[0] + self.temp_tag_box_coor[-1])
				if self.editing_bool:
					self.editing_bool = False
					edit_id = self.tag_list_content[self.tag_list.GetFocusedItem()][-1]
					self.undo_list.append([edit_id, self.current_tag_boxes[edit_id][1], "B"])
					self.current_tag_boxes[edit_id][1] = self.temp_tag_box_coor[0] + self.temp_tag_box_coor[1]
					
					self.bind_unbind(False)
					self.edit_box.SetLabel("Edit box")
					self.change_counter += 1
					self.redo_list.clear()
					self.disable_enable(_init = True)
				else:
					self.current_process = 2
					self.tag_name(self.current_process)
				
				self.temp_tag_box_coor.clear()

	def tag_name(self, tag_type, descriptive_tags = None, current_tag = ""):
		TagDialog(parent = self, tag_type = tag_type, tags = self.current_tag_count, descriptive_tags = descriptive_tags, current_tag = current_tag).ShowModal()
	
	def check_boundaries(self, w, h):
		if w < 0:
			w = 0
		elif w > self.img.width:
			w = self.img.width - 1
		if h < 0:
			h = 0
		elif h > self.img.height:
			h = self.img.height - 1
		return w, h

	def mouse_movement(self, event):
		wm, hm = event.GetPosition()
		wp, hp = self.temp_tag_box_coor[0]
		
		wm, hm = self.check_boundaries(wm, hm)

		if not wm == wp and not hm == hp:
			self.img_draw(1, [wm, hm, wp, hp])
		event.Skip()

	def img_draw(self, draw_type, drawing_coordinates = None, selected_index = -1, edit_index = -1):
		###Drawing types
		#1 = Temporary
		#2 = Update
		#3 = Clean
		#4 = Refresh
		#5 = All
		#6 = Tag
		###
		if draw_type == 1:
			img = self.temp_img.copy()
			draw = ImageDraw.Draw(img)
			draw.rectangle(drawing_coordinates, outline = "white", width = 2)
			self.s_bmp.SetBitmap(img_to_bmp(img, alpha = self.b_alpha))
		elif draw_type == 2:
			draw = ImageDraw.Draw(self.temp_img)
			draw.rectangle(drawing_coordinates, outline = "white", width = 2)
		else:
			self.temp_img = self.img.copy()
			draw = ImageDraw.Draw(self.temp_img)
			if draw_type == 3: 
				if selected_index == -1:				
					self.s_bmp.SetBitmap(img_to_bmp(self.img, alpha = self.b_alpha))
				else:
					draw.rectangle(self.current_tag_boxes[selected_index][1], outline = "yellow", width = 2)
					self.s_bmp.SetBitmap(img_to_bmp(self.temp_img, alpha = self.b_alpha))
			else:
				boxes = [[],[]]
				for id_key in self.current_tag_boxes.keys():
					if len(self.current_tag_boxes[id_key]) > 1:
						if edit_index != id_key:
							color = "yellow" if not selected_index == -1 and selected_index == id_key else "white"									
							boxes[0].append([self.current_tag_boxes[id_key][-1], color])
							
							temp_x = (self.current_tag_boxes[id_key][-1][0] + self.current_tag_boxes[id_key][-1][2]) / 2
							temp_y = -1
							top = 1 if self.current_tag_boxes[id_key][-1][1] < self.current_tag_boxes[id_key][-1][-1] else -1
							
							if self.current_tag_boxes[id_key][-1][top] - 15 < 0:
								temp_y = self.current_tag_boxes[id_key][-1][top] + 10 if self.current_tag_boxes[id_key][-1][-top] + 15 > self.img.height else self.current_tag_boxes[id_key][-1][-top] + 10
							else:
								temp_y = self.current_tag_boxes[id_key][-1][top] - 10
							
							boxes[1].append([(temp_x, temp_y), self.current_tag_boxes[id_key][0], color])
				
				self.draw_box_or_text(draw_type, draw, boxes)									
				self.s_bmp.SetBitmap(img_to_bmp(self.temp_img, alpha = self.b_alpha))
		self.main_panel.Layout()
	
	def draw_box_or_text(self, draw_type, draw, coordinates):
		if draw_type == 4 or draw_type == 5:
			for coor in coordinates[0]:
				draw.rectangle(coor[0], outline = coor[1], width = 2)
		if draw_type == 5 or draw_type == 6:
			for coor in coordinates[1]:
				draw.text(coor[0], coor[1], fill = coor[2])
			
class TagDialog(wx.Dialog):    
	def __init__(self, parent = None, tag_type = 1, tags = None, descriptive_tags = None, current_tag = ""):
		super().__init__(parent, title = "Edit tag", style = wx.CAPTION | wx.CENTER)
		
		###Tag types###
		
		#Edit tag = 1
		#New tag = 2
		#New descriptive tag = 3
		#General tag = 4
		#Cancel = 5
		
		###############
		self.main_panel = wx.Panel(self)
		self.main_sizer = wx.BoxSizer(wx.VERTICAL)
		
		####Variables####
		global complete_tag_dataset
		
		self.tags = [key for key in (complete_tag_dataset.keys() if not tags else tags.keys())]
		self.temp_tags = []
		
		self.tag_type = tag_type
		self.descriptive_tags = descriptive_tags
		self.current_tag = current_tag		
		self.tag_listener_name = "tag_listener" if self.tag_type != 4 else "general_tag_listener"		
		self.tag_msg = ""
		
		font = wx.Font(10, family = wx.DEFAULT, style = wx.NORMAL, weight = wx.NORMAL, underline = False, encoding = wx.FONTENCODING_DEFAULT)
		
		if self.tag_type != 1:
			self.SetTitle("Add tag name" if self.tag_type == 2 else "Add new descriptive tag" if self.tag_type == 3 else "Add general tag")
		
		if self.descriptive_tags:
			for tag in self.descriptive_tags:
				if tag in self.tags:
					self.tags.remove(tag)
		
		#################

		self.listbox_tags = wx.ListBox(self.main_panel, size = (-1, 200), choices = self.tags, style = wx.LB_SINGLE | wx.LB_NEEDED_SB | wx.LB_SORT)
		self.listbox_tags.Bind(wx.EVT_LISTBOX, self.on_select)
		self.listbox_tags.SetFont(font)
		
		txt_btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
		
		self.text = wx.TextCtrl(self.main_panel, size = (120, -1), style = wx.TE_PROCESS_ENTER)
		self.text.Bind(wx.EVT_TEXT_ENTER, self.enter_key_press)
		self.text.Bind(wx.EVT_TEXT, self.search_tag)
		
		self.finish_btn = wx.Button(self.main_panel, size = (50, -1), label = "Edit" if self.tag_type == 1 else "Add")
		self.finish_btn.Bind(wx.EVT_BUTTON, self.finish_editing)
		self.finish_btn.Disable()
		
		cancel_btn = wx.Button(self.main_panel, size = (60, -1), label = "Cancel")
		cancel_btn.Bind(wx.EVT_BUTTON, self.finish_editing)		
			
		txt_btn_sizer.Add(self.text, 0, wx.ALL, 5)
		txt_btn_sizer.Add(self.finish_btn, wx.EXPAND | 0, wx.ALL, 5)		
		txt_btn_sizer.Add(cancel_btn, 0, wx.EXPAND | wx.ALL, 5)
		
		self.error_message = wx.StaticText(self.main_panel, style = wx.ALIGN_CENTER) 
		
		self.Bind(wx.EVT_CHAR_HOOK, self.key_event)
		
		self.main_sizer.Add(txt_btn_sizer, 0, wx.EXPAND | wx.ALL, 5)
		self.main_sizer.Add(self.error_message, 0, wx.EXPAND | wx.ALL, 5)
		self.main_sizer.Add(self.listbox_tags, 0, wx.EXPAND | wx.ALL, 5)
		
		self.main_panel.SetSizer(self.main_sizer)
		self.main_sizer.Fit(self)
		self.main_panel.Layout()
		self.Centre()
	
	def key_event(self, event):
		if event.GetKeyCode() == wx.WXK_ESCAPE:
			self.on_close("", 5)
		event.Skip()
		
	def search_tag(self, event):
		self.tag_msg = event.GetString()
		tmp_dump = []
		
		if self.tag_msg:
			self.finish_btn.Enable()
			index = 0
			while index < self.listbox_tags.GetCount():
				if not self.tag_msg in self.listbox_tags.GetString(index):
					tmp_dump.append(self.listbox_tags.GetString(index))
					self.listbox_tags.Delete(index)
				else:
					index = index + 1
			index = 0
			while index < len(self.temp_tags):
				if self.tag_msg in self.temp_tags[index]:
					self.listbox_tags.Append(self.temp_tags[index])
					self.temp_tags.pop(index)
				else:
					index = index + 1
			
			self.check_descriptive_tags()
		else:
			self.finish_btn.Disable()
			self.listbox_tags.Set(self.tags)
			self.temp_tags.clear()

		self.temp_tags = self.temp_tags + tmp_dump
		self.main_panel.Layout()
		self.main_sizer.Fit(self)
		
	def finish_editing(self, event):
		if event.GetEventObject().GetLabel() == "Cancel":
			self.on_close("", 5)
		else:
			self.tag_msg = self.text.GetValue()
			if self.tag_msg:
				self.on_close(self.tag_msg, self.tag_type)
	
	def check_descriptive_tags(self):
		same_tag_msg = "Tag is the same as the tag being edited, \npress cancel to keep the current tag or select a different one"
		exist_tag_msg = "Tag selected already exist as a descriptive tag, \nplease choose a diferent one"
		self.error_message.SetLabel("")
		return_bool = True
		if self.descriptive_tags:
			for descriptive_tag in self.descriptive_tags:
				if self.tag_msg == descriptive_tag:
					self.error_message.SetLabel(same_tag_msg if self.current_tag and self.tag_msg == self.current_tag else exist_tag_msg)
					self.finish_btn.Disable()
					return_bool = False
		else:
			if self.current_tag and self.tag_msg == self.current_tag:
				self.error_message.SetLabel(same_tag_msg)
				self.finish_btn.Disable()
				return_bool = False
		return return_bool
	
	def on_close(self, tag, tag_type):
		pub.sendMessage(self.tag_listener_name, tag = tag, tag_type = tag_type)
		self.Close()
		
	def enter_key_press(self, event):
		self.tag_msg = event.GetString()
		if self.tag_msg and self.check_descriptive_tags():
			self.on_close(self.tag_msg, self.tag_type)
		
	def on_select(self, event):
		self.tag_msg = self.listbox_tags.GetStringSelection()
		self.text.SetValue(self.tag_msg)

if __name__ == "__main__":
	app = wx.App()
	frame = MainFrame()
	app.MainLoop()
