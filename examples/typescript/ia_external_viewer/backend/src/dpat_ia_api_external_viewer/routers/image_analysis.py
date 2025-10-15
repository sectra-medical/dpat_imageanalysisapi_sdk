from typing import Annotated, Optional
from urllib.parse import parse_qs, urlparse

from fastapi import (
    Body,
    Cookie,
    Depends,
    HTTPException,
    Query,
    Response,
    Header,
    Path,
    APIRouter,
)
import httpx

from dpat_ia_api_external_viewer.models import (
    Exam,
    LaunchRequest,
    LaunchResponse,
    Result,
)
from dpat_ia_api_external_viewer.settings import get_settings

router = APIRouter()


async def get_http_client(settings=Depends(get_settings)) -> httpx.AsyncClient:
    """Dependency that provides a configured HTTP client."""
    return httpx.AsyncClient(verify=not settings.ignore_ssl_errors)


@router.post("/launch")
async def launch(
    launch_request: LaunchRequest = Body(...),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Launch against Pathology Image Analysis API. Return the response and set cookies."""
    async with client:
        url = f"{launch_request.launchUrl}?appId={launch_request.appId}"
        response = await client.get(url)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        launch_response = LaunchResponse.model_validate(response.json())
        launch_query_parameters = parse_qs(urlparse(launch_request.launchUrl).query)
        request_id = launch_query_parameters["requestId"][0]
        exam = Exam(
            request_id=request_id,
            blocks=launch_response.blocks,
        )
        response = Response(
            content=exam.model_dump_json(),
            media_type="application/json",
        )
        response.set_cookie(
            key="Token",
            value=launch_response.callback_info.token,
            secure=True,
            httponly=True,
            samesite="strict",
        )
        response.set_cookie(
            key="Callback-Url",
            value=launch_response.callback_info.url,
            secure=True,
            httponly=True,
            samesite="strict",
        )
        return response


@router.get("/requests/{accession_number}/images/info")
async def get_images_in_case(
    accession_number: Annotated[str, Path(title="The accession number of the request")],
    accession_number_issuer: Annotated[
        Optional[str], Query(title="The issuer of the accession number")
    ] = None,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get images for a specific request."""
    async with client:
        url = f"{callback_url}/requests/{accession_number}/images/info"
        if accession_number_issuer:
            url += f"?accessionNumberIssuer={accession_number_issuer}"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get("/slides/{slide_id}/info")
async def get_image(
    slide_id: Annotated[str, Path(title="The slide ID")],
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get image metadata for slide."""
    async with client:
        url = f"{callback_url}/slides/{slide_id}/info"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


async def _get_tile(
    slide_id: str,
    level: int,
    x: int,
    y: int,
    extension: str,
    z: Optional[float],
    channels: Optional[str],
    token: str,
    callback_url: str,
    client: httpx.AsyncClient,
):
    """Get tile from Pathology Image Analysis API.

    FastApi has trouble handling both get_tile routes with the same function,
    as 1_1_0 is interpreted as x=11, y=0, z=None."""
    async with client:
        url = f"{callback_url}/images/{slide_id}_files/{level}/{x}_{y}"
        if z is not None:
            url += f"_{z}"
        url += f".{extension}"
        if channels:
            url += f"?channels={channels}"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return Response(content=response.content, media_type="application/octet-stream")


@router.get("/images/{slide_id}_files/{level}/{x}_{y}_{z}.{extension}")
async def get_tile_with_z(
    slide_id: Annotated[str, Path(title="The slide ID")],
    level: Annotated[int, Path(title="The dzi level of the tile", ge=0)],
    x: Annotated[int, Path(title="The X coordinate of the tile", ge=0)],
    y: Annotated[int, Path(title="The Y coordinate of the tile", ge=0)],
    z: Annotated[float, Path(title="The Z coordinate of the tile")],
    extension: Annotated[str, Path(title="The image format (jpeg, png, etc.)")],
    channels: Annotated[Optional[str], Query(title="Channels to get")] = None,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get tile with Z coordinate from Pathology Image Analysis API."""
    return await _get_tile(
        slide_id=slide_id,
        level=level,
        x=x,
        y=y,
        z=z,
        extension=extension,
        channels=channels,
        token=token,
        callback_url=callback_url,
        client=client,
    )


@router.get("/images/{slide_id}_files/{level}/{x}_{y}.{extension}")
async def get_tile_without_z(
    slide_id: Annotated[str, Path(title="The slide ID")],
    level: Annotated[int, Path(title="The dzi level of the tile", ge=0)],
    x: Annotated[int, Path(title="The X coordinate of the tile", ge=0)],
    y: Annotated[int, Path(title="The Y coordinate of the tile", ge=0)],
    extension: Annotated[str, Path(title="The image format (jpeg, png, etc.)")],
    channels: Annotated[Optional[str], Query(title="Channels to get")] = None,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get tile without Z coordinate from Pathology Image Analysis API."""
    return await _get_tile(
        slide_id=slide_id,
        level=level,
        x=x,
        y=y,
        z=None,
        extension=extension,
        channels=channels,
        token=token,
        callback_url=callback_url,
        client=client,
    )


@router.get("/slides/{slide_id}/label")
async def get_slide_label(
    slide_id: Annotated[str, Path(title="The slide ID")],
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get slide label image for slide."""
    async with client:
        url = f"{callback_url}/slides/{slide_id}/label"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return Response(content=response.content, media_type="application/octet-stream")


@router.get("/applications/{app_id}")
async def get_application(
    app_id: Annotated[str, Path(title="The application ID")],
    token: str = Header(..., alias="Authorization"),
    callback_url: str = Header(..., alias="X-Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get metadata on registered application."""
    async with client:
        url = f"{callback_url}/applications/{app_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.post("/applications/{app_id}/results/")
async def store_result(
    app_id: Annotated[str, Path(title="The application ID")],
    result: Result,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Store result."""
    async with client:
        url = f"{callback_url}/applications/{app_id}/results/"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = await client.post(url, headers=headers, json=result)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code not in [200, 201]:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get("/applications/{app_id}/results/{result_id}")
async def get_result(
    app_id: Annotated[str, Path(title="The application ID")],
    result_id: Annotated[str, Path(title="The result ID")],
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Get result."""
    async with client:
        url = f"{callback_url}/applications/{app_id}/results/{result_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.put("/applications/{app_id}/results/{result_id}")
async def modify_result(
    app_id: Annotated[str, Path(title="The application ID")],
    result_id: Annotated[str, Path(title="The result ID")],
    result: Result,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    client: httpx.AsyncClient = Depends(get_http_client),
):
    """Modify stored result."""
    async with client:
        url = f"{callback_url}/applications/{app_id}/results/{result_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = await client.put(url, headers=headers, json=result)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get("/applications/{app_id}/results/slide/{slide_id}")
async def get_results_for_slide(
    app_id: Annotated[str, Path(title="The application ID")],
    slide_id: Annotated[str, Path(title="The slide ID")],
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    settings=Depends(get_settings),
):
    """Return list of results for slide."""
    async with httpx.AsyncClient(verify=settings.ignore_ssl_errors) as client:
        url = f"{callback_url}/applications/{app_id}/results/slide/{slide_id}"
        headers = {"Authorization": f"Bearer {token}"}
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@router.get("/applications/{app_id}/results/{result_id}/attachments")
async def download_attachment(
    app_id: Annotated[str, Path(title="The application ID")],
    result_id: Annotated[str, Path(title="The result ID")],
    name: Annotated[str, Query(title="The name of the attachment")],
    start: Annotated[
        Optional[int], Query(title="The start byte position", ge=0)
    ] = None,
    end: Annotated[Optional[int], Query(title="The end byte position", ge=0)] = None,
    token: str = Cookie(None, alias="Token"),
    callback_url: str = Cookie(None, alias="Callback-Url"),
    settings=Depends(get_settings),
):
    """Download attachment for result."""
    async with httpx.AsyncClient(verify=settings.ignore_ssl_errors) as client:
        url = f"{callback_url}/applications/{app_id}/results/{result_id}/attachments?name={name}"
        headers = {"Authorization": f"Bearer {token}"}

        if start is not None and end is not None:
            headers["Range"] = f"bytes={start}-{end}"

        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Unauthorized")
        if response.status_code not in [200, 206]:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        return Response(content=response.content, media_type="application/octet-stream")
