import type { SearchResult } from "@/types";
import { ResultCard } from "@/components/ResultCard";

type ResultsListProps = {
  items: SearchResult[];
};

export function ResultsList({ items }: ResultsListProps): JSX.Element {
  if (items.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-ink/30 bg-white/70 p-5 text-sm text-ink/70">
        No results yet. Run a search to see matching opportunities.
      </div>
    );
  }

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {items.map((item, index) => (
        <ResultCard key={`${item.link || item.url || item.title || "result"}-${index}`} item={item} index={index} />
      ))}
    </div>
  );
}
