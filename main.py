import pickle, functions
from github import Github

###Pickle structure###
#[main_last_commit, functions_last_commit]

def save_to_pickle(to_dump):
	with open("program_variables", "wb") as pickle_file:
		pickle.dump(to_dump, pickle_file)
		
main_script_name = functions.retrieve_variables(3)
functions_script = functions.retrieve_variables(4)

g = Github()
repo = g.get_repo("Camilo685/Image_tagger")
main_commits = repo.get_commits(path = main_script_name)
main_last_commit = main_commits[0].commit.committer.date

functions_commits = repo.get_commits(path = functions_script)
functions_last_commit = functions_commits[0].commit.committer.date

to_dump = [main_last_commit, functions_last_commit]

try:
	with open("program_variables", "rb") as pickle_file:
		data = pickle.load(pickle_file)
except:
	save_to_pickle(to_dump)
else:
	to_update = []
	save = False
	if data[0] != main_last_commit:
		update_main.append(main_script_name)
		save = True
	if data[1] != functions_last_commit:
		update_main.append(functions_script)
		save = True
	if save:
		save_to_pickle(to_dump)

missing_icons = functions.check_icons()

if missing_icons or to_update:
	functions.update_information(missing_icons = missing_icons, to_update = to_update)

if __name__ == "__main__":
	with open("Image_organizer.py") as main_script:
		exec(main_script.read())
