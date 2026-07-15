import { NextRequest, NextResponse } from "next/server";
import {
  getLeads,
  getLeadsByQuery,
  getLeadsWithoutWebsites,
} from "@/lib/database";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get("query");
    const noWebsite = searchParams.get("no_website");

    let leads;

    if (noWebsite === "true") {
      leads = getLeadsWithoutWebsites();
    } else if (query) {
      leads = getLeadsByQuery(query);
    } else {
      leads = getLeads();
    }

    return NextResponse.json({
      success: true,
      leads,
      count: leads.length,
    });
  } catch (error) {
    console.error("Error fetching leads:", error);
    return NextResponse.json(
      { success: false, error: "Failed to fetch leads" },
      { status: 500 }
    );
  }
}
