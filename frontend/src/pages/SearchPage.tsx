import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { FlightSearchForm } from "../components/FlightSearchForm";

export function SearchPage() {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (ident: string, date: string) => {
    setError(null);
    setIsSearching(true);
    try {
      navigate(`/flight/${encodeURIComponent(ident)}/${date}`);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <main className="page search-page">
      <h1>Flight Companion</h1>
      <p className="tagline">
        Look up a flight to see its recent on-time history, live position, and everything else you need
        to know — delays, gate, terminal, and airport info.
      </p>
      <FlightSearchForm onSearch={handleSearch} isSearching={isSearching} error={error} />
    </main>
  );
}
