export type SearchResult = {
  title?: string;
  snippet?: string;
  link?: string;
  url?: string;
  company?: string;
  [key: string]: unknown;
};

export type SearchApiSuccess = {
  search_results: SearchResult[];
};

export type SearchApiError = {
  detail?: string;
};
