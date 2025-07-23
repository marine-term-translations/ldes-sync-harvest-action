#! /bin/sh
pwd

ls -al

echo "repo name is:" $GITHUB_REPOSITORY
cd ../..
pwd
ls -al
# copy over ./github/workspace/* /*
rsync --recursive --progress -avzh ./github/workspace/* ./

cd src
ls -al

npm install -g @treecg/actor-init-ldes-client
npm install -g yaml 
npm list --depth=0

cd ..
cd ./github/workspace
git config --global --add safe.directory /github/workspace
# set user name and email 
git config --global user.name 'GitHub Actions'
git config --global user.email 'actions@github.com'

cd ../..
cd src

# executing the setup.sh script
bash setup.sh





# copy over everything in ./ back to ./github/workspace
# overwrite everything in ./github/workspace
# do not copy over the .git folder and the .github folder 
# also do not copy over the following files:
# - entrypoint.sh
# - Dockerfile
# - README.md
# - LICENSE
# - .gitignore
# - .dockerignore
# - .env
# package.json
# poetry.lock
# pyproject.toml
# requirements.txt
# everything in src folder and recursively under src folder
# package-lock.json
# actions.yml