import os
import yaml
import json
import shutil
from pathlib import Path
import subprocess

# the purpose of this script is to simulate the behavior of the sync action in the github workflow
# a sync action can have multiple steps and outcomes
# first a dictionary must be made for all the yml files that are in the repo.
# after this is done there will be multiple checks to see if there are new yml files, or changes in existing yml files
# if there are new yml files there will be a nesws entry in teh objects.json file
# if there is a change in an existing yml file than this one must be updated in the objects.json file and overwritten in the child yml file
# if there is a change and the object.json file indicates for the file that this was merged this entry must be changed to bacth-x +1

subprocess.run(["git", "checkout", "main"])

# first step is to get al yml files in the repo starting from the parent folder from where this file is located
# this is done by using the pathlib library
parent_folder = Path(__file__).resolve().parent.parent
all_yml_files = []
for file in parent_folder.rglob("*.yml"):
    # Convert the path to string and perform the replacements outside the f-string
    file_str = str(file)
    if "http__" in file_str:
        print(file_str)
        all_yml_files.append(file_str)

# now that we have a list of yml files make a dictionary where the key is the name of the file , so the name of the file without the path
# then have 2 values as keys , vbeing child and parent , the parent is the path without the github/workspace folder part.
# the child is the path with the github/workspace folder part
# it can be that the child or the parent is empty, this is not a problem
yml_dict = {}
for file in all_yml_files:
    file_name = os.path.basename(file)

    # check if file_name is already in the dictionary
    if file_name not in yml_dict:
        yml_dict[file_name] = {"parent": "", "child": ""}
    # Use pathlib to find all paths matching the file_name
    for path in parent_folder.rglob(file_name):
        path_str = str(path)
        print(path_str)

        # Determine if it's parent or child based on path length
        if yml_dict[file_name]["parent"] == "":
            yml_dict[file_name]["parent"] = path_str
        elif len(path_str) < len(yml_dict[file_name]["parent"]):
            yml_dict[file_name]["child"] = yml_dict[file_name]["parent"]
            yml_dict[file_name]["parent"] = path_str
        else:
            yml_dict[file_name]["parent"] = path_str


# json print the yml dict
print(json.dumps(yml_dict, indent=4))

objects_file = os.path.join(parent_folder, "github", "workspace", "objects.json")

# Extract the latest branch from objects.json
if os.path.exists(objects_file):
    with open(objects_file, "r") as f:
        objects = json.load(f)
        latest_branch = max(
            (int(obj["branch"].split("-")[1]) for obj in objects if "branch" in obj),
            default=0,
        )
        print(f"Latest branch: batch-{latest_branch}")
else:
    objects = {}

file_names = []
for object in objects:
    file_names.append(object["file_name"])
# now check if there are new yml files or changes in existing yml files
# while the yml files are being checked , also keep track of the objects.json file
# also a new variable is created called new_branch to keep track of all the changes that will be applied in a new branch
new_branch = []
new_branch_name = f"batch-{latest_branch + 1}"

for file in yml_dict:
    if file not in file_names:
        print(f"New file found: {file}")
        # put it in the new_branch list
        new_branch.append(file)
        # copy file from parent location to ../github/workspace/ that is relative to this script
        parent_path = yml_dict[file]["parent"]
        print(parent_path)
        # get name of the parent folder of the file, only get the name of the folder not the whole path
        parent_folder_file = os.path.dirname(parent_path)
        split_path = parent_folder_file.split(os.sep)
        # get the last folder name
        parent_folder_file = split_path[-1]
        # the lcoation to copy over to is the ../github/workspace/ + the name of the file with the fodler before that so /folder/file.yml
        to_copy_to = os.path.join(
            parent_folder, "github", "workspace", parent_folder_file, file
        )
        print(to_copy_to)
        shutil.copyfile(parent_path, to_copy_to)
        # make new entry in the objects.json file
        new_entry = {
            "file_name": file,
            "status": "recieved",
            "branch": new_branch_name,
        }
        # add the new entry to the objects list
        objects.append(new_entry)

    if file in file_names:
        print(f"File found: {file}")
        # open both the parent and the child file and load in yaml
        parent_path = yml_dict[file]["parent"]
        child_path = yml_dict[file]["child"]
        with open(parent_path, "r") as f:
            parent_yaml = yaml.safe_load(f)
        with open(child_path, "r") as f:
            child_yaml = yaml.safe_load(f)

        # Compare the 'original' values within the 'labels'
        differences_found = False
        if "labels" in parent_yaml and "labels" in child_yaml:
            for parent_label, child_label in zip(
                parent_yaml["labels"], child_yaml["labels"]
            ):
                if "original" in parent_label and "original" in child_label:
                    if parent_label["original"] != child_label["original"]:
                        print(
                            f"Difference found in 'original' for label '{parent_label.get('name', 'unknown')}' in file: {file}"
                        )
                        print(f"  Parent: {parent_label['original']}")
                        print(f"  Child: {child_label['original']}")
                        differences_found = True
        if differences_found:
            # Update the child file with the parent values
            with open(child_path, "w") as f:
                yaml.dump(parent_yaml, f)

            # Update the objects.json file if the status is "merged"
            for obj in objects:
                if obj["file_name"] == file:
                    if obj["status"] == "merged":
                        obj["branch"] = new_branch_name
                    # Update the status to "received" if it was previously "merged"
                    obj["status"] = "received"
                    break
# save the new objects.json file
with open(objects_file, "w") as f:
    json.dump(objects, f, indent=4)

# now that the objects.json file is updated, we need to create a new branch and commit the changes
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"sync action for main branch"])
subprocess.run(["git", "push", "origin", "main"])
subprocess.run(["git", "checkout", "-b", new_branch_name])
subprocess.run(["git", "add", "."])
subprocess.run(["git", "commit", "-m", f"sync action for {new_branch_name} branch"])
subprocess.run(["git", "push", "origin", new_branch_name])
