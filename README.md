# Automatic Google Drive Synchronization (auto-sync-drive)

> IN DEVELOPMENT

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
  "local_folder_path": "PATH TO LOCAL BACKUP FOLDER (ex: C:\\Users\\test\\backup)"
}
```

To run the script (with activated environment), simply:

```bash
python synchronize.py
```

## Contact

If you have any suggestions, contact me:

<phnogs@hotmail.com>
