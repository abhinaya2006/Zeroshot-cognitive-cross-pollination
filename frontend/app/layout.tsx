import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Zero-Shot Cognitive Cross-Pollination",
  description: "A Structure-Mapping Approach to Serendipitous Discovery",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-darkBg text-slate-100 selection:bg-purple-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
