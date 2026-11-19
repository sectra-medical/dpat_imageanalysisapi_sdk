import { AppBar, Box, Stack, Toolbar, Typography } from "@mui/material";
import type { Exam } from "../models/Exam";
import { HEADER_TEXT } from "../constants";

interface HeaderProps {
  exam: Exam | null;
  height: number;
}

/**
 * Header component that displays a fixed application bar with exam information.
 *
 * @param exam - The exam object containing request ID information, or null if no exam is available
 * @param height - The height to set for the toolbar
 */
function Header({ exam, height }: HeaderProps): React.ReactElement {
  return (
    <AppBar position="fixed">
      <Toolbar style={{ height, minHeight: height }}>
        <Box sx={{ flexGrow: 1 }} />
        <Typography
          variant="h6"
          sx={{
            position: "absolute",
            left: "50%",
            transform: "translateX(-50%)",
          }}
        >
          {HEADER_TEXT}
        </Typography>
        <Stack direction="row" spacing={1} sx={{ marginLeft: "auto" }}>
          <Typography variant="body1">Request ID:</Typography>
          <Typography variant="body1">
            {exam !== null ? exam.request_id : "NA"}
          </Typography>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}

export default Header;
