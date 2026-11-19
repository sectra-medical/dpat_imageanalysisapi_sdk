import { LOCAL_STORAGE_EXAM_KEY } from "./constants"
import type { Exam } from "./models/Exam"

/**
 * Handles storage events to determine when the viewer should be closed due to exam changes.
 *
 * This function monitors local storage changes for exam data and closes the viewer when:
 * - The exam data is removed from storage (newValue is null)
 * - No current exam is loaded (exam is null)
 * - A different exam is loaded (request_id mismatch)
 *
 * @param event - The storage event containing information about the local storage change
 * @param exam - The currently loaded exam object, or null if no exam is loaded
 * @param setClosed - React state setter function to update the closed state of the viewer
 */
export function closeOnExamStateChange(
  event: StorageEvent,
  exam: Exam | null,
  setClosed: React.Dispatch<React.SetStateAction<boolean>>
) {
  if (event.key === LOCAL_STORAGE_EXAM_KEY) {
    if (event.newValue === null || exam === null) {
      setClosed(true);
    } else {
      const newRequestId = event.newValue;
      if (newRequestId !== exam.request_id) {
        setClosed(true);
      }
    }
  }
}

export function setExamState(exam: Exam) {
    localStorage.setItem(LOCAL_STORAGE_EXAM_KEY, exam.request_id);
}

export function clearExamState() {
    localStorage.removeItem(LOCAL_STORAGE_EXAM_KEY);
}