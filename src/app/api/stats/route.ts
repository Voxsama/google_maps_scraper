import { NextResponse } from "next/server";
import { getStats, getRecentSearches } from "@/lib/database";

export async function GET() {
  try {
    const stats = getStats();
    const recent_searches = getRecentSearches();

    return NextResponse.json({
      success: true,
      stats,
      recent_searches,
    });
  } catch (error) {
    console.error("Error fetching stats:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch stats" },
      { status: 500 }
    );
  }
}
