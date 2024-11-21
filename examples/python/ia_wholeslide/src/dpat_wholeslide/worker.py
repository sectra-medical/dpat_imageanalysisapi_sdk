#!/usr/bin/env python
import io
import os
import json
import sys

from pathlib import Path
import time

import PIL  # pip install pillow
import PIL.Image

import click
from click import secho
from requests_toolbelt import MultipartDecoder
from tqdm import tqdm

from dpat_wholeslide.version import __version__
from dpat_wholeslide.dzidesc import DziDescription
from dpat_wholeslide.utils import requests_session_from_callbackinfo
from dpat_wholeslide.locks import lock_release, lock_try_acquire


# %%

# --------------------------------------------
# Common
# --------------------------------------------


def latest_request_data(folder_path):
    """
    Given a folder path, locate the latest request data file and return its contents as a dict.
    """
    latest_file = sorted(folder_path.glob("request*.json"))
    if not latest_file:
        return None
    latest_file = latest_file[-1]
    return json.loads(latest_file.read_text())


def session_from_folder(folder_path):
    """
    Given a folder path, locate the latest request data file and return a requests Session
    together with the request data.
    """
    req = latest_request_data(folder_path)
    if not req:
        return None, None
    api = requests_session_from_callbackinfo(req["callbackInfo"])
    return api, req


# --------------------------------------------
# CLI Commands
# --------------------------------------------


@click.group()
def main():
    pass


# ============================================
# Download Thumbnail
# ============================================
@main.command(name="thumbnail", help="download slide thumbnail")
@click.argument("folder")
def cli_download_thumbnail(folder):
    """
    Download a thumbnail for the given slide and persist in the folder as 'thumbnail.jpg'.

    Examplifies using the tile-based (Deep Zoom Image (DZI) pyramid) API calls.
    """
    folder_path = Path(folder)
    return download_thumbnail(folder_path)


def download_thumbnail(folder_path):
    secho(f"downloading thumbnail for '{folder_path}'")
    # - locate latest request_user file
    api, req = session_from_folder(folder_path)

    # request image metadata
    # we re-download metadata even though its in theory persisted in req already
    # (for clarity)
    slide_id = req["slideId"]
    metadata = api.get(f"slides/{slide_id}/info?scope=extended&includePHI=false").json()
    # DziDescription is a helper class to manage Deep Zoom Image (DZI) pyramid logic,
    # useful when requesting tiles from the Sectra DPAT IA-API.
    dzi = DziDescription(
        metadata["imageSize"]["width"],
        metadata["imageSize"]["height"],
        tile_size=metadata["tileSize"]["width"],
        tile_overlap=0,
        resolution=metadata["micronsPerPixel"],
    )
    wanted_mpp = 64.0  # this is microns per pixel, suitable for a thumbnail
    (lvl_dzi, mpp_at_level, mpp_diff_f) = dzi.level_at_mpp(
        wanted_mpp, always_smaller=True
    )
    # prepare a blank image to paste the tiles into
    dst_img = PIL.Image.new("RGB", (lvl_dzi.width(), lvl_dzi.height()), color=(0, 0, 0))
    # iterate over all tiles in the level and download them
    for tiledesc in tqdm(
        lvl_dzi.tiles_for_level(),
        desc="downloading thumbnail tiles",
        total=lvl_dzi.n_tiles(),
    ):
        # This is the Sectra DPAT IA-API endpoint for downloading tiles
        # GET <callback URL>/images/<slideId>_files/<level>/<x>_<y>[_<foc_plane>].<ext>[?opticalPath=<opticalPathId>]
        img = io.BytesIO(
            api.get(
                f"images/{slide_id}_files/{tiledesc.tile.level}/{tiledesc.tile.col}_{tiledesc.tile.row}_0.jpg"
            ).content
        )
        img_pil = PIL.Image.open(img).convert("RGB")
        img_cropped = img_pil.crop(
            (
                tiledesc.crop.left,
                tiledesc.crop.top,
                tiledesc.crop.right,
                tiledesc.crop.bottom,
            )
        )
        dst_img.paste(
            img_cropped, box=(int(tiledesc.place_point.x), int(tiledesc.place_point.y))
        )
    # save the thumbnail to disk
    dst_filepath = folder_path / "thumbnail.jpg"
    dst_img.save(dst_filepath)
    secho(f"wrote thumbnail to '{dst_filepath}'")

    # - download slide label image (NOTE: might contain PHI!)
    r = api.get(f"slides/{slide_id}/label")
    r.raise_for_status()
    if r.status_code == 204:
        secho("no label image stored for this slide")
    else:
        img = io.BytesIO(r.content)
        img_pil = PIL.Image.open(img).convert("RGB")
        dst_label_filepath = folder_path / "label.jpg"
        img_pil.save(dst_label_filepath)
        secho(f"wrote label image to '{dst_label_filepath}'")
    secho("done")


# ============================================
# Set Progress Percentage
# ============================================


@main.command(
    help="update progress text for a given FOLDER (e.g. 'data/queue/my-request/my-slide')"
)
@click.option(
    "--text",
    help="Explicit text to set as label, use '{}' to insert percentage.",
    required=False,
    default="analysis, progress {} %",
)
@click.argument("folder")
@click.argument("percent")
def progress(folder, text, percent):
    """
    Update the progress text for the latest result (annotation) in the given slide folder.

    if text is None, will default to "analysis, progress {} %" where {} is replaced by the percentage.
    """
    # parse inputs
    folder_path = Path(folder)
    if not folder_path.exists():
        secho(
            f"Error: invalid folder path '{folder}' -- the path does not exist.",
            fg="red",
        )
        sys.exit(1)
    secho(f"updating progress text for '{folder_path}'")
    # - locate latest request_user file
    api, req = session_from_folder(folder_path)
    set_progress(api, req, text, percent)
    secho("done")


def set_progress(api, req, text, progress_percent):
    """
    Update the progress text for the latest result (annotation) of the slide described in req.
    """
    new_text = text
    if not new_text:
        new_text = "analysis, progress {} %"
    if "{}" in new_text:
        new_text = new_text.format(progress_percent)

    # TODO: use this code in webserver.py as well (currently its duplicated)
    # TODO: seems this could be a more generic upsert operation for results
    r = api.get(f"slides/{req['slideId']}/info?scope=extended&includePHI=false")
    r.raise_for_status()
    metadata = r.json()
    max_y = metadata["imageSize"]["height"] / metadata["imageSize"]["width"]

    store_data = {
        "slideId": req["slideId"],
        "displayResult": new_text,  # text as shown in the annotation list (L)
        "displayProperties": {
            # table-style properties shown when the annotation is selected
            "Progress": f"{progress_percent} %"
        },
        "applicationVersion": __version__,
        "data": {
            "context": {},
            "result": {
                "type": "primitive",
                "content": {
                    "style": {
                        "fillStyle": None,
                        "size": None,
                        "strokeStyle": "#FFA500",
                    },
                    "polygons": [
                        {
                            "points": [
                                {"x": 0.0, "y": 0.0},
                                {"x": 1.0, "y": 0.0},
                                {"x": 1.0, "y": max_y},
                                {"x": 0.0, "y": max_y},
                            ]
                        }
                    ],
                    "labels": [
                        # place label at the top center
                        {"location": {"x": 0.5, "y": 0.0}, "label": new_text}
                    ],
                },
            },
        },
    }

    # check if there is already an app result from our app for this slide
    r = api.get(f"applications/{req['applicationId']}/results/slide/{req['slideId']}")
    r.raise_for_status()
    existing_annots = r.json()
    if len(existing_annots) > 0:
        latest_annot = existing_annots[-1]
        old_text = latest_annot["displayResult"]
        latest_annot.update(store_data)
        secho(f"  updating '{old_text}' -> '{new_text}'")
        response = api.put(
            f"applications/{req['applicationId']}/results/{latest_annot['id']}",
            json=latest_annot,
        )
    else:
        secho(f"  adding new '{new_text}'")
        response = api.post(
            f"applications/{req['applicationId']}/results/", json=store_data
        )
    response.raise_for_status()


# ============================================
# Download WSI files
# ============================================
@main.command(name="wsi", help="download WSI")
@click.argument("folder")
def cli_download_wsi(folder):
    """
    Download the WSI file(s) for the given slide and persist in the folder below 'wsi_files'.
    """
    return download_wsi(folder)


def download_wsi(folder):
    folder_path = Path(folder)
    # - locate latest request_user file
    api, req = session_from_folder(folder_path)
    slide_id = req["slideId"]

    secho(f"downloading WSI for '{folder_path}'")
    r = api.get(f"slides/{slide_id}/files", stream=True)

    # TODO: the MultipartDecoder in requests-toolbelt reads the entire r.content
    #       into memory, which means we need to rewrite this to use a custom implementation
    if r.headers["Content-Type"].startswith("multipart/related"):
        # multiple files
        decoder = MultipartDecoder.from_response(r, "utf-8")
        for r_part in decoder.parts:
            # take all keys in r_part.headers and convert them from byte to str
            headers = {
                k.decode("utf-8"): v.decode("utf-8") for k, v in r_part.headers.items()
            }
            filename = (
                headers["Content-Disposition"].split("filename=")[1].strip('""')
                + ".dcm"
            )
            dest_path = folder_path / f"wsi_files/{filename}"
            if not dest_path.exists():
                dest_path.parent.mkdir(exist_ok=True, parents=True)
                # we can safely write the entire content to disk here
                # because it is already in memory
                with open(dest_path, "wb") as f:
                    f.write(r_part.content)
                print(f"wsi saved to '{dest_path}'")
            else:
                print(f"file already existed, ignored: '{dest_path}'")
    else:
        # application/octet-stream -- single file
        filename = r.headers["Content-Disposition"].split("filename=")[1].strip('""')
        tmp_path = folder_path / f"wsi_files/{filename}.part"
        dest_path = folder_path / f"wsi_files/{filename}"
        if not dest_path.exists():
            print("downloading", dest_path)
            dest_path.parent.mkdir(exist_ok=True, parents=True)
            with open(tmp_path, "wb") as f:
                # configure tqdm to output download speed
                sbar = tqdm(
                    unit="B", ascii=True, unit_scale=True, desc="downloading wsi"
                )
                # stream chunks and write to disk
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    sbar.update(len(chunk))
                    f.write(chunk)
            tmp_path.rename(dest_path)
            print(f"done, wsi saved to '{dest_path}'")
        else:
            print(f"file already exists: '{dest_path}'")


