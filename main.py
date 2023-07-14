import pickle, functions
from github import Github

###Pickle structure###
#[main_last_commit, functions_last_commit, main_last_commit]

def save_to_pickle(to_dump):
	with open("program_variables", "wb") as pickle_file:
		pickle.dump(to_dump, pickle_file)

def main():
	print("main3")
	image_organizer_script_name = functions.retrieve_variables(3)
	functions_script = functions.retrieve_variables(4)
	main_script = functions.retrieve_variables(5)

	g = Github()
	repo = g.get_repo("Camilo685/Image_tagger")
	image_organizer_commits = repo.get_commits(path = image_organizer_script_name)
	image_organizer_last_commit = image_organizer_commits[0].commit.committer.date

	functions_commits = repo.get_commits(path = functions_script)
	functions_last_commit = functions_commits[0].commit.committer.date
	
	main_commits = repo.get_commits(path = main_script)
	main_last_commit = main_commits[0].commit.committer.date

	to_dump = [main_last_commit, functions_last_commit, main_last_commit]
	to_update = []
	reset = False
	
	try:
		with open("program_variables", "rb") as pickle_file:
			data = pickle.load(pickle_file)
	except:
		save_to_pickle(to_dump)
	else:
		if data[0] != image_organizer_last_commit:
			to_update.append(image_organizer_script_name)
		if data[1] != functions_last_commit:
			to_update.append(functions_script)
		if data[2] != main_last_commit:
			to_update.append(main_script)
			reset = True
		if to_update:
			save_to_pickle(to_dump)

	missing_icons = functions.check_icons()

	if missing_icons or to_update:
		functions.update_information(missing_icons = missing_icons, to_update = to_update)

	return reset

if __name__ == "__main__":
	main()
