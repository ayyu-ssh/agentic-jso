"use client";

import { useState } from "react";
import { useSearchStore } from "@/store/searchStore";

function ChipRow({
  title,
  items,
  value,
  setValue,
  onAdd,
  onRemove,
  placeholder,
}: {
  title: string;
  items: string[];
  value: string;
  setValue: (value: string) => void;
  onAdd: (value: string) => void;
  onRemove: (value: string) => void;
  placeholder: string;
}): JSX.Element {
  const commitValue = () => {
    if (!value.trim()) {
      return;
    }
    onAdd(value);
    setValue("");
  };

  return (
    <div>
      <label className="mb-2 block text-sm font-semibold uppercase tracking-wide text-ink/80">{title}</label>
      <div className="flex gap-2">
        <input
          className="w-full rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
          placeholder={placeholder}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onBlur={commitValue}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              commitValue();
            }
          }}
        />
        <button
          type="button"
          className="rounded-xl bg-ink px-3 py-2 text-sm font-semibold text-white"
          onClick={commitValue}
        >
          Add
        </button>
      </div>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.map((item) => (
          <button
            key={item}
            type="button"
            className="rounded-full border border-ink/30 bg-white px-3 py-1 text-xs text-ink transition hover:border-ink"
            onClick={() => onRemove(item)}
            title="Remove"
          >
            {item} x
          </button>
        ))}
      </div>
    </div>
  );
}

export function SearchForm(): JSX.Element {
  const [intentDraft, setIntentDraft] = useState("");
  const [locationDraft, setLocationDraft] = useState("");

  const {
    query,
    resumeFile,
    jobSearchIntent,
    locationPreferences,
    loading,
    error,
    setQuery,
    setResumeFile,
    addIntent,
    removeIntent,
    addLocation,
    removeLocation,
    submitSearch,
    reset,
  } = useSearchStore();

  const commitAndSubmit = async () => {
    if (intentDraft.trim()) {
      addIntent(intentDraft);
      setIntentDraft("");
    }
    if (locationDraft.trim()) {
      addLocation(locationDraft);
      setLocationDraft("");
    }
    await submitSearch();
  };

  const handleReset = () => {
    setIntentDraft("");
    setLocationDraft("");
    reset();
  };

  return (
    <section className="rounded-3xl border border-black/10 bg-panel p-5 shadow-soft">
      <div className="mb-5">
        <h2 className="text-2xl font-bold text-ink">Search Inputs</h2>
        <p className="mt-1 text-sm text-ink/70">Upload resume PDF, refine intent, and run the JSO search pipeline.</p>
      </div>

      <div className="space-y-4">
        <div>
          <label className="mb-2 block text-sm font-semibold uppercase tracking-wide text-ink/80">Query</label>
          <input
            className="w-full rounded-xl border border-ink/20 bg-white px-3 py-2 text-sm outline-none ring-accent focus:ring-2"
            placeholder="Example: AI product analyst roles in fintech"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <div>
          <label className="mb-2 block text-sm font-semibold uppercase tracking-wide text-ink/80">Resume (PDF)</label>
          <input
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => setResumeFile(event.target.files?.[0] ?? null)}
            className="block w-full cursor-pointer rounded-xl border border-ink/20 bg-white p-2 text-sm"
          />
          <p className="mt-1 text-xs text-ink/60">
            {resumeFile ? `Selected: ${resumeFile.name}` : "No file selected. Max size 20MB."}
          </p>
        </div>

        <ChipRow
          title="Job Search Intent"
          items={jobSearchIntent}
          value={intentDraft}
          setValue={setIntentDraft}
          onAdd={addIntent}
          onRemove={removeIntent}
          placeholder="ex: startups, remote-first, staff level"
        />

        <ChipRow
          title="Location Preferences"
          items={locationPreferences}
          value={locationDraft}
          setValue={setLocationDraft}
          onAdd={addLocation}
          onRemove={removeLocation}
          placeholder="ex: Bengaluru, Singapore, remote"
        />

        {error ? (
          <p className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</p>
        ) : null}

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            disabled={loading}
            onClick={() => void commitAndSubmit()}
            className="rounded-xl bg-accent px-4 py-2 text-sm font-semibold text-black transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {loading ? "Searching..." : "Run Search"}
          </button>
          <button
            type="button"
            disabled={loading}
            onClick={handleReset}
            className="rounded-xl border border-ink/25 bg-white px-4 py-2 text-sm font-semibold text-ink transition hover:border-ink disabled:cursor-not-allowed disabled:opacity-70"
          >
            Reset
          </button>
        </div>
      </div>
    </section>
  );
}
