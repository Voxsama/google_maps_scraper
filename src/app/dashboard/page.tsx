"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

interface LeadStats {
  total_leads: number;
  leads_without_websites: number;
  leads_with_websites: number;
  unique_queries: number;
}

interface RecentSearch {
  search_query: string;
  last_scraped: string;
  lead_count: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<LeadStats | null>(null);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const res = await fetch("/api/stats");
        const data = await res.json();
        if (data.success) {
          setStats(data.stats);
          setRecentSearches(data.recent_searches);
        }
      } catch (err) {
        console.error("Failed to fetch stats:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  const noWebsitePercent =
    stats && stats.total_leads > 0
      ? Math.round((stats.leads_without_websites / stats.total_leads) * 100)
      : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-accent-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-dark-400 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-dark-100">Dashboard</h1>
        <p className="text-dark-400 text-sm mt-1">
          Overview of your scraped leads and opportunities
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Leads */}
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-accent-600/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-accent-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold text-dark-100">{stats?.total_leads ?? 0}</p>
          <p className="text-dark-400 text-sm mt-1">Total Leads</p>
        </div>

        {/* No Website - Opportunity */}
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700 border-l-4 border-l-danger-500">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-danger-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-danger-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold text-danger-400">{stats?.leads_without_websites ?? 0}</p>
          <p className="text-dark-400 text-sm mt-1">No Website (Opportunity!)</p>
          {stats && stats.total_leads > 0 && (
            <p className="text-danger-400 text-xs mt-2 font-medium">
              {noWebsitePercent}% of leads don&apos;t have a website
            </p>
          )}
        </div>

        {/* Has Website */}
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-success-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-success-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold text-dark-100">{stats?.leads_with_websites ?? 0}</p>
          <p className="text-dark-400 text-sm mt-1">Has Website</p>
        </div>

        {/* Unique Searches */}
        <div className="bg-dark-800 rounded-xl p-6 border border-dark-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 rounded-lg bg-warning-500/20 flex items-center justify-center">
              <svg className="w-5 h-5 text-warning-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
          <p className="text-3xl font-bold text-dark-100">{stats?.unique_queries ?? 0}</p>
          <p className="text-dark-400 text-sm mt-1">Unique Searches</p>
        </div>
      </div>

      {/* Recent Searches */}
      <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
        <div className="px-6 py-4 border-b border-dark-700">
          <h2 className="text-lg font-semibold text-dark-100">Recent Searches</h2>
        </div>
        {recentSearches.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <p className="text-dark-400 text-sm">
              No searches yet. Go to the Search page to start scraping leads.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-dark-700">
            {recentSearches.map((search, index) => (
              <div
                key={index}
                className="px-6 py-4 flex items-center justify-between hover:bg-dark-900/50 transition-colors"
              >
                <div>
                  <p className="text-dark-100 font-medium">{search.search_query}</p>
                  <p className="text-dark-400 text-xs mt-0.5">
                    {search.lead_count} lead{search.lead_count !== 1 ? "s" : ""} found
                  </p>
                </div>
                <Link
                  href={`/results?query=${encodeURIComponent(search.search_query)}`}
                  className="text-accent-400 hover:text-accent-300 text-sm font-medium"
                >
                  View Results
                </Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
