/** An attachment stored for a result. */
export interface Attachment {
    /** The name of the attachment. */
    name: string;

    /** The state of the attachment. `new`, `upload-in-progress`, `stored`. */
    state: string;
}

/** Point. */
export interface Point {
    /** X coordinate. */
    x: number;

    /** Y coordinate. */
    y: number;
}

/** Style. */
export interface ResultStyle {
    /** Color and alpha values for stroke. */
    strokeStyle?: string;

    /** Color and alpha values for fill. */
    fillStyle?: string;

    /** Size of stroke */
    size?: number;
}

/** Polygon. */
export interface Polygon {
    /** Array of points, each with an x and y coordinate. Min 3 points. */
    points: Point[];
}

/** Polyline. */
export interface Polyline {
    /** Array of points, each with an x and y coordinate. Min 2 points. */
    points: Point[];
}

/** Arc. */
export interface Arc {
    /** X and y coordinate of center point. */
    center: Point;

    /** Radius of arc. */
    radius: number;

    /** In radians. */
    startAngle: number;

    /** In radians. */
    endAngle: number;
}

/** Label */
export interface ResultLabel {
    /** X and y coordinate of upper left corner of the label. */
    location: Point;

    /**
     * Text displayed in label. It is recommended to have one label showing
     * the same information as in the displayResult.
     */
    label: string;
}

/** The content of a result. */
export interface ResultContent {
    /** Style applied to all objects. */
    style?: ResultStyle;

    /** Array of polygons. */
    polygons?: Polygon[];

    /** Array of lines. */
    polylines?: Polyline[];

    /** Array of arcs. */
    arcs?: Arc[];

    /** Array of labels. */
    labels?: ResultLabel[];
}

/** Represents a number of graphical representations. */
export interface PrimitiveResult {
    /** The type of the result. */
    type: string;

    /** The content of the result. */
    content: ResultContent[];
}

/** The data for a result. */
export interface ResultData {
    /** Result context (apps private data, don't make it too big). */
    context: Record<string, unknown>;

    /** Result data that is displayed in the Sectra pathology image window. */
    result: PrimitiveResult;
}

/** A result stored on a slide by an application. */
export interface Result {
    /** The internal id of the result. */
    id: number;

    /** Used to prevent corrupted data due to concurrency issues. */
    versionId: string;

    /**
     * The id of slide on which to display result. In case of
     * server-side application, it should be same as the slide the request was
     * initiated on.
     */
    slideId: string;

    /**
     * Textual description of the result. Strongly recommended to be populated
     * with an actual result value relevant to the end-user, e.g. "Ki67 Index:
     * 18.5%". For Primitives, we recommend that the same value is also stored
     * as a label. This value is also shown in the annotation list.
     */
    displayResult?: string;

    /**
     * Key/value pair(s) of results, displayed in the graphics popup.
     * Do not make key names too long since they will be truncated.
     */
    displayProperties: Record<string, string>;

    /**
     * Version of the application that produced the result. Strongly
     * recommended to be populated, so the end-user can distinguish which
     * version of the application produced the result.
     */
    applicationVersion?: string;

    /** List of attachments that will be uploaded for the result. */
    attachments: Attachment[];

    /** Contains the result data. */
    data: ResultData;
}
