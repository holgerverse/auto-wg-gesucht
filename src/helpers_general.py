from json import dumps, load
from os.path import join


def save_file_to_json(object_to_save, file_name, folder):
	updated_hash_json = dumps(object_to_save, indent=4)
	with open(join(folder, file_name + ".json"), "w") as outfile:
		outfile.write(updated_hash_json)


def try_read_json_file(file_name, folder, substitute):
	try:
		with open(join(folder, file_name + '.json'), 'r') as openfile:
			json_content = load(openfile)
		return json_content
	except FileNotFoundError:
		print("No file called " + file_name + ".json")
		return substitute
