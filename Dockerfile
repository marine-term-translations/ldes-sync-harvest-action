# use a python image
FROM python:3.11

# install node and npm
RUN apt-get update
RUN apt-get install -y nodejs npm

# install rsync
RUN apt-get install -y rsync

# copy over src folder
COPY src /src
COPY package.json /package.json
COPY package-lock.json /package-lock.json
COPY poetry.lock /poetry.lock
COPY pyproject.toml /pyproject.toml

# install dependencies
RUN npm install
RUN pip install poetry
RUN pip install pyyaml pycountry validators pyrdfj2 rdflib
RUN poetry install --no-root

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT [ "/entrypoint.sh" ]