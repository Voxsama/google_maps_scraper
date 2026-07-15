import { NextResponse } from "next/server";
import { scrapeGoogleMaps } from "@/lib/scraper";
import { insertLead } from "@/lib/database";

export const runtime = "nodejs";
export const maxDuration = 120;

// Simple in-memory concurrency gate to prevent multiple simultaneous scrape requests
const globalForScrape = globalThis as unknown as { __scrapeInProgress: boolean };
if (globalForScrape.__scrapeInProgress === undefined) {
  globalForScrape.__scrapeInProgress = false;
}

export async function POST(request: Request) {
  // Reject concurrent scrape requests
  if (globalForScrape.__scrapeInProgress) {
    return NextResponse.json(
      { success: false, error: "A scrape is already in progress. Please wait and try again." },
      { status: 429 }
    );
  }

  globalForScrape.__scrapeInProgress = true;

  try {
    const body = await request.json();
    const { query } = body;

    if (!query || typeof query !== "string" || !query.trim()) {
      return NextResponse.json(
        { success: false, error: "A non-empty query string is required" },
        { status: 400 }
      );
    }

    const trimmedQuery = query.trim();
    const leads = await scrapeGoogleMaps(trimmedQuery);

    // Store each lead in the database
    for (const lead of leads) {
      insertLead({
        business_name: lead.business_name,
        address: lead.address,
        phone: lead.phone,
        category: lead.category,
        rating: lead.rating,
        review_count: lead.review_count,
        website: lead.website,
        has_website: lead.has_website,
        search_query: trimmedQuery,
      });
    }

    return NextResponse.json({
      success: true,
      leads,
      count: leads.length,
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "An unexpected error occurred";
    return NextResponse.json(
      { success: false, error: message },
      { status: 500 }
    );
  } finally {
    globalForScrape.__scrapeInProgress = false;
  }
}
