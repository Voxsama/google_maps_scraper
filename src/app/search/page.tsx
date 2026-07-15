"use client";

import { useState } from "react";
import Link from "next/link";

interface ScrapeResult {
  success: boolean;
  leads?: Array<{
    business_name: string;
    address: string;
    phone: string;
    category: string;
    rating: number | null;
    review_count: number | null;
    website: string;
    has_website: number;
  }>;
  count?: number;
  error?: string;
}

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: query.trim() }),
      });

      const data: ScrapeResult = await response.json();

      if (!response.ok || !data.success) {
        setError(data.error || "An unexpected error occurred");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to connect to the server"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh]">
      <h1 className="text-3xl font-bold text-dark-100 mb-2">
        Find Businesses Without Websites
      </h1>
      <p className="text-dark-400 mb-8 text-center max-w-md">
        Search Google Maps for local businesses and discover leads that need a
        website.
      </p>

      <div className="w-full max-w-xl">
        <div className="flex gap-3">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !loading) handleSearch();
            }}
            placeholder="e.g. plumbers in Austin TX"
            disabled={loading}
            className="flex-1 px-4 py-3 rounded-lg bg-dark-800 border border-dark-600 text-dark-100 placeholder-dark-500 focus:outline-none focus:ring-2 focus:ring-accent-500 focus:border-transparent disabled:opacity-50"
          />
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-6 py-3 bg-accent-600 hover:bg-accent-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg
                  className="animate-spin h-4 w-4"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  ></circle>
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  ></path>
                </svg>
                Scraping...
              </span>
            ) : (
              "Search"
            )}
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="mt-6 p-4 rounded-lg bg-dark-800 border border-dark-700 text-center">
            <div className="flex items-center justify-center gap-3">
              <svg
                className="animate-spin h-5 w-5 text-accent-400"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              <p className="text-dark-200 font-medium">
                Scraping Google Maps... This may take a minute
              </p>
            </div>
            <p className="text-dark-400 text-sm mt-2">
              Scrolling through results and extracting business details
            </p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="mt-6 p-4 rounded-lg bg-danger/10 border border-danger/30">
            <p className="text-danger font-medium">Error</p>
            <p className="text-danger/80 text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Success State */}
        {result && result.success && (
          <div className="mt-6 p-4 rounded-lg bg-success/10 border border-success/30">
            <p className="text-success font-medium">Scraping Complete!</p>
            <p className="text-dark-200 text-sm mt-1">
              Found{" "}
              <span className="font-bold text-dark-100">{result.count}</span>{" "}
              businesses.{" "}
              {result.leads &&
                `${result.leads.filter((l) => !l.has_website).length} without a website.`}
            </p>
            <Link
              href="/results"
              className="inline-block mt-3 px-4 py-2 bg-accent-600 hover:bg-accent-700 text-white text-sm font-medium rounded-lg transition-colors"
            >
              View Results
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
