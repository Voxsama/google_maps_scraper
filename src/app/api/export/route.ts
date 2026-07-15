import { NextResponse } from "next/server";
import { exportLeadsCSV } from "@/lib/database";

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const noWebsite = searchParams.get("no_website") === "true";
    const query = searchParams.get("query") || undefined;

    const csv = exportLeadsCSV({ noWebsite, query });

    if (!csv) {
      return new Response("No leads to export", {
        status: 200,
        headers: {
          "Content-Type": "text/plain",
        },
      });
    }

    return new Response(csv, {
      status: 200,
      headers: {
        "Content-Type": "text/csv",
        "Content-Disposition": 'attachment; filename="leads-export.csv"',
      },
    });
  } catch (error) {
    console.error("Error exporting leads:", error);
    return NextResponse.json(
      { success: false, error: "Failed to export leads" },
      { status: 500 }
    );
  }
}
