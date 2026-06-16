/** A 2D size. */
export interface Size {
    /** Width. */
    width: number;

    /** Height. */
    height: number;
}

/** A focal plane with identifier and offset in um. */
export interface FocalPlane {
    /** Id of the focal plane. Use the id in tile requests. */
    id: string;

    /** The offset in um of the focal plane. */
    offsetUm: number;
}

/** A optical path with identifier and description. */
export interface OpticalPath {
    /** The id of the optical path. Use the id in tile requests */
    id: string;

    /** The description of the optical path. */
    description: string;
}

/** A file format identified by MimeType. */
export interface FileFormat {
    /** The MimeType of the format. */
    mimeType: string;
}

/** A tile format identified by MimeType */
export interface TileFormat extends FileFormat {
    /** The extension that should be used for the tile format
     * in tile requests. */
    extension: string;
}

/** A staining. */
export interface Staining {
    /** The display name of the staining. */
    displayName: string;
}

/** A block. */
export interface Block {
    /** The display name of the block. */
    displayName: string;
}

/** A specimen. */
export interface Specimen {
    /** The anatomy of the specimen. */
    anatomy: string;

    /** A description of the specimen. */
    description: string;
}

/**Metadata for an image. Only includes the basic scope and non-PHI properties. */
export interface Image {
    /** The id of the whole-slide image. */
    id: string;

    /**
     * Indicates whether tiles can be retrieved or not. A typical example of when this is
     * false is when not enough sub-sampled pyramid levels are available.
     */
    isStreamable: boolean;

    /** Width and height - in pixels - of the highest resolution pyramid level. */
    imageSize: Size;

    /** Width and height - in pixels - of tiles. */
    tileSize: Size;

    /**
     * The resolution- in microns per pixel (MPP) - of the highest resolution
     * pyramid level.
     */
    micronsPerPixel: number;

    /** Information about focal planes defined during the scanning process. */
    focalPlanes: FocalPlane[];

    /**
     * Informationabout optical paths, if optical pathinformationis available
     * in the image metadata (typically for fluorescence slides).
     */
    opticalPaths: OpticalPath[];

    /**
     * The compression of the image data in the original scanner format.
     */
    storedTileFormat: TileFormat;

    /**
     * List of available formats that can be used to request tiles.
     */
    availableTileFormats: TileFormat[];

    /** The type of the imported whole-slide image files. */
    fileFormat: FileFormat;

    /** Slide staining. Contains the display name from LIS. */
    staining: Staining;

    /**
     * Block from which the tissue slice was cut. Contains the display name
     * from LIS, including specimen.
     */
    block: Block;

    /**
     * Specimen from which the tissue block was cut. Contains anatomy and
     * description.
     */
    specimen: Specimen;
}


export interface CaseImage {
    /** The id of the whole-slide image. */
    id: string;

    /** Slide staining. Contains the display name from LIS. */
    staining: Staining;

    /**
     * Block from which the tissue slice was cut. Contains the display name
     * from LIS, including specimen.
     */
    block: Block;

    /**
     * Specimen from which the tissue block was cut. Contains anatomy and
     * description.
     */
    specimen: Specimen;

    /** The Study Instance UID of the image. */
    seriesInstanceUid: string

    /** The LIS Slide ID of the image. */
    lisSlideId?: string
}