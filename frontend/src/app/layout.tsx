import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI Red Team Security Validation",
  description: "AI Red Team-Driven Security Validation for Blue-Green Deployment",
};

import { Sidebar } from "@/components/Sidebar";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-row">
        <Sidebar />
        <main className="flex-1 min-h-screen max-w-6xl py-12 px-12 md:px-24">
          {children}
        </main>
      </body>
    </html>
  );
}
