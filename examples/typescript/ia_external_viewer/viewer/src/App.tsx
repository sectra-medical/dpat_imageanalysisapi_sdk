import { useState, useMemo, useEffect } from "react";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import "./App.css";
import { Paper } from "@mui/material";
import { ImageAnalysisApiClient } from "./api/ImageAnalysisApi";
import type { Image } from "./models/ImageInfo";
import type { Exam } from "./models/Exam";
import ImageViewer from "./components/ImageViewer";
import Header from "./components/Header";
import Load from "./components/Load";
import Clear from "./components/Clear";
import Close from "./components/Close";
import {
  API_VERSION,
  APP_ID,
  APP_VERSION,
  HEADER_HEIGHT,
  SELECTOR_HEIGHT,
} from "./constants";
import { closeOnExamStateChange } from "./examState";

function App() {
  const [exam, setExam] = useState<Exam | null>(null);
  const [images, setImages] = useState<Record<string, Image>>({});
  const [closed, setClosed] = useState<boolean>(false);
  const client = useMemo(
    () =>
      new ImageAnalysisApiClient({
        apiVersion: API_VERSION,
        applicationVersion: APP_VERSION,
        applicationId: APP_ID,
      }),
    []
  );

  useEffect(() => {
    const handler = (event: StorageEvent) =>
      closeOnExamStateChange(event, exam, setClosed);
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, [exam]);

  return (
    <Paper
      style={{
        width: "100vw",
        height: "100vh",
      }}
    >
      <Router>
        <Header exam={exam} height={HEADER_HEIGHT} />
        <Routes>
          <Route path="/Clear" element={<Clear />} />
          <Route path="/Logout" element={<Clear />} />
          <Route
            path="/"
            element={
              closed ? (
                <Close />
              ) : exam === null ? (
                <Load client={client} setExam={setExam} setImages={setImages} />
              ) : (
                <ImageViewer
                  exam={exam}
                  images={images}
                  client={client}
                  appBarHeight={HEADER_HEIGHT}
                  selectorHeight={SELECTOR_HEIGHT}
                />
              )
            }
          />
        </Routes>
      </Router>
    </Paper>
  );
}

export default App;
