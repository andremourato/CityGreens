# CityGreens

## Setup
### Install python and pip (requires python >=3.4)
sudo apt-get update
sudo apt-get install python3 python3-pip

### Install pipenv
pip3 install --user pipenv

### Install project python modules
pipenv install

## Useful commands
### Running python environment from commandline
pipenv shell

### Running python module from pipenv
pipenv run module.py

### Installing dependencies
pipenv install newdependency 
>like pip install --user newdependency

### Removing dependencies
pipenv uninstall newdependency

### Sync packages
pipenv sync
