import React, { useEffect } from "react";
import { Box, CircularProgress } from "@mui/material";
import type { IImageAnalysisApiClient } from "../api/ImageAnalysisApi";
import type { Image } from "../models/ImageInfo";
import type { Exam } from "../models/Exam";
import { LOCAL_STORAGE_EXAM_KEY } from "../constants";
import { setExamState } from "../examState";

interface LoadProps {
  client: IImageAnalysisApiClient;
  setExam: React.Dispatch<React.SetStateAction<Exam | null>>;
  setImages: React.Dispatch<React.SetStateAction<Record<string, Image>>>;
}

/**
 * Load component that handles the initial loading and setup of exam data from URL parameters.
 *
 * This component performs the following operations on mount:
 * 1. Extracts the launch URL from query parameters
 * 2. Launches the exam using the provided client
 * 3. Stores the exam request ID in localStorage
 * 4. Fetches all images for slides in the exam blocks
 * 5. Updates the parent component state with exam and images data
 *
 * @param client - The client instance used to launch the app and fetch images
 * @param setExam - Callback function to set the exam data in parent state
 * @param setImages - Callback function to set the images data in parent state
 */
export default function Load({
  client,
  setExam,
  setImages,
}: LoadProps): React.ReactElement {
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const launchUrlParam = getFromSearchParams(urlParams, "launchUrl");
    client
      .launchAsync(launchUrlParam)
      .then((exam) => {
        setExamState(exam);
        localStorage.setItem(LOCAL_STORAGE_EXAM_KEY, exam.request_id);
        const allSlides = exam.blocks.flatMap((block) => block.slides);
        const imagePromises = allSlides.map((slide) =>
          client
            .getImageAsync(slide.id)
            .then((image) => ({ [slide.id]: image }))
        );

        Promise.all(imagePromises).then((imageObjects) => {
          const allImages = imageObjects.reduce(
            (acc, imageObj) => ({ ...acc, ...imageObj }),
            {}
          );
          setImages(allImages);
          setExam(exam);
        });
      })
      .catch((error) => {
        console.error("Error during launch:", error);
      });
  }, [client, setExam, setImages]);
  return (
    <Box
      display="flex"
      justifyContent="center"
      alignItems="center"
      minHeight="50vh"
    >
      <CircularProgress />
    </Box>
  );
}

function getFromSearchParams(
  searchParams: URLSearchParams,
  parameter: string
): string {
  const value = searchParams.get(parameter);
  if (value === null) {
    throw new Error(`Missing parameter ${parameter} in URL search params.`);
  }
  return value;
}
