from flask import Flask, request, jsonify
import json
import pandas as pd
import requests
import subprocess
import os

#Server-side application to launch a python script.

def download_info(callbackUrl, slideId, header):
    """
    Download slide information and returns a json of the response.
    """
    pull_info = requests.get(url=callbackUrl + "/slides/" + slideId+"/info?scope=extended&includePHI=true", verify=False, headers=header, stream=True)
    return pull_info.json()

IP = "<IP>"

@app.route('/Analysis_run', methods=['GET'])
def handle_analysis_run_get_request():
#     return 'This is a GET request'
    #response example for sectra get
    registration_response = jsonify({
    "applicationId": "<applicationId>",
    "displayName": "Run analysis rerun",
    "manufacturer": "HUG",
    "url": "http://<IP>:5000/Analysis_run",
    "inputTemplate":{"type":"wholeSlide"}
    })
    return registration_response

@app.route('/Analysis_run/info', methods=['GET'])
def handle_analysis_run_get_info_request():
    info = jsonify({
    "apiVersion": "1.6",
    "softwareVersion": "1.0"
    })
    return info

@app.route('/Analysis_run', methods=['POST'])
def handle_analysis_run_post_request():
    
    data = request.json 
    action = data["action"]

    #only run on initial app invocation
    if action == "create":
        slideId = data["slideId"]
        token = data["callbackInfo"]["token"]
        header = {"Authorization": "Bearer " + token, "Content-Type": "application/json"}
        data["callbackInfo"]["url"]
        url = data["callbackInfo"]["url"]
        info = download_info(url, slideId, header)
        slideName = info["lisSlideId"]

        cmd_hp=f'cmd /k "<path_to_python.exe> <path_to_python_script> <arguments>"'
        subprocess.Popen(cmd_hp, creationflags=subprocess.CREATE_NEW_CONSOLE)

    return '', 200

if __name__ == '__main__':
    app.run(host = IP)