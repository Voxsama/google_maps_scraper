"use client";

import { useState, useEffect, useCallback } from "react";
import LeadCard from "@/components/LeadCard";
import LeadTable from "@/components/LeadTable";

interface Lead {
  id?: number;
  business_name: string;
  address: string;
  phone: string;
  category: string;
  rating: number | null;
  review_count: number | null;
  website: string;
  has_website: number;
  search_query: string;
  scraped_at?: string;
}

export default function ResultsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"table" | "cards">("table");
  const [filterNoWebsite, setFilterNoWebsite] = useState(false);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (filterNoWebsite) {
        params.set("no_website", "true");
      }
      const url = `/api/leads${params.toString() ? `?${params.toString()}` : ""}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        setLeads(data.leads);
      } else {
        setError("Failed to fetch leads");
      }
    } catch {
      setError("Failed to fetch leads. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [filterNoWebsite]);

  useEffect(() => {
    fetchLeads();
  }, [fetchLeads]);

  const handleExport = () => {
    const params = new URLSearchParams();
    if (filterNoWebsite) {
      params.set("no_website", "true");
    }
    const exportUrl = `/api/export${params.toString() ? `?${params.toString()}` : ""}`;
    window.location.href = exportUrl;
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-dark-100">Results</h1>
          <p className="text-dark-400 text-sm mt-1">
            {loading
              ? "Loading..."
              : `${leads.length} lead${leads.length !== 1 ? "s" : ""} found`}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* View mode toggle */}
          <div className="flex bg-dark-800 border border-dark-700 rounded-lg overflow-hidden">
            <button
              onClick={() => setViewMode("table")}
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                viewMode === "table"
                  ? "bg-accent-600 text-white"
                  : "text-dark-300 hover:text-dark-100"
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18M3 6h18M3 18h18" />
              </svg>
            </button>
            <button
              onClick={() => setViewMode("cards")}
              className={`px-3 py-2 text-sm font-medium transition-colors ${
                viewMode === "cards"
                  ? "bg-accent-600 text-white"
                  : "text-dark-300 hover:text-dark-100"
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>
          </div>

          {/* Filter toggle */}
          <button
            onClick={() => setFilterNoWebsite(!filterNoWebsite)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterNoWebsite
                ? "bg-danger-500 text-white"
                : "bg-dark-800 border border-dark-700 text-dark-300 hover:text-dark-100"
            }`}
          >
            {filterNoWebsite ? "Showing: No Website Only" : "Show No Website Only"}
          </button>

          {/* Export button */}
          <button
            onClick={handleExport}
            className="px-4 py-2 bg-accent-600 hover:bg-accent-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            Export CSV
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-danger-500/10 border border-danger-500/30 rounded-xl p-4">
          <p className="text-danger-400">{error}</p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-dark-400 text-sm">Loading leads...</p>
          </div>
        </div>
      )}

      {/* Empty state */}
      {!loading && !error && leads.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <svg
            className="w-16 h-16 text-dark-600 mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <h3 className="text-lg font-medium text-dark-200 mb-1">No leads found</h3>
          <p className="text-dark-400 text-sm max-w-md">
            {filterNoWebsite
              ? "No businesses without websites found. Try running a search first or removing the filter."
              : "Start by running a search on the Search page to scrape business leads from Google Maps."}
          </p>
        </div>
      )}

      {/* Results */}
      {!loading && !error && leads.length > 0 && (
        <>
          {viewMode === "table" ? (
            <LeadTable leads={leads} />
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {leads.map((lead, index) => (
                <LeadCard key={lead.id ?? index} lead={lead} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
