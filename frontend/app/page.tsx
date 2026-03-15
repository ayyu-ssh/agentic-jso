"use client";

import { SearchForm } from "@/components/SearchForm";
import { ResultsList } from "@/components/ResultsList";
import { useSearchStore } from "@/store/searchStore";

function formatTimestamp(timestamp: number | null): string {
  if (!timestamp) {
    return "No search executed yet.";
  }
  return `Last run: ${new Date(timestamp).toLocaleString()}`;
}

export default function HomePage(): JSX.Element {
  const { results, loading, lastCompletedAt } = useSearchStore();

  return (
    <main className="min-h-screen pb-10">
      <div className="mx-auto w-full max-w-6xl px-4 pt-8 sm:px-6 lg:px-8">
        <header className="mb-6 rounded-3xl border border-black/10 bg-panel p-6 shadow-soft">
          <p className="text-xs uppercase tracking-[0.2em] text-ink/70">JSO Prototype</p>
          <h1 className="mt-2 text-3xl font-bold leading-tight text-ink sm:text-4xl">
            Resume-Assisted Job Search
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink/80">
            This frontend is intentionally minimal for fast iteration, while keeping API boundaries and state structure ready for future integration into JSO dashboards.
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1fr_1.25fr]">
          <SearchForm />

          <section className="rounded-3xl border border-black/10 bg-panel p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between gap-4">
              <h2 className="text-2xl font-bold text-ink">Results</h2>
              <p className="text-xs text-ink/60">{formatTimestamp(lastCompletedAt)}</p>
            </div>

            {loading ? (
              <div className="rounded-2xl border border-dashed border-ink/30 bg-white/70 p-5 text-sm text-ink/70">
                Search in progress. This may take a moment while the backend runs resume parsing and parallel source queries.
              </div>
            ) : (
              <ResultsList items={results} />
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
