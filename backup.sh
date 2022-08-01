#!/bin/bash

current_user=`id -u -n`
base_folder="/c/Users/${current_user}/Desktop/github/auto-sync-drive"

# Activate virtual environment
source "${base_folder}/auto-sync-drive/Scripts/activate"

# Redirect to repository folder
cd $base_folder

# Run script
python synchronize.py