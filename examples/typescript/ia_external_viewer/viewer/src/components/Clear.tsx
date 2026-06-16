import React from "react";
import Close from "./Close";
import { clearExamState } from "../examState";

/**
 * Clears the exam data from local storage and renders a Close component.
 *
 * This component performs a side effect by removing the exam key from localStorage
 * when it's rendered, then displays a Close component.
 */
export default function Clear(): React.ReactElement {
  clearExamState();
  return <Close />;
}
