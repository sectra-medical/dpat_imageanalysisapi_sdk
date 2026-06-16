import { Typography } from "@mui/material";
import React from "react";

/**
 * A React component that automatically closes the current window when rendered.
 *
 * This component calls `window.close()` immediately upon rendering and displays
 * a message indicating that the window should close automatically. Typically used
 * as a cleanup or exit component in popup windows or modal dialogs.
 */
export default function Close(): React.ReactElement {
  window.close();
  return <Typography>This window should be closed automatically.</Typography>;
}
