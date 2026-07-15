"use client";

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

interface LeadCardProps {
  lead: Lead;
}

export default function LeadCard({ lead }: LeadCardProps) {
  const noWebsite = lead.has_website === 0;

  return (
    <div
      className={`bg-dark-800 border border-dark-700 rounded-xl p-5 ${
        noWebsite ? "border-l-4 border-l-danger-500" : ""
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <h3 className="text-lg font-semibold text-dark-100">
          {lead.business_name}
        </h3>
        {noWebsite ? (
          <span className="bg-danger-500 text-white rounded-full px-3 py-1 text-xs font-bold whitespace-nowrap">
            No Website
          </span>
        ) : (
          <span className="bg-success-500 text-white rounded-full px-3 py-1 text-xs font-bold whitespace-nowrap">
            Has Website
          </span>
        )}
      </div>

      <div className="space-y-2">
        {lead.category && (
          <span className="inline-block bg-accent-600/20 text-accent-400 text-xs px-2 py-1 rounded-md font-medium">
            {lead.category}
          </span>
        )}

        {lead.address && (
          <p className="text-dark-300 text-sm flex items-center gap-2">
            <svg
              className="w-4 h-4 text-dark-400 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
              />
            </svg>
            {lead.address}
          </p>
        )}

        {lead.phone && (
          <p className="text-dark-300 text-sm flex items-center gap-2">
            <svg
              className="w-4 h-4 text-dark-400 flex-shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
            <a href={`tel:${lead.phone}`} className="text-accent-400 hover:underline">
              {lead.phone}
            </a>
          </p>
        )}

        <div className="flex items-center gap-3 pt-1">
          {lead.rating !== null && (
            <div className="flex items-center gap-1 text-sm">
              <span className="text-warning-400">&#9733;</span>
              <span className="text-dark-200">{lead.rating}</span>
            </div>
          )}
          {lead.review_count !== null && (
            <span className="text-dark-400 text-sm">
              ({lead.review_count} reviews)
            </span>
          )}
        </div>

        {lead.has_website === 1 && lead.website && (
          <p className="text-sm truncate">
            <a
              href={lead.website}
              target="_blank"
              rel="noopener noreferrer"
              className="text-accent-400 hover:underline"
            >
              {lead.website}
            </a>
          </p>
        )}
      </div>
    </div>
  );
}
