import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "leads.db");

// Use globalThis to survive Next.js hot module replacement in development
const globalForDb = globalThis as unknown as { __leadsDb: Database.Database | undefined };

function getDb(): Database.Database {
  if (!globalForDb.__leadsDb) {
    const db = new Database(DB_PATH);
    db.pragma("journal_mode = WAL");
    db.exec(`
      CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        business_name TEXT,
        address TEXT,
        phone TEXT,
        category TEXT,
        rating REAL,
        review_count INTEGER,
        website TEXT,
        has_website INTEGER DEFAULT 0,
        search_query TEXT,
        scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(business_name, address, search_query)
      )
    `);
    globalForDb.__leadsDb = db;
  }
  return globalForDb.__leadsDb;
}

export interface Lead {
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

export interface LeadStats {
  total_leads: number;
  leads_without_websites: number;
  leads_with_websites: number;
  unique_queries: number;
}

export function insertLead(lead: Omit<Lead, "id" | "scraped_at">): void {
  const database = getDb();
  const stmt = database.prepare(`
    INSERT INTO leads (business_name, address, phone, category, rating, review_count, website, has_website, search_query)
    VALUES (@business_name, @address, @phone, @category, @rating, @review_count, @website, @has_website, @search_query)
    ON CONFLICT(business_name, address, search_query) DO UPDATE SET
      phone = excluded.phone,
      category = excluded.category,
      rating = excluded.rating,
      review_count = excluded.review_count,
      website = excluded.website,
      has_website = excluded.has_website,
      scraped_at = CURRENT_TIMESTAMP
  `);
  stmt.run(lead);
}

export function getLeads(options?: { noWebsite?: boolean; query?: string }): Lead[] {
  const database = getDb();
  const conditions: string[] = [];
  const params: Record<string, string | number> = {};

  if (options?.noWebsite) {
    conditions.push("has_website = 0");
  }
  if (options?.query) {
    conditions.push("search_query = @query");
    params.query = options.query;
  }

  const whereClause = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
  const stmt = database.prepare(`SELECT * FROM leads ${whereClause} ORDER BY scraped_at DESC`);
  return stmt.all(params) as Lead[];
}

export function getLeadsByQuery(query: string): Lead[] {
  const database = getDb();
  const stmt = database.prepare(
    "SELECT * FROM leads WHERE search_query = ? ORDER BY scraped_at DESC"
  );
  return stmt.all(query) as Lead[];
}

export function getLeadsWithoutWebsites(): Lead[] {
  const database = getDb();
  const stmt = database.prepare(
    "SELECT * FROM leads WHERE has_website = 0 ORDER BY scraped_at DESC"
  );
  return stmt.all() as Lead[];
}

export function getStats(): LeadStats {
  const database = getDb();
  const total = database
    .prepare("SELECT COUNT(*) as count FROM leads")
    .get() as { count: number };
  const withoutWebsites = database
    .prepare("SELECT COUNT(*) as count FROM leads WHERE has_website = 0")
    .get() as { count: number };
  const withWebsites = database
    .prepare("SELECT COUNT(*) as count FROM leads WHERE has_website = 1")
    .get() as { count: number };
  const uniqueQueries = database
    .prepare("SELECT COUNT(DISTINCT search_query) as count FROM leads")
    .get() as { count: number };

  return {
    total_leads: total.count,
    leads_without_websites: withoutWebsites.count,
    leads_with_websites: withWebsites.count,
    unique_queries: uniqueQueries.count,
  };
}

export interface RecentSearch {
  search_query: string;
  last_scraped: string;
  lead_count: number;
}

export function getRecentSearches(): RecentSearch[] {
  const database = getDb();
  const stmt = database.prepare(`
    SELECT DISTINCT search_query, MAX(scraped_at) as last_scraped, COUNT(*) as lead_count
    FROM leads
    GROUP BY search_query
    ORDER BY last_scraped DESC
    LIMIT 10
  `);
  return stmt.all() as RecentSearch[];
}

export function exportLeadsCSV(options?: { noWebsite?: boolean; query?: string }): string {
  const leads = getLeads(options);
  if (leads.length === 0) return "";

  const headers = [
    "ID",
    "Business Name",
    "Address",
    "Phone",
    "Category",
    "Rating",
    "Review Count",
    "Website",
    "Has Website",
    "Search Query",
    "Scraped At",
  ];

  const rows = leads.map((lead) => [
    lead.id,
    `"${(lead.business_name || "").replace(/"/g, '""')}"`,
    `"${(lead.address || "").replace(/"/g, '""')}"`,
    `"${(lead.phone || "").replace(/"/g, '""')}"`,
    `"${(lead.category || "").replace(/"/g, '""')}"`,
    lead.rating ?? "",
    lead.review_count ?? "",
    `"${(lead.website || "").replace(/"/g, '""')}"`,
    lead.has_website ? "Yes" : "No",
    `"${(lead.search_query || "").replace(/"/g, '""')}"`,
    lead.scraped_at || "",
  ]);

  return [headers.join(","), ...rows.map((row) => row.join(","))].join("\n");
}
