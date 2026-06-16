import React, { useEffect, useState } from "react";
import { ImageList, ImageListItem, ImageListItemBar } from "@mui/material";
import type { Image, Size } from "../models/ImageInfo";
import type { IImageAnalysisApiClient } from "../api/ImageAnalysisApi";
import type { ExamBlock } from "../models/Exam";

interface ImageSelectorProps {
  client: IImageAnalysisApiClient;
  blocks: ExamBlock[];
  images: Record<string, Image>;
  selectedImage: Image;
  setSelectedImage: (image: Image) => void;
  height: number;
}

async function getThumbnail(
  image: Image,
  height: number,
  client: IImageAnalysisApiClient
): Promise<string> {
  const width = Math.round(
    (image.imageSize.width * height) / image.imageSize.height
  );
  const baseDziLevel = Math.ceil(
    Math.log2(Math.max(image.imageSize.width, image.imageSize.height))
  );
  const thumbnailDziLevel = Math.ceil(Math.log2(width)) + 1;
  const levelWidth =
    image.imageSize.width / Math.pow(2, baseDziLevel - thumbnailDziLevel);
  const levelHeight =
    image.imageSize.height / Math.pow(2, baseDziLevel - thumbnailDziLevel);

  console.log("level size", thumbnailDziLevel, levelWidth, levelHeight);
  // Calculate number of tiles needed
  const tilesX = Math.ceil(levelWidth / image.tileSize.width);
  const tilesY = Math.ceil(levelHeight / image.tileSize.height);

  // Create a canvas to merge tiles
  const canvas = document.createElement("canvas");
  canvas.width = levelWidth;
  canvas.height = levelHeight;
  const ctx = canvas.getContext("2d");

  if (!ctx) {
    throw new Error("Could not get canvas context");
  }

  // Fetch and draw all tiles
  const tilePromises: Promise<void>[] = [];

  for (let y = 0; y < tilesY; y++) {
    for (let x = 0; x < tilesX; x++) {
      const tilePromise = client
        .getTileAsync(image.id, thumbnailDziLevel, x, y, "0", "jpeg")
        .then((tileBlob) => {
          return new Promise<void>((resolve) => {
            const img = new window.Image();
            img.onload = () => {
              ctx.drawImage(
                img,
                x * image.tileSize.width,
                y * image.tileSize.height
              );
              resolve();
            };
            const blob = new Blob([tileBlob], { type: "image/jpeg" });
            img.src = URL.createObjectURL(blob);
          });
        });
      tilePromises.push(tilePromise);
    }
  }

  // Wait for all tiles to be loaded and drawn
  await Promise.all(tilePromises);

  // Convert to PNG data URL
  return canvas.toDataURL("image/png");
}

/**
 * A component that displays a horizontal list of image thumbnails for selection.
 * Each thumbnail shows an image with its associated block and staining information.
 *
 * @param client - The client instance used to fetch image thumbnails
 * @param blocks - Array of blocks containing slides to display
 * @param images - Record mapping slide IDs to image objects
 * @param selectedImage - The currently selected image object
 * @param setSelectedImage - Function to update the selected image
 * @param height - The height of each thumbnail in pixels
 */
export default function ImageSelector({
  client,
  blocks,
  images,
  selectedImage,
  setSelectedImage,
  height,
}: ImageSelectorProps) {
  const GAP = 10;
  const size: Size = { width: height, height: height };
  const [thumbnails, setThumbnails] = useState<Record<string, string>>({});
  useEffect(() => {
    Object.values(images).map((image) => {
      getThumbnail(image, size.height, client).then((thumbnail) => {
        setThumbnails((prevThumbnails) => ({
          ...prevThumbnails,
          [image.id]: thumbnail,
        }));
      });
    });
  }, [client, images, size.height]);

  function onClick(event: React.MouseEvent<HTMLElement>, image: Image) {
    event.persist();
    setSelectedImage(image);
  }

  return (
    <ImageList gap={GAP} style={{ gridAutoFlow: "column" }}>
      {blocks.map((block) =>
        block.slides.map((slide) => {
          const image = images[slide.id];
          if (!image) {
            return null;
          }
          return (
            <ImageListItem
              key={slide.id}
              onClick={(event) => onClick(event, image)}
            >
              <img
                src={thumbnails[slide.id]}
                loading="lazy"
                alt={slide.id}
                style={{
                  width: size.width,
                  height: size.height,
                  objectFit: "contain",
                  border:
                    "5px solid " +
                    (image.id === selectedImage?.id
                      ? "rgb(60, 115, 187)"
                      : "transparent"),
                }}
              />
              <ImageListItemBar
                title={image.block.displayName}
                subtitle={image.staining.displayName}
              />
            </ImageListItem>
          );
        })
      )}
    </ImageList>
  );
}
