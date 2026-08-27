import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
    title: "SpeakerSense AI",
    description: "Real-time AI speaking coach",
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
