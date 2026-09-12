import { useState, type FormEvent } from "react";

interface Props {
  onSearch: (ident: string, date: string) => void;
  isSearching: boolean;
  error: string | null;
}

function today(): string {
  return new Date().toISOString().slice(0, 10);
}

export function FlightSearchForm({ onSearch, isSearching, error }: Props) {
  const [ident, setIdent] = useState("");
  const [date, setDate] = useState(today());

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    const trimmed = ident.trim();
    if (!trimmed) return;
    onSearch(trimmed.toUpperCase(), date);
  };

  return (
    <form className="search-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Flight number</span>
        <input
          type="text"
          placeholder="e.g. UA123"
          value={ident}
          onChange={(e) => setIdent(e.target.value)}
          autoCapitalize="characters"
          required
        />
      </label>
      <label className="field">
        <span>Date</span>
        <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
      </label>
      <button type="submit" disabled={isSearching}>
        {isSearching ? "Searching…" : "Track flight"}
      </button>
      {error && (
        <p role="alert" className="error-text">
          {error}
        </p>
      )}
    </form>
  );
}
