import { create } from "zustand";
import type { SearchApiError, SearchApiSuccess, SearchResult } from "@/types";

type SearchStore = {
  query: string;
  resumeFile: File | null;
  jobSearchIntent: string[];
  locationPreferences: string[];
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  lastCompletedAt: number | null;
  setQuery: (value: string) => void;
  setResumeFile: (file: File | null) => void;
  addIntent: (value: string) => void;
  removeIntent: (value: string) => void;
  addLocation: (value: string) => void;
  removeLocation: (value: string) => void;
  clearError: () => void;
  reset: () => void;
  submitSearch: () => Promise<void>;
};

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024;

function normalizeTerm(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function dedupe(items: string[], incoming: string): string[] {
  const normIncoming = normalizeTerm(incoming);
  if (!normIncoming) {
    return items;
  }
  if (items.some((item) => item.toLowerCase() === normIncoming.toLowerCase())) {
    return items;
  }
  return [...items, normIncoming];
}

export const useSearchStore = create<SearchStore>((set, get) => ({
  query: "",
  resumeFile: null,
  jobSearchIntent: [],
  locationPreferences: [],
  results: [],
  loading: false,
  error: null,
  lastCompletedAt: null,

  setQuery: (value) => set({ query: value }),
  setResumeFile: (file) => set({ resumeFile: file }),
  addIntent: (value) => set((state) => ({ jobSearchIntent: dedupe(state.jobSearchIntent, value) })),
  removeIntent: (value) =>
    set((state) => ({
      jobSearchIntent: state.jobSearchIntent.filter((item) => item !== value),
    })),
  addLocation: (value) =>
    set((state) => ({ locationPreferences: dedupe(state.locationPreferences, value) })),
  removeLocation: (value) =>
    set((state) => ({
      locationPreferences: state.locationPreferences.filter((item) => item !== value),
    })),
  clearError: () => set({ error: null }),
  reset: () =>
    set({
      query: "",
      resumeFile: null,
      jobSearchIntent: [],
      locationPreferences: [],
      results: [],
      loading: false,
      error: null,
      lastCompletedAt: null,
    }),

  submitSearch: async () => {
    const { query, resumeFile, jobSearchIntent, locationPreferences } = get();
    const cleanedQuery = query.trim();

    if (!cleanedQuery) {
      set({ error: "Enter a search query before submitting." });
      return;
    }
    if (!resumeFile) {
      set({ error: "Upload a resume PDF before submitting." });
      return;
    }
    if (!resumeFile.name.toLowerCase().endsWith(".pdf")) {
      set({ error: "Resume must be a PDF file." });
      return;
    }
    if (resumeFile.size > MAX_FILE_SIZE_BYTES) {
      set({ error: "Resume exceeds the 20MB limit." });
      return;
    }

    const formData = new FormData();
    formData.append("query", cleanedQuery);
    formData.append("resume", resumeFile);

    for (const term of jobSearchIntent) {
      formData.append("job_search_intent", term);
    }
    for (const location of locationPreferences) {
      formData.append("location_preferences", location);
    }

    set({ loading: true, error: null });

    try {
      const response = await fetch("/api/search", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const body = (await response.json().catch(() => ({}))) as SearchApiError;
        const message = body.detail || "Search failed. Please try again.";
        set({ loading: false, error: message, results: [] });
        return;
      }

      const body = (await response.json()) as SearchApiSuccess;
      set({
        loading: false,
        results: Array.isArray(body.search_results) ? body.search_results : [],
        error: null,
        lastCompletedAt: Date.now(),
      });
    } catch {
      set({
        loading: false,
        error: "Unable to reach the API. Check backend status and try again.",
      });
    }
  },
}));
