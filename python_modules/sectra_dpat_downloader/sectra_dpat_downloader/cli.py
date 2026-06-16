import logging
from pathlib import Path
from typing import Callable, Iterable, List, Optional

import click
from sectra_dpat_downloader.models import CaseImage
from sectra_dpat_downloader.client import SectraDpatDownloader
from concurrent.futures import ThreadPoolExecutor


def download_wsi_images_in_case(
    base_url: str,
    application_id: str,
    username: str,
    password: str,
    accession_number: str,
    output_folder: Path,
    accession_number_issuer: Optional[str],
    include_metadata: bool,
    threads: int,
):
    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
    client = SectraDpatDownloader.from_credentials(
        base_url=base_url,
        application_id=application_id,
        username=username,
        password=password,
    )

    images_in_case = list(
        client.get_images_in_case(
            accession_number=accession_number,
            accession_number_issuer=accession_number_issuer,
        )
    )
    logging.info(f"Found {len(images_in_case)} images in case {accession_number}")
    try:
        from tqdm.contrib.concurrent import thread_map
        from tqdm.contrib.logging import logging_redirect_tqdm

        def map_function(fn: Callable, iterable: Iterable, max_workers: int, **kwargs):
            with logging_redirect_tqdm():
                list(
                    thread_map(
                        fn,
                        iterable,
                        max_workers=max_workers,
                        **kwargs,
                    )
                )

    except ImportError:

        def map_function(fn: Callable, iterable: Iterable, max_workers: int, **kwargs):
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(
                    executor.map(
                        fn,
                        iterable,
                    )
                )

    failed_image_ids: List[str] = []

    def process_image(image: CaseImage):
        try:
            image_id = image.lis_slide_id or image.id

            image_output_folder = output_folder.joinpath(image_id)
            logging.info(
                f"Downloading image {image_id} with staining {image.staining.display_name} and block {image.block.display_name} to {image_output_folder}"
            )
            image_output_folder.mkdir(parents=True, exist_ok=True)
            client.download_image_files(image.id, output_folder=image_output_folder)
            if include_metadata:
                metadata_file = image_output_folder.joinpath(image_id).with_suffix(
                    ".json"
                )
                logging.info(
                    f"Downloading metadata for image {image_id} to {metadata_file}"
                )
                metadata = client.get_image_metadata(image.id)
                with open(metadata_file, "w") as file:
                    file.write(metadata.model_dump_json(indent=4))

        except Exception:
            logging.error(
                f"Failed to download image {image.id} with staining {image.staining.display_name} and block {image.block.display_name}",
                exc_info=True,
            )
            failed_image_ids.append(image.id)

    map_function(process_image, images_in_case, max_workers=threads)
    if failed_image_ids:
        raise RuntimeError(
            f"Failed to download {len(failed_image_ids)} of {len(images_in_case)} "
            f"images in case {accession_number}: {', '.join(failed_image_ids)}"
        )
    logging.info(f"WSI images downloaded to {output_folder}")


@click.command()
@click.option("--base-url", required=True, help="Base URL of the server")
@click.option(
    "--application-id", required=True, help="Application ID for authentication"
)
@click.option("--username", required=True, help="Username for authentication")
@click.option(
    "--password",
    required=True,
    prompt=True,
    hide_input=True,
    help="Password for authentication",
)
@click.option("--accession-number", required=True, help="Accession number of exam")
@click.option(
    "--output-folder",
    required=True,
    type=click.Path(path_type=Path),
    help="Folder to save the downloaded WSI image",
)
@click.option(
    "--accession-number-issuer",
    default=None,
    help="Optional issuer of the accession number",
)
@click.option(
    "--metadata",
    is_flag=True,
    help="Include metadata for the downloaded images",
)
@click.option(
    "--threads",
    default=1,
    type=int,
    help="Number of threads to use for downloading images",
)
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level",
)
def main(
    base_url,
    application_id,
    username,
    password,
    accession_number,
    output_folder,
    accession_number_issuer,
    metadata,
    threads,
    log_level,
):
    """Download WSI images in exam from a server."""
    logging.basicConfig(level=log_level)

    try:
        download_wsi_images_in_case(
            base_url=base_url,
            application_id=application_id,
            username=username,
            password=password,
            accession_number=accession_number,
            output_folder=output_folder,
            accession_number_issuer=accession_number_issuer,
            include_metadata=metadata,
            threads=threads,
        )
    except RuntimeError as error:
        raise click.ClickException(str(error))
