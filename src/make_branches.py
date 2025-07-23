import os
import subprocess
from config_validation import load_config
import pathlib
import json
import yaml

# Configuration
FOLDERS_TO_SEARCH = os.getcwd()
CONFIG_LOCATION = pathlib.Path(__file__).parent / "../config.yml"
BRANCH_PREFIX = "batch-"

config = load_config(CONFIG_LOCATION)
print(f"Loaded config: {config}")
FILES_PER_BRANCH = config.get("batch-size", 50)


def find_yml_files(folder):
    print(f"Searching for yml files in {folder}")
    yml_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(".yml") and file.startswith("http"):
                yml_files.append(os.path.join(root, file))
    print(f"Found {len(yml_files)} yml files")
    return yml_files


def create_branch(branch_name, files):
    subprocess.run(["git", "checkout", "main"])
    subprocess.run(["git", "restore", "."])
    subprocess.run(["git", "clean", "-fd"])
    subprocess.run(["git", "checkout", "-b", branch_name])

    # find the yml files in the files list
    # open the files and change the translations to be filled in to "to fill in"

    for file in files:
        with open(file, "r") as f:
            yml = yaml.safe_load(f)
        for label in yml["labels"]:
            for translation in label["translations"]:
                # for each key change the value to "to be filled in"
                for key in translation:
                    translation[key] = "to be filled in"
        with open(file, "w") as f:
            yaml.dump(yml, f)
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", f"made branch with yml files"])
    subprocess.run(["git", "push", "origin", branch_name])


def main():
    yml_files = find_yml_files(FOLDERS_TO_SEARCH)
    # checkout main branch
    subprocess.run(["git", "checkout", "main"])

    with open("objects.json", "r") as f:
        objects = json.load(f)
    for i in range(0, len(yml_files), FILES_PER_BRANCH):
        branch_name = f"{BRANCH_PREFIX}{i // FILES_PER_BRANCH + 1}"
        # open the objects.json file and find the object whose file_name is in the yml_files[i : i + FILES_PER_BRANCH]
        # change the  "branch": "main", to "branch": branch_name
        for obj in objects:
            if any(
                obj["file_name"] in yml_file
                for yml_file in yml_files[i : i + FILES_PER_BRANCH]
            ):
                obj["branch"] = branch_name
    with open("objects.json", "w") as f:
        json.dump(objects, f, indent=4)

    subprocess.run(["git", "add", "objects.json"])
    subprocess.run(["git", "commit", "-m", "updated objects.json"])
    subprocess.run(["git", "push", "origin", "main"])

    for i in range(0, len(yml_files), FILES_PER_BRANCH):
        branch_name = f"{BRANCH_PREFIX}{i // FILES_PER_BRANCH + 1}"
        create_branch(branch_name, yml_files[i : i + FILES_PER_BRANCH])


if __name__ == "__main__":
    main()
