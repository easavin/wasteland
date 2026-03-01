import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Wasteland Chronicles Admin",
  description: "Admin dashboard for the Wasteland Chronicles Telegram game",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="antialiased min-h-screen bg-[#0a0a0a] text-neutral-200">
        {children}
      </body>
    </html>
  );
}
