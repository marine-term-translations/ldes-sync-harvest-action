import pathlib
import yaml
import pycountry
import validators


def load_config(config_path: pathlib.Path) -> dict:
    with open(config_path, "r") as config_file:
        config = yaml.safe_load(config_file)
    # Validate config here
    return config


"""
the config must validate to this object

batch-size: int
target_languages: list of str -> en, fr , es, etc
    - en
    - fr
sources:
- name: str
    url: http://vocab.nerc.ac.uk/ldes/P02/ -> url to the source
    language: str -> en, fr , es, etc
    id-path: http://purl.org/dc/terms/identifier -> path to the id must be uri
    items: -> list of items to be extracted
    - name: definition
        path: http://www.w3.org/2004/02/skos/core#definition -> path to the definition must be uri
    - name: altLabel
        path: http://www.w3.org/2004/02/skos/core#altLabel -> path to the altLabel must be uri

"""

CONFIG_LOCATION = pathlib.Path(__file__).parent.parent / "../config.yml"


def validate_config(config_path: pathlib.Path) -> bool:
    # try and load the config
    try:
        config = load_config(config_path)

        # do checks here
        if not isinstance(config["batch-size"], int):
            raise ValueError(
                f"Invalid value for 'batch-size': {config['batch-size']}. Expected an integer."
            )
        if not isinstance(config["target_languages"], list):
            raise ValueError(
                f"Invalid value for 'target_languages': {config['target_languages']}. Expected a list."
            )
        for language in config["target_languages"]:
            if not pycountry.languages.get(alpha_2=language):
                raise ValueError(
                    f"Invalid value for 'target_language' in language: {language}. Expected a valid language code."
                )
        for source in config["sources"]:
            if not isinstance(source["name"], str):
                raise ValueError(
                    f"Invalid value for 'name' in source: {source['name']}. Expected a string."
                )
            if not isinstance(source["url"], str) or not validators.url(source["url"]):
                raise ValueError(
                    f"Invalid value for 'url' in source: {source['url']}. Expected a valid URL."
                )
            if not pycountry.languages.get(alpha_2=source["language"]):
                raise ValueError(
                    f"Invalid value for 'language' in source: {source['language']}. Expected a valid language code."
                )
            if not isinstance(source["id-path"], str) or not validators.url(
                source["id-path"]
            ):
                raise ValueError(
                    f"Invalid value for 'id-path' in source: {source['id-path']}. Expected a valid URL."
                )
            if not isinstance(source["items"], list):
                raise ValueError(
                    f"Invalid value for 'items' in source: {source['items']}. Expected a list."
                )
            for item in source["items"]:
                if not isinstance(item["name"], str):
                    raise ValueError(
                        f"Invalid value for 'name' in item: {item['name']}. Expected a string."
                    )
                if not isinstance(item["path"], str) or not validators.url(
                    item["path"]
                ):
                    raise ValueError(
                        f"Invalid value for 'path' in item: {item['path']}. Expected a valid URL."
                    )
        return True
    except Exception as e:
        print(f"Error loading config: {e}")
        # print more info here
        print(Exception(e))
        return False


if __name__ == "__main__":
    if validate_config(CONFIG_LOCATION):
        print("Config is valid")
    else:
        print("Config is invalid")
        exit(1)
