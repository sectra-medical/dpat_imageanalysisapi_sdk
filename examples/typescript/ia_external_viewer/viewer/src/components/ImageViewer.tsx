import { Box } from "@mui/material";
import { OpenSeaDragonViewer } from "./OpenSeadragonViewer";
import ImageSelector from "./ImageSelector";
import { type IImageAnalysisApiClient } from "../api/ImageAnalysisApi";
import type { Image } from "../models/ImageInfo";
import type { Exam } from "../models/Exam";
import { useState } from "react";

interface ImageViewerProps {
  exam: Exam;
  images: Record<string, Image>;
  client: IImageAnalysisApiClient;
  appBarHeight: number;
  selectorHeight: number;
}

/**
 * A React component that displays wsi images with a viewer and image selector.
 *
 * @param exam - The medical examination data containing blocks of images
 * @param images - Array of available images for the examination
 * @param client - Client instance for API communication
 * @param appBarHeight - Height of the application bar in pixels, used for positioning
 * @param selectorHeight - Height of the image selector component in pixels
 */
function ImageViewer({
  exam,
  images,
  client,
  appBarHeight,
  selectorHeight,
}: ImageViewerProps) {
  const [selectedImage, setSelectedImage] = useState<Image>(
    Object.values(images)[0]
  );
  return (
    <>
      <Box
        style={{
          position: "fixed",
          top: appBarHeight,
          left: 0,
          width: "100vw",
          height: `calc(100vh - ${appBarHeight}px)`,
        }}
      >
        <OpenSeaDragonViewer image={selectedImage} />
      </Box>
      <Box
        style={{
          backgroundColor: "rgba(247,249,252,0.6)",
          position: "fixed",
          bottom: "1vh",
          left: "1vw",
          paddingRight: "1vw",
          paddingLeft: "1vw",
        }}
      >
        <ImageSelector
          client={client}
          blocks={exam.blocks}
          images={images}
          selectedImage={selectedImage}
          setSelectedImage={setSelectedImage}
          height={selectorHeight}
        />
      </Box>
    </>
  );
}

export default ImageViewer;
