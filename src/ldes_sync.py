# python : checks the ttl ldes file and then all the subsequent yml files to check if any changes have been made

import os
import pathlib
from config_validation import load_config
from pyrdfj2 import J2RDFSyntaxBuilder
import rdflib
import re
import json
import yaml

CONFIG_LOCATION = pathlib.Path(__file__).parent / "../config.yml"
QUERYBUILDER = J2RDFSyntaxBuilder(
    templates_folder=pathlib.Path(__file__).parent / "templates"
)

config = load_config(CONFIG_LOCATION)

languages_to_fill = config["target_languages"]


def new_combined_yml_file(old_yml, new_yml):
    # check if any of the dict_key_values have changed
    # print(old_yml)
    # print(new_yml)

    combined_labels = []

    for label in new_yml["labels"]:
        c_label = {}
        # print(label)
        for labelo in old_yml["labels"]:
            if label["name"] == labelo["name"]:
                if label["original"] != labelo["original"]:
                    print(f"Label {label['name']} has changed")
                    c_label = label
                else:
                    c_label = labelo
        combined_labels.append(c_label)

    new_yml["labels"] = combined_labels
    return new_yml


for source in config["sources"]:
    source_name = source["name"]
    print(f"Checking {source_name}...")

    # check if folder exists
    path_to_check = pathlib.Path(__file__).parent / f"../{source_name}"
    if not os.path.exists(path_to_check):
        print(f"Folder {source_name} does not exist")
        continue

    # load in the ttl ldes file with rdflib
    source_path_ttl = path_to_check / "output_ldes_stream.ttl"
    assert os.path.exists(source_path_ttl), f"{source_path_ttl} does not exist"
    with open(source_path_ttl, "r") as f:
        data = f.read()
        data = re.sub(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d)", r"\1T\2", data)
    with open(source_path_ttl, "w") as f:
        f.write(data)
    # load in the ttl file with rdflib
    g = rdflib.Graph()
    g.parse(source_path_ttl, format="ttl")

    # loop over each .yml file in the folder and load in the yml file
    for file in os.listdir(path_to_check):
        if file.endswith(".yml"):
            file_path = path_to_check / file
            try:
                with open(file_path, "r") as f:
                    yml_data = yaml.safe_load(f)
                    # print(yml_data["uri"])

                # get the info from the graph for the uri
                sparql_query = QUERYBUILDER.build_syntax(
                    "query.sparql",
                    language=source["language"],
                    id_path=source["id-path"],
                    dict_key_values=source["items"],
                )
                qres = g.query(sparql_query)
                json_res = qres.serialize(format="json")
                json_res = json.loads(json_res)
                # print(json_res["results"]["bindings"])
                # search for the uri in the json_res
                for row in json_res["results"]["bindings"]:
                    if row["identifier"]["value"] == yml_data["uri"]:
                        yml_text = QUERYBUILDER.build_syntax(
                            "single_yml.yml",
                            row=row,
                            languages=languages_to_fill,
                            source_items=source["items"],
                        )
                        # safe laod the yml text
                        yml_new_data = yaml.safe_load(yml_text)

                        # check if the data is the same
                        if yml_data != yml_new_data:
                            print(f"Data in {file} has changed")
                            new_file = new_combined_yml_file(yml_data, yml_new_data)

                            # write the new file
                            with open(file_path, "w") as f:
                                f.write(yaml.dump(new_file, allow_unicode=True))
                        break

            except Exception as e:
                print(f"Error loading {file}: {e}")

    # do the opposite, check if there are any new content in the ttl file that is not in the yml files
    sparql_query = QUERYBUILDER.build_syntax(
        "query.sparql",
        language=source["language"],
        id_path=source["id-path"],
        dict_key_values=source["items"],
    )
    qres = g.query(sparql_query)
    json_res = qres.serialize(format="json")
    json_res = json.loads(json_res)
    for row in json_res["results"]["bindings"]:
        uri = row["identifier"]["value"]
        found = False
        for file in os.listdir(path_to_check):
            if file.endswith(".yml"):
                file_path = path_to_check / file
                with open(file_path, "r") as f:
                    yml_data = yaml.safe_load(f)
                    if yml_data["uri"] == uri:
                        found = True
                        break
        if not found:
            print(f"New data found in {source_name} for {uri}")
            # make a new yml file
            yml_text = QUERYBUILDER.build_syntax(
                "single_yml.yml",
                row=row,
                languages=languages_to_fill,
                source_items=source["items"],
            )
            identifier_raw = row["id_node"]["value"]
            identifier = re.sub(r"[^a-zA-Z0-9]", "_", identifier_raw)
            with open(
                pathlib.Path(__file__).parent / f"../{source_name}/{identifier}.yml",
                "w",
            ) as f:
                f.write(yml_text)
