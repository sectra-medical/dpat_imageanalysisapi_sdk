# -*- coding: utf-8 -*-

"""
analysisapi -- python client for the Sectra Pathology Image Analysis API

This is a requests-style, non-async implementation.
"""

import logging as log
from io import BytesIO
import time
import requests

DEFAULT_TIMEOUT = (
    3.0 * 2 + 0.05,
    30.0 * 2,
)  # ( connect_timeout, read_timeout ) in seconds


class AnalysisApi:
    def __init__(self, url, hookname, token=None, api_version="1.5"):
        """
        @param url -- typically https://localhost/SectraPathologyServer/external/imageanalysis/v1
        """
        self.url = url
        self.name = hookname
        self.token = token
        self._session = requests.Session()
        self.api_version = api_version

    def _auth_get(self, url, ok_codes=[200]):
        """make GET request adding the bearer token"""
        r = self._session.get(url, headers=self._headers(), timeout=DEFAULT_TIMEOUT)
        if not r.status_code in ok_codes:
            r.raise_for_status()
        return r

    def slideinfo(self, slide_id):
        """GET slide metadata for slide"""
        r = self._auth_get("{}/slides/{}/info".format(self.url, slide_id))
        slide_info = r.json()["blocks"][0]["slides"][0]  # yeah, weird
        return slide_info

    def tile(self, slide_id, dzilvl, col, row, zstack=0, format="jpg"):
        """retrieve an image tile"""
        tile_url = "{}/images/{}_files/{}/{}_{}_{}.{}".format(
            self.url, slide_id, dzilvl, col, row, zstack, format
        )
        r = self._session.get(
            tile_url, headers=self._headers(), timeout=DEFAULT_TIMEOUT
        )
        if not r.status_code == 200:
            r.raise_for_status()
        return BytesIO(r.content)

    def store_result(self, result_data):
        """store result into sectra pathology db"""
        url = f"{self.url}/hooks/{self.name}/results/"
        r = self._session.post(
            url, headers=self._headers(), timeout=DEFAULT_TIMEOUT, json=result_data
        )
        if not r.status_code == 200:
            r.raise_for_status()
        parsed = r.json()
        return parsed

    def update_result(self, result_data):
        """update existing result"""
        result_id = result_data["id"]
        url = f"{self.url}/hooks/{self.name}/results/{result_id}"
        r = self._session.put(
            url, headers=self._headers(), timeout=DEFAULT_TIMEOUT, json=result_data
        )
        if not r.status_code == 200:
            r.raise_for_status()
        parsed = r.json()
        return parsed

    def _headers(self):
        return {
            "Authorization": "Bearer {}".format(self.token),
            "X-Sectra-ApiVersion": f"{self.api_version}",
        }
