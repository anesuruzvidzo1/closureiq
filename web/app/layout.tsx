import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ClosureIQ · Alberta closure planning from public data",
  description:
    "ClosureIQ ranks Alberta operators' inactive wells and builds the lowest cost closure plan to meet Directive 088 quotas, from public AER data.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
