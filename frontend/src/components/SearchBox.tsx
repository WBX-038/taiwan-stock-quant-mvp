import { Search } from "lucide-react";
import { FormEvent, useState } from "react";

type Props = {
  loading: boolean;
  onSearch: (query: string) => void;
};

export function SearchBox({ loading, onSearch }: Props) {
  const [query, setQuery] = useState("2330");

  function submit(event: FormEvent) {
    event.preventDefault();
    const clean = query.trim();
    if (clean) onSearch(clean);
  }

  return (
    <form className="search" onSubmit={submit}>
      <Search size={20} aria-hidden="true" />
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="輸入台股名稱或代號，例如 台積電 / 2330"
        aria-label="股票名稱或代號"
      />
      <button type="submit" disabled={loading}>
        {loading ? "分析中" : "分析"}
      </button>
    </form>
  );
}
