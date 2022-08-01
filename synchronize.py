# This code was adapted from https://github.com/ClarityCoders/GoogleDrive
# His youtube video for reference https://www.youtube.com/watch?v=LSP9PUx7n04

# This adaptation includes:
# - Synchronization:
#   - Downloads and uploads files when needed to make local and remote origins identical
#   - Checks for file modification and updates origin with the oldest file
# - Clean logging to stdout and to file (if specified in configuration)

import pickle
import json
import os
import io

from loguru import logger
from utils.utils import Utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

API_URL = ['https://www.googleapis.com/auth/drive']


class Drive():

    def __init__(self):
        creds = None

        # Checks if authentication token exists, then load it
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # Create new authencation token if it does not exist or has expired
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', API_URL)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.__service = build('drive', 'v3', credentials=creds)

    # List all files inside specified Drive folder
    def list_files(self, folder_id):
        # Call API
        response = self.__service.files().list(
            q=f"'{folder_id}' in parents", fields='files(id,name,modifiedTime,mimeType)'
        ).execute()

        # Return all file names
        files_dict = {"all": response.get('files', []), "names": []}
        for item in files_dict['all']:
            files_dict['names'].append(item['name'])

        return files_dict

    # Download file from drive to local folder
    def download_file(self, filename, local_path, file_id, update=False):
        local_absolute_path = f"{local_path}/{filename}"

        # Request for download API
        request = self.__service.files().get_media(fileId=file_id)

        # File stream
        fh = io.BytesIO()

        # Setup request and file stream
        downloader = MediaIoBaseDownload(fh, request)

        # Wait while file is being downloaded
        done = False
        while done is False:
            done = downloader.next_chunk()

        # Save download buffer to file
        with open(local_absolute_path, 'wb') as out:
            out.write(fh.getbuffer())

        # Change local modification time to match remote
        modified_time = self.__service.files().get(fileId=file_id, fields='modifiedTime').execute()['modifiedTime']
        modified_timestamp = Utils.convert_datetime_timestamp(modified_time)
        os.utime(local_absolute_path, (modified_timestamp, modified_timestamp))

        if update is not False:
            logger.info("Local file '{}' updated successfully in folder '{}'.", filename, local_absolute_path)
        else:
            logger.info("File '{}' downloaded successfully in folder '{}'.", filename, local_absolute_path)

    # Upload file from local to drive folder
    def upload_file(self, filename, local_path, folder_id, update=False):
        local_absolute_path = f"{local_path}/{filename}"

        # Custom file metadata for upload (modification time matches local)
        modified_timestamp = Utils.get_local_file_timestamp(local_absolute_path)
        file_metadata = {
            'name': filename,
            'modifiedTime': Utils.convert_timestamp_datetime(modified_timestamp),
            'parents': [folder_id]
        }

        # File definitions for upload
        media = MediaFileUpload(local_absolute_path)

        # Send POST request for upload API
        try:
            if update != False:
                uploaded_file = self.__service.files().update(fileId=update, media_body=media).execute()

                logger.info("Remote file '{}' updated successfully in folder '{}'.", filename, local_absolute_path)

            else:
                uploaded_file = self.__service.files().create(
                    body=file_metadata, media_body=media, fields='id'
                ).execute()

                logger.info("File '{}' uploaded successfully in folder '{}'.", filename, local_absolute_path)

            return uploaded_file
        except:
            logger.error("Error uploading file: {}.", filename)

            return False

    # Create folder with respective parent Folder ID
    def upload_folder(self, foldername, folder_id):
        # Custom folder metadata for upload
        folder_metadata = {'name': foldername, 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.folder'}

        try:
            # Send POST request for upload API
            uploaded_folder = self.__service.files().create(body=folder_metadata).execute()
            logger.info("Remote folder created: '{}'.", uploaded_folder['name'])

            return uploaded_folder['id']
        except:
            logger.error("Error creating folder: '{}'.", folder_metadata["name"])

            return False

    # Verifies if file was modified or not
    def compare_files(self, local_file_data, remote_file_data):
        modified = False

        if local_file_data['modifiedTime'] > remote_file_data['modifiedTime']:
            modified = 'local'
        elif local_file_data['modifiedTime'] < remote_file_data['modifiedTime']:
            modified = 'remote'

        return modified

    # Recursive method to synchronize all folder and files
    def synchronize(self, local_path, folder_id, recursive=False):
        logger.info("{} folder '{}'", "Recursively synchronizing" if recursive else "Synchronizing", local_path)

        # Check if local path exists, if not, creates folder
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        # List remote and local files
        drive_files = self.list_files(folder_id)
        local_files = Utils.list_local_files(local_path)

        # Compare files with same name in both origins and check which is newer, updating
        same_files = list(set(drive_files['names']) & set(local_files))

        if len(same_files) == 0 and not recursive:
            logger.info("No files to update on folder '{}'.", local_path)

        for sm_file in same_files:
            local_absolute_path = f"{local_path}/{sm_file}"

            remote_file_data = next(
                item for item in drive_files['all'] if item["name"] == sm_file
            )  # Filter to respective file
            remote_file_data["modifiedTime"] = Utils.convert_datetime_timestamp(remote_file_data["modifiedTime"])

            local_file_data = {}
            local_file_data["name"] = sm_file
            local_file_data["modifiedTime"] = Utils.get_local_file_timestamp(local_absolute_path)

            # Checks if files were modified on any origin
            modified = self.compare_files(local_file_data, remote_file_data)

            if modified == 'local':
                if os.path.isdir(local_absolute_path):
                    self.synchronize(local_absolute_path, remote_file_data['id'], recursive=True)
                else:
                    self.upload_file(sm_file, local_path, folder_id, remote_file_data['id'])

            elif modified == 'remote':
                if remote_file_data["mimeType"] == 'application/vnd.google-apps.folder':
                    self.synchronize(local_absolute_path, remote_file_data['id'], recursive=True)
                else:
                    self.download_file(sm_file, local_path, remote_file_data['id'], True)

        # Compare different files in both origins and download/upload what is needed
        different_files = list(set(drive_files['names']) ^ set(local_files))

        if len(different_files) == 0 and not recursive:
            logger.info("No files to download/upload on folder '{}'.", local_path)

        for diff_file in different_files:
            # If file is only on Google Drive (DOWNLOAD)
            if diff_file in drive_files['names']:
                for remote_file in drive_files['all']:
                    if remote_file['name'] == diff_file:
                        if remote_file['mimeType'] == 'application/vnd.google-apps.folder':
                            local_absolute_path = f"{local_path}/{diff_file}"
                            self.synchronize(
                                local_absolute_path, remote_file['id'], recursive=True
                            )  # Recursive to download files inside folders
                        else:
                            self.download_file(remote_file['name'], local_path, remote_file['id'])

            # IF file is only on local (UPLOAD)
            else:
                local_absolute_path = f"{local_path}/{diff_file}"

                # Check if path redirects to a file or folder
                if os.path.isdir(local_absolute_path):
                    created_folder_id = self.upload_folder(diff_file, folder_id)
                    if created_folder_id != False:
                        self.synchronize(
                            local_absolute_path, created_folder_id, recursive=True
                        )  # Recursive to upload files inside folders
                else:
                    self.upload_file(diff_file, local_path, folder_id)


def main():
    # Make sure configuration file exists and is updated
    if not os.path.exists("./configs.json"):
        logger.error(
            "Please rename example file 'configs-example.json' to 'configs.json' and update all required fields."
        )
        return

    configs = json.load(open("configs.json", "r", encoding='utf-8'))

    # Make sure backup folder exists
    if not os.path.exists(configs["local_folder_abs_path"]):
        logger.error("Create backup folder on '{}'.", configs["local_folder_abs_path"])
        return

    # Configure logging to file if enabled
    if configs["log_to_file"]:
        log_path = os.path.join(configs["local_folder_abs_path"], "sync.log")
        if not os.path.exists(log_path):
            log_obj = open(log_path, "w")
        else:
            log_obj = open(log_path, "a")

        logger.add(log_obj, format="{time} | {level} | {function} | {message}")

    logger.success("Starting synchronization...")

    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.synchronize(configs['local_folder_abs_path'], configs['drive_folder_id'])

    logger.success("Synchronization finalized!")


if __name__ == '__main__':
    main()