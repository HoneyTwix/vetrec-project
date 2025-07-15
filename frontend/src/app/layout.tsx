import "@/styles/globals.css";

import { type Metadata } from "next";
import { Geist } from "next/font/google";
import { Toaster } from "@/components/ui/sonner";
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/nextjs";

export const metadata: Metadata = {
  title: "VetRec Medical Action Extraction",
  description: "Extract actionable items from medical visit transcripts using AI",
  icons: [{ rel: "icon", url: "/favicon.ico" }],
};

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${geist.variable}`}>
      <body>
        <ClerkProvider>
          <SignedIn>
            <header className="flex justify-end items-center p-4 gap-4 h-16 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border-b border-slate-800 shadow-sm">
              <UserButton />
            </header>
            {children}
          </SignedIn>
          <SignedOut>
            {children}
          </SignedOut>
          <Toaster />
        </ClerkProvider>
      </body>
    </html>
  );
}
