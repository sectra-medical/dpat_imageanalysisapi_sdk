import OpenSeadragon, { DziTileSource } from "openseadragon";
import React, { useEffect } from "react";
import type { Image } from "../models/ImageInfo";

interface OpenSeaDragonViewerProps {
  image: Image;
}

function OpenSeaDragonViewer({
  image,
}: OpenSeaDragonViewerProps): React.ReactElement {
  useEffect(() => {
    const viewer = createViewer(image);
    return () => {
      closeViewer(viewer);
    };
  }, [image]);
  return (
    <div
      id="viewer"
      style={{
        width: "100%",
        height: "100%",
      }}
    />
  );
}
export { OpenSeaDragonViewer };

function createDziTileSource(image: Image): DziTileSource {
  return new DziTileSource(
    image.imageSize.width,
    image.imageSize.height,
    image.tileSize.width,
    0,
    // @ts-expect-error Wrong type definition
    "/api/image_analysis/images/" + image.id + "_files/",
    "jpeg",
    false,
    undefined,
    undefined
  );
}

function createViewer(image: Image): OpenSeadragon.Viewer {
  const tileSource = createDziTileSource(image);
  const options = {
    id: "viewer",
    tileSources: tileSource,
    showZoomControl: false,
    showHomeControl: false,
    showFullPageControl: false,
    zoomPerScroll: 2,
    showNavigator: true,
    loadTilesWithAjax: true,
  };
  return OpenSeadragon(options);
}

function closeViewer(viewer: OpenSeadragon.Viewer): void {
  viewer.close();
  viewer.destroy();
}
