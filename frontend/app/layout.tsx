import type { Metadata } from "next";
import { IBM_Plex_Mono, Public_Sans, Space_Grotesk } from "next/font/google";
import "./globals.css";
import NavBar from "@/components/NavBar";
import TodayStrip from "@/components/TodayStrip";
import SentryInit from "@/components/SentryInit";

const body = Public_Sans({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});
const heading = Space_Grotesk({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});
const mono = IBM_Plex_Mono({
  variable: "--font-mono-face",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "PO Delivery Tracker",
  description: "Track purchase-order line delivery status.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="en"
      className={`${body.variable} ${heading.variable} ${mono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-page text-ink">
        <SentryInit />
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-3 focus:z-50 focus:rounded-lg focus:bg-surface focus:px-3 focus:py-2 focus:shadow-card"
        >
          Skip to content
        </a>
        <NavBar />
        <TodayStrip />
        <main id="main" className="flex-1">
          {children}
        </main>
      </body>
    </html>
  );
}
