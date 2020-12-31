from __future__ import print_function
import pickle
import json
import os
import io
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
        response = self.__service.files().list(q="'{}' in parents".format(folder_id)).execute()

        # Return all file names
        files_dic = {"all": response.get('files', []), "names": []}
        for item in files_dic['all']:
            files_dic['names'].append(item['name'])
        
        return files_dic
    

    # Download file from drive to local folder
    def download_file(self, file_id, filename):
        # Request for download API
        request = self.__service.files().get_media(fileId=file_id)
        
        # File stream
        fh = io.BytesIO()

        # Setup request and file stream
        downloader = MediaIoBaseDownload(fh, request)
        
        # Wait while file is being downloaded
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print("Download %d%%." % int(status.progress() * 100))

        # Save download buffer to file
        with open("{}/{}".format(CONFIGS['local_folder_path'], filename), 'wb') as out: 
            out.write(fh.getbuffer())

        print("File downloaded successfully: {}".format(filename))


    # Upload file from local to drive folder
    def upload_file(self, filename, local_path, folder_id):
        # Custom file metadata for upload
        file_metadata = {'name': filename, 'parents': [folder_id]}

        # File definitions for upload
        media = MediaFileUpload('{}\\{}'.format(local_path, filename))

        # Send POST request for upload API
        try:
            uploaded_file = self.__service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print('File uploaded successfully: {}'.format(filename))

            return uploaded_file
        except:
            return False


    # Upload file from local to drive folder
    def upload_folder(self, foldername, folder_id):
        # Custom folder metadata for upload
        folder_metadata = {'name': foldername, 'parents': [folder_id], 'mimeType': 'application/vnd.google-apps.folder'}

        try:
            # Send POST request for upload API
            uploaded_folder = self.__service.files().create(body=folder_metadata).execute()
            print('Folder created with ID: {}'.format(uploaded_folder['id']))

            return uploaded_folder['id']
        except:
            return False


    # Recursive method to synchronize all folder and files
    def synchronize(self, local_path, folder_id):
        # List remote and local files
        drive_files = self.list_files(folder_id)
        local_files = list_local_files(local_path)

        # Find all different files between drive and local folders
        different_files = list(set(drive_files['names']) ^ set(local_files))

        # Compare files in both origins and download/upload what is needed
        for diff_file in different_files:
            # IF file is only on Google Drive
            if diff_file in drive_files['names']:
                for f in drive_files['all']:
                    if f['name'] == diff_file:
                        self.download_file(f['id'], f['name'])

            # IF file is only on local
            else:
                local_absolute_path = "{}\\{}".format(local_path, diff_file)

                # Check if path redirects to a file or folder (and then upload)
                if os.path.isdir(local_absolute_path):
                    created_folder_id = self.upload_folder(diff_file, folder_id)
                    if created_folder_id != False:
                        self.synchronize(local_absolute_path, created_folder_id) # Recursive to upload files inside folders
                else:
                    self.upload_file(diff_file, local_path, folder_id)


# Return list of all files in specified backup folder
def list_local_files(local_path):
    return os.listdir(local_path)


def main():
    # Load configs file
    try:
        global CONFIGS
        CONFIGS = json.load(open("configs.json", "r", encoding='utf-8'))
    except:
        print("Please rename example file 'configs-example.json' to 'configs.json' and update all fields.")
        return
    
    # Instantiate Drive class and synchronize files
    my_drive = Drive()
    my_drive.synchronize(CONFIGS['local_folder_path'], CONFIGS['drive_folder_id'])


if __name__ == '__main__':
    main()