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

interface LeadTableProps {
  leads: Lead[];
}

export default function LeadTable({ leads }: LeadTableProps) {
  return (
    <div className="overflow-x-auto rounded-xl border border-dark-700">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-dark-950 text-dark-300 uppercase text-xs">
            <th className="text-left px-4 py-3 font-medium">Business Name</th>
            <th className="text-left px-4 py-3 font-medium">Category</th>
            <th className="text-left px-4 py-3 font-medium">Address</th>
            <th className="text-left px-4 py-3 font-medium">Phone</th>
            <th className="text-left px-4 py-3 font-medium">Rating</th>
            <th className="text-left px-4 py-3 font-medium">Reviews</th>
            <th className="text-left px-4 py-3 font-medium">Website Status</th>
          </tr>
        </thead>
        <tbody>
          {leads.map((lead, index) => {
            const noWebsite = lead.has_website === 0;
            const rowBg = noWebsite
              ? "bg-danger-500/10"
              : index % 2 === 0
              ? "bg-dark-800"
              : "bg-dark-900";

            return (
              <tr
                key={lead.id ?? index}
                className={`${rowBg} border-t border-dark-700`}
              >
                <td className="px-4 py-3 text-dark-100 font-medium">
                  {lead.business_name}
                </td>
                <td className="px-4 py-3">
                  {lead.category && (
                    <span className="inline-block bg-accent-600/20 text-accent-400 text-xs px-2 py-0.5 rounded-md">
                      {lead.category}
                    </span>
                  )}
                </td>
                <td className="px-4 py-3 text-dark-300 max-w-[200px] truncate">
                  {lead.address}
                </td>
                <td className="px-4 py-3">
                  {lead.phone ? (
                    <a
                      href={`tel:${lead.phone}`}
                      className="text-accent-400 hover:underline"
                    >
                      {lead.phone}
                    </a>
                  ) : (
                    <span className="text-dark-500">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-dark-200">
                  {lead.rating !== null ? (
                    <span className="flex items-center gap-1">
                      <span className="text-warning-400">&#9733;</span>
                      {lead.rating}
                    </span>
                  ) : (
                    <span className="text-dark-500">-</span>
                  )}
                </td>
                <td className="px-4 py-3 text-dark-300">
                  {lead.review_count ?? "-"}
                </td>
                <td className="px-4 py-3">
                  {noWebsite ? (
                    <span className="bg-danger-500 text-white rounded-full px-3 py-1 text-xs font-bold">
                      No Website
                    </span>
                  ) : (
                    <span className="bg-success-500 text-white rounded-full px-3 py-1 text-xs font-bold">
                      Has Website
                    </span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
