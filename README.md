# Automatic Google Drive Synchronization with Python (auto-sync-drive)

> IN DEVELOPMENT

![Usage](./assets/usage.gif)

This is a python script that automates synchronization between a local folder and a remote folder on Google Drive using Google Drive API's. Inspired by [this video](https://www.youtube.com/watch?v=LSP9PUx7n04).

## Installation

You can use conda to manage the environment:

```bash
conda env create -f environment.yml
```

## Usage

If you installed everything with conda, first activate the environment:

```bash
conda activate auto-sync-drive
```

Then, you will rename **configs-example.json** file to **configs.json** and substitute every value as informed:

```json
{
  "drive_folder_id": "GOOGLE DRIVE BACKUP FOLDER ID (last route param)",
  "local_folder_path": "PATH TO LOCAL BACKUP FOLDER (ex: C:\\Users\\test\\backup)",
  "log_file_path": "PATH TO LOG FILE"
}
```

To run the script (with activated environment), simply:

```bash
python synchronize.py
```

## Automation

In Windows, you can use Task Scheduler to run this script on schedules times, for example every day at noon. To use this, you can use my bash script (or create your own) adding the correct paths into **backup.sh** and creating a task with the following action (paths can change):

```
"C:\Program Files\Git\git-bash.exe" "C:\Users\test\Desktop\auto-sync-drive\backup.sh"
```

## Contact

If you have any suggestions, contact me:

<phnogs@hotmail.com>
