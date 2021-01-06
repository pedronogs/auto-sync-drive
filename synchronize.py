from __future__ import print_function
import pickle
import json
import os
import io
import sys
from utils.Utils import Utils
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import MediaFileUpload, MediaIoBaseDownload

API_URL = ['https://www.googleapis.com/auth/drive']
CONFIGS = None

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
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', API_URL)
                creds = flow.run_local_server(port=0)

            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.__service = build('drive', 'v3', credentials=creds)
    

    # List all files inside specified Drive folder
    def list_files(self, folder_id):
        # Call API
        response = self.__service.files().list(q="'{}' in parents".format(folder_id), fields='files(id,name,modifiedTime,mimeType)').execute()

        # Return all file names
        files_dic = {"all": response.get('files', []), "names": []}
        for item in files_dic['all']:
            files_dic['names'].append(item['name'])
        
        return files_dic
    

    # Download file from drive to local folder
    def download_file(self, filename, local_path, file_id, update=False):
        local_absolute_path = "{}\\{}".format(local_path, filename)

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

        if update != False:
            print("\nLocal file '{}' updated successfully in folder '{}'.".format(filename, local_absolute_path.rsplit('\\', 2)[-2]))
        else:
            print("\nFile '{}' downloaded successfully in folder '{}'.".format(filename, local_absolute_path.rsplit('\\', 2)[-2]))


    # Upload file from local to drive folder
    def upload_file(self, filename, local_path, folder_id, update=False):
        local_absolute_path = "{}\\{}".format(local_path, filename)

        # Custom file metadata for upload (modification time matches local)
        modified_timestamp = Utils.get_local_file_timestamp(local_absolute_path)
        file_metadata = {'name': filename, 'modifiedTime': Utils.convert_timestamp_datetime(modified_timestamp), 'parents': [folder_id]}

        # File definitions for upload
        media = MediaFileUpload(local_absolute_path)

        # Send POST request for upload API
        try:
            if update != False:
                uploaded_file = self.__service.files().update(fileId=update, media_body=media).execute()
                print("\nRemote file '{}' updated successfully in folder '{}'.".format(filename, local_absolute_path.rsplit('\\', 2)[-2]))
            else:
                uploaded_file = self.__service.files().create(body=file_metadata, media_body=media, fields='id').execute()
                print("\nFile '{}' uploaded successfully in folder '{}'.".format(filename, local_absolute_path.rsplit('\\', 2)[-2]))

            return uploaded_file
        except:
            print('\nError uploading file: {}'.format(filename))

            return False


    # Create folder with respective parent Folder ID
    def upload_folder(self, foldername, folder_id):
        # Custom folder metadata for upload
        folder_metadata = {'name': foldername, 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.folder'}

        try:
            # Send POST request for upload API
            uploaded_folder = self.__service.files().create(body=folder_metadata).execute()
            print('\nRemote folder created: {}'.format(uploaded_folder['name']))

            return uploaded_folder['id']
        except:
            print('\nError creating folder...')

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
    def synchronize(self, local_path, folder_id):
        print("------------- Synchronizing folder '{}' -------------".format(local_path.rsplit('\\', 1)[-1]), end="\r")

        # Check if local path exists, if not, creates folder
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        # List remote and local files
        drive_files = self.list_files(folder_id)
        local_files = Utils.list_local_files(local_path)

        # Compare files with same name in both origins and check which is newer, updating
        same_files = list(set(drive_files['names']) & set(local_files))
        for sm_file in same_files:
            local_absolute_path = "{}\\{}".format(local_path, sm_file)

            remote_file_data = next(item for item in drive_files['all'] if item["name"] == sm_file) # Filter to respective file
            remote_file_data["modifiedTime"] = Utils.convert_datetime_timestamp(remote_file_data["modifiedTime"])

            local_file_data = {}
            local_file_data["name"] = sm_file
            local_file_data["modifiedTime"] = Utils.get_local_file_timestamp(local_absolute_path)

            # Checks if files were modified on any origin
            modified = self.compare_files(local_file_data, remote_file_data)

            if modified == 'local':
                if os.path.isdir(local_absolute_path):
                    self.synchronize(local_absolute_path, remote_file_data['id'])
                else:
                    self.upload_file(sm_file, local_path, folder_id, remote_file_data['id'])
    
            elif modified == 'remote':
                if remote_file_data["mimeType"] == 'application/vnd.google-apps.folder':
                    self.synchronize(local_absolute_path, remote_file_data['id'])
                else:
                    self.download_file(sm_file, local_path, remote_file_data['id'], True)

        # Compare different files in both origins and download/upload what is needed
        different_files = list(set(drive_files['names']) ^ set(local_files))
        for diff_file in different_files:
            # IF file is only on Google Drive (DOWNLOAD)
            if diff_file in drive_files['names']:
                for remote_file in drive_files['all']:
                    if remote_file['name'] == diff_file:
                        if remote_file['mimeType'] == 'application/vnd.google-apps.folder':
                            local_absolute_path = "{}\\{}".format(local_path, diff_file)
                            self.synchronize(local_absolute_path, remote_file['id']) # Recursive to download files inside folders
                        else:
                            self.download_file(remote_file['name'], local_path, remote_file['id'])

            # IF file is only on local (UPLOAD)
            else:
                local_absolute_path = "{}\\{}".format(local_path, diff_file)

                # Check if path redirects to a file or folder
                if os.path.isdir(local_absolute_path):
                    created_folder_id = self.upload_folder(diff_file, folder_id)
                    if created_folder_id != False:
                        self.synchronize(local_absolute_path, created_folder_id) # Recursive to upload files inside folders
                else:
                    self.upload_file(diff_file, local_path, folder_id)


def main():
    # Load configs file
    try:
        global CONFIGS
        CONFIGS = json.load(open("configs.json", "r", encoding='utf-8'))
    except:
        print("Please rename example file 'configs-example.json' to 'configs.json' and update all fields.")
        return
    
    # Logs STDOUT to file if exists
    if CONFIGS["log_file_path"] != False:
        sys.stdout = open(CONFIGS["log_file_path"], 'a')
        
        from datetime import datetime
        print("\n******* Log date: {} *******\n".format(datetime.now().strftime("%d/%m/%Y %H:%M:%S")))

    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.synchronize(CONFIGS['local_folder_path'], CONFIGS['drive_folder_id'])


if __name__ == '__main__':
    main()