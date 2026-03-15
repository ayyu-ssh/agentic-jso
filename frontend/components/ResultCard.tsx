import type { SearchResult } from "@/types";

type ResultCardProps = {
  item: SearchResult;
  index: number;
};

export function ResultCard({ item, index }: ResultCardProps): JSX.Element {
  const title = typeof item.title === "string" ? item.title : "Untitled role";
  const snippet = typeof item.snippet === "string" ? item.snippet : "No description snippet was returned.";
  const url =
    (typeof item.link === "string" && item.link) ||
    (typeof item.url === "string" && item.url) ||
    "";

  return (
    <article
      className="animate-riseIn rounded-2xl border border-black/10 bg-panel p-4 shadow-soft"
      style={{ animationDelay: `${Math.min(index, 8) * 70}ms` }}
    >
      <h3 className="text-lg font-semibold leading-tight text-ink">{title}</h3>
      <p className="mt-3 text-sm leading-relaxed text-ink/80">{snippet}</p>
      {url ? (
        <a
          href={url}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block rounded-full border border-ink px-3 py-1 text-xs font-semibold uppercase tracking-wide text-ink transition hover:bg-ink hover:text-white"
        >
          Open Listing
        </a>
      ) : (
        <span className="mt-4 inline-block rounded-full border border-ink/25 px-3 py-1 text-xs text-ink/60">
          Link unavailable
        </span>
      )}
    </article>
  );
}
