import type { Metadata } from "next";
import localFont from "next/font/local";
import Link from "next/link";
import "./globals.css";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "LeadScraper - Find Businesses Without Websites",
  description:
    "Scrape Google Maps to find local businesses without websites and offer your web development services.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-dark-900 text-dark-100 min-h-screen`}
      >
        <nav className="border-b border-dark-700 bg-dark-950/80 backdrop-blur-sm sticky top-0 z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center justify-between h-16">
              <div className="flex items-center gap-2">
                <span className="text-accent-400 font-bold text-xl font-[family-name:var(--font-geist-sans)]">
                  LeadScraper
                </span>
              </div>
              <div className="flex items-center space-x-1">
                <Link
                  href="/search"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-dark-200 hover:text-white hover:bg-dark-800 transition-colors"
                >
                  Search
                </Link>
                <Link
                  href="/results"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-dark-200 hover:text-white hover:bg-dark-800 transition-colors"
                >
                  Results
                </Link>
                <Link
                  href="/dashboard"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-dark-200 hover:text-white hover:bg-dark-800 transition-colors"
                >
                  Dashboard
                </Link>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
