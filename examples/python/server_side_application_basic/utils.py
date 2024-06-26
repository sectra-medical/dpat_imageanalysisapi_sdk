from flask import Flask, request, jsonify
import json
import pandas as pd
import requests
import shutil

def download_info(callbackUrl, slideId, header):
    """
    Download slide information and returns a json of the response.
    """
    pull_info = requests.get(url=callbackUrl + "/slides/" + slideId+"/info?scope=extended&includePHI=true", verify=False, headers=header, stream=True)
    return pull_info.json()

def download_image(outputPath,callbackUrl, slideId, header,anonym_name):
    """
    Download image from Sectra into the specified path with specified name.
    """
    folder_path = os.path.normpath(os.path.join(outputPath, anonym_name))
    if not os.path.exists(folder_path):
        os.mkdir(folder_path)
        print(f"Directory '{folder_path}' created successfully.")
    else:
        print(f"Directory '{folder_path}' already exists. Image not downloaded.")
        return os.path.normpath(os.path.join(outputPath,anonym_name))
    pull_dcm = requests.get(url=callbackUrl + "/slides/" + slideId + "/files", verify=False, headers=header, stream=True) #NOTE: downloaded images are NOT anonymized
    decoder_mime = decoder.MultipartDecoder.from_response(pull_dcm)
    for part in decoder_mime.parts:
        _, dict = parse_header(str(part.headers[b"content-disposition"]))
        filename, size = str.strip(dict["filename"], "'\""), len(part.content)
        with open(os.path.normpath(os.path.join(outputPath,anonym_name,filename)), "wb") as file:
            file.write(part.content)
    return os.path.normpath(os.path.join(outputPath,anonym_name))

def remove_folders(path):
    """
    Removes specified folder and subfolders.
    """
    try:
        shutil.rmtree(path)
        print(f"Folder {path} has been removed")
    except OSError as e:
        print(f"Error: {e}")