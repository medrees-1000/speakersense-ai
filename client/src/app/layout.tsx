import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PostureSense AI",
  description: "Real-time AI posture coach with spoken alerts and exercise reports",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
