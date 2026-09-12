import { Route, Routes } from "react-router-dom";

import { FlightDetailPage } from "./pages/FlightDetailPage";
import { SearchPage } from "./pages/SearchPage";

export function App() {
  return (
    <Routes>
      <Route path="/" element={<SearchPage />} />
      <Route path="/flight/:ident/:date" element={<FlightDetailPage />} />
    </Routes>
  );
}
