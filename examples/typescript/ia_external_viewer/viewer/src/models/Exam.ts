import type { Image } from "./ImageInfo"

/** A Slide available in the exam. */
export interface ExamSlide {
    /** The id of the slide. */
    id: string;

    /** Description of the slide. */
    description: string;
}

/** A block available in the exam. */
export interface ExamBlock {
    /** The name of the block. */
    name: string;

    /** Slides in the block available in the exam. */
    slides: ExamSlide[];
}


/** An Exam containing blocks and a request ID. */
export interface Exam {
    /** The request ID of the exam. */
    request_id: string;

    /** The blocks in the exam. */
    blocks: ExamBlock[];
}

/** An Exam extended with a mapping of slide IDs to their corresponding image data. */
export interface ExamWithImages extends Exam {
    /** A mapping of slide IDs to their corresponding image data. */
    images: Record<string, Image>;
}