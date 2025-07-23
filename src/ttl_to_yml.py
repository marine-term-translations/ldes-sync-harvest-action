# this file will convert a given ttl file with the config.yml file to a series of small editable yml files

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

for source in config["sources"]:
    source_name = source["name"]
    source_path_ttl = (
        pathlib.Path(__file__).parent / f"../{source_name}" / "output_ldes_stream.ttl"
    )

    # Preprocess the ttl file to replace spaces with 'T' in datetime strings -> required for rdflib otherwise it throws an error
    with open(source_path_ttl, "r") as f:
        data = f.read()
    data = re.sub(r"(\d{4}-\d{2}-\d{2}) (\d{2}:\d{2}:\d{2}\.\d)", r"\1T\2", data)
    with open(source_path_ttl, "w") as f:
        f.write(data)

    # load in the ttl file with rdflib
    g = rdflib.Graph()
    g.parse(source_path_ttl, format="ttl")

    # get all the variables needed to form the quert from the config file
    source_id_path = source["id-path"]
    source_language = source["language"]
    source_items = source["items"]

    # create the sparql query
    sparql_query = QUERYBUILDER.build_syntax(
        "query.sparql",
        language=source_language,
        id_path=source_id_path,
        dict_key_values=source_items,
    )

    print(sparql_query)

    # perform the query
    qres = g.query(sparql_query)

    # convert the qres to a json object
    json_res = qres.serialize(format="json")
    # load the json object into a python object
    json_res = json.loads(json_res)
    objects_file = []
    for row in json_res["results"]["bindings"]:

        # print(row)
        # print(languages_to_fill)
        # print(source_language)
        # print(source_items)

        yml_text = QUERYBUILDER.build_syntax(
            "single_yml.yml",
            row=row,
            languages=languages_to_fill,
            source_items=source_items,
        )

        identifier_raw = row["id_node"]["value"]

        # process id so that it is a valid file name
        identifier = re.sub(r"[^a-zA-Z0-9]", "_", identifier_raw)

        file_info = {
            "file_name": f"{identifier}.yml",
            "status": "recieved",
            "branch": "main",
        }
        objects_file.append(file_info)

        # print(yml_text)
        # write the ouput to a file
        # location file is ../{source_name}/row["identifier"]["value"].yml

        with open(
            pathlib.Path(__file__).parent / f"../{source_name}/{identifier}.yml",
            "w",
            encoding="utf-8",
        ) as f:
            f.write(yml_text)

    # write the objects_file to a file
    # check if objects.json exists
    if os.path.isfile(pathlib.Path(__file__).parent / f"../objects.json"):
        with open(
            pathlib.Path(__file__).parent / f"../objects.json",
            "r",
            encoding="utf-8",
        ) as f:
            objects = json.load(f)
            # check what files are already in the objects.json file and only add the new ones
            existing_files = {obj["file_name"] for obj in objects}
            for file in objects_file:
                if file["file_name"] not in existing_files:
                    objects.append(file)
        with open(
            pathlib.Path(__file__).parent / f"../objects.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(objects, f, indent=4)
    else:
        # make a new objects.json file and dump the objects_file in it
        with open(
            pathlib.Path(__file__).parent / f"../objects.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(objects_file, f, indent=4)

# in the end go over all yml files created , and parse and write them again
# to make sure they are correctly formatted
for source in config["sources"]:
    source_name = source["name"]
    for file in os.listdir(pathlib.Path(__file__).parent / f"../{source_name}"):
        if file.endswith(".yml"):
            file_path = pathlib.Path(__file__).parent / f"../{source_name}" / file
            with open(file_path, "r") as f:
                yml_data = yaml.safe_load(f)
            with open(file_path, "w") as f:
                yaml.dump(yml_data, f, allow_unicode=True)