# ============================================
# watch -- e.g. act as Queue Controller
# ============================================
@main.command(name="watch", help="start monitoring for WSI processing requests")
@click.argument("queue_folder")
def cli_watch(queue_folder):
    """
    Start a persistent monitoring process that acts when user requests are made.
    """
    secho(f"starting watch loop, monitoring '{queue_folder}'")
    secho("Press CTRL-C to stop.")
    while True:
        # list all .txt files in queue_folder sorted by modification time (oldest first)
        for queue_file in sorted(
            Path(queue_folder).glob("*.txt"), key=os.path.getmtime
        ):
            queue_file_lock = queue_file.with_suffix(".lock")
            queue_lock = lock_try_acquire(str(queue_file_lock))
            if queue_lock is None:
                # lock not acquired, skip this file
                continue

            # lock acquired, process the file
            try:
                secho(f"processing request in '{queue_file}'")
                # read the file and extract the path to the request file
                req_file_relpath = Path(queue_file.read_text().strip())
                req_file = queue_file.parent / req_file_relpath
                req = json.loads(req_file.read_text())
                api = requests_session_from_callbackinfo(req["callbackInfo"])
                set_progress(api, req, None, 10)

                # download thumbnail
                thumbnail_path = req_file.parent / "thumbnail.jpg"
                if not thumbnail_path.exists():
                    download_thumbnail(req_file.parent)
                set_progress(api, req, None, 20)

                # - download WSI
                wsi_folder_path = req_file.parent / "wsi_files"
                if len(list(wsi_folder_path.glob("*"))) == 0:
                    download_wsi(req_file.parent)
                set_progress(api, req, None, 40)

                # calculate something complicated
                secho("doing some complicated analysis")
                time.sleep(2)
                set_progress(api, req, None, 60)
                time.sleep(2)
                set_progress(api, req, None, 80)
                time.sleep(2)
                set_progress(api, req, None, 100)

                # - save final result
                metadata = api.get(
                    f"slides/{req['slideId']}/info?scope=extended&includePHI=false"
                ).json()
                max_y = metadata["imageSize"]["height"] / metadata["imageSize"]["width"]
                text = "ANSWER: 42"

                store_data = {
                    "slideId": req["slideId"],
                    "displayResult": text,  # text as shown in the annotation list (L)
                    "displayProperties": {},
                    "applicationVersion": __version__,
                    "data": {
                        "context": {},
                        "result": {
                            "type": "primitive",
                            "content": {
                                "style": {
                                    "fillStyle": None,
                                    "size": None,
                                    "strokeStyle": "#FFA500",
                                },
                                "polygons": [
                                    {
                                        "points": [
                                            {"x": 1 * (1.0 / 3), "y": 1 * (max_y / 3)},
                                            {"x": 2 * (1.0 / 3), "y": 1 * (max_y / 3)},
                                            {"x": 2 * (1.0 / 3), "y": 2 * (max_y / 3)},
                                            {"x": 1 * (1.0 / 3), "y": 2 * (max_y / 3)},
                                        ]
                                    }
                                ],
                                "labels": [
                                    # place label at the center
                                    {
                                        "location": {"x": 0.5, "y": max_y / 2.0},
                                        "label": text,
                                    }
                                ],
                            },
                        },
                    },
                }

                # check for existing result
                r = api.get(
                    f"applications/{req['applicationId']}/results/slide/{req['slideId']}"
                )
                existing_annots = r.json()
                if len(existing_annots) > 0:
                    # update existing resulti nstead
                    latest_annot = existing_annots[-1]
                    latest_annot.update(store_data)
                    response = api.put(
                        f"applications/{req['applicationId']}/results/{latest_annot['id']}",
                        json=latest_annot,
                    )
                else:
                    response = api.post(
                        f"applications/{req['applicationId']}/results/", json=store_data
                    )
                response.raise_for_status()
                secho("saved final result. done")
                # - remove queue file
                queue_file.unlink()
            finally:
                lock_release(queue_lock)
            # break the loop - we want to re-read the directory listing since
            # concurrent workers might have removed/added files
            break
        # sleep for a while
        secho("sleeping for 5 seconds before re-listing queue directory")
        time.sleep(10)


# %%

if __name__ == "__main__":
    main()
