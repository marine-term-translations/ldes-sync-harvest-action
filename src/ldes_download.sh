#!/bin/bash

python config_validation.py
if [ $? -ne 0 ]; then
    echo "Config file is not valid. Please check the config file and try again."
    exit 1
fi

config=$(python -c "import json, yaml; print(json.dumps(yaml.safe_load(open('../../config.yml'))))")
echo $config

# Use Python to output each source as a separate line
python -c "import json; [print(json.dumps(source)) for source in json.loads('$config')['sources']]" | while read source; do
    echo $source
    # Use Python to extract the name and url from the source
    source_name=$(python -c "import json; print(json.loads('''$source''')['name'])")
    source_url=$(python -c "import json; print(json.loads('''$source''')['url'])")

    echo "Harvesting $source_name from $source_url"
    # check if there is a folder at location ../$source_name, if not create it
    if [ ! -d "../../$source_name" ]; then
        mkdir "../../$source_name"
    fi

    # CLI command to harvest data from a LDES
    actor-init-ldes-client --pollingInterval 5000 --mimeType text/turtle --emitMemberOnce true --disablePolling true --requestsPerMinute 40 "$source_url" > "../../$source_name/output_ldes_stream.ttl"
 
done