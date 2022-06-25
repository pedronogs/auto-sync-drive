# Automatic Google Drive Synchronization with Python (auto-sync-drive)

This is a python script that automates synchronization between a local folder and a remote folder on Google Drive using Google Drive API's. Inspired by [this video](https://www.youtube.com/watch?v=LSP9PUx7n04).

The inspiration to make this code is to help beginners on Python programming to make practical and useful code. This script can be run either on Windows or Linux, possibly with minor adjustments.

![Usage](./assets/usage.gif)

## Installation

You can use any virtual environment manager to run this code (Python >3.8), but for beginners I will add a simple example using `pyenv`. You can use `pyenv` to manage python versions and `python -m venv` to manage the environments:

```bash
# Highly recommend using git-bash for this
git clone https://github.com/pedronogs/auto-sync-drive

cd auto-sync-drive

# Install PyEnv by yourself and then...
pyenv install 3.8.3 # Install python 3.8.3 or any version you find suitable, >3.8
pyenv global 3.8.3 # Set python version globally, or as you wish

python -m venv auto-sync-drive # Create virtual environment
source auto-sync-drive/Scripts/activate # Activate virtual environment, path depends on OS

pip install -r requirements.txt # Install packages
```

## Usage

Then, you will rename **configs-example.json** file to **configs.json** and replace every value as needed:

```json
{
	"drive_folder_id": "GOOGLE DRIVE BACKUP FOLDER ID (last route param)",
	"local_folder_path": "PATH TO LOCAL BACKUP FOLDER (ex: c:/Users/user/Desktop/backup for Windows, or /home/user/Desktop/backup for Linux)",
	"log_to_file": true
}
```

To run the script (with activated environment), simply:

```bash
python synchronize.py
```

## Automation

In Linux you can add a `cronjob` to run scripts automatically, but for Windows it is a little bit different, so I will help. In Windows, you can use the native tool `Task Scheduler` to run this script on scheduled times, for example every day at noon. To use this, you can use my bash script (or create your own) adding the correct paths into **backup.sh** and creating a task with the following action (paths can change):

```
"C:\Program Files\Git\git-bash.exe" "C:\Users\user\Desktop\auto-sync-drive\backup.sh"
```

## Contact

If you have any suggestions, create an issue or contact me:

<phnogs@hotmail.com>
