import type { Metadata } from "next";
import { Suspense } from "react";
import { Newsreader, Manrope } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const newsreader = Newsreader({
  variable: "--font-newsreader",
  subsets: ["latin"],
  weight: ["300", "400", "500"],
  style: ["normal", "italic"],
  display: "swap",
});

const manrope = Manrope({
  variable: "--font-manrope",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Prisma(x) Discussion",
  description:
    "Exploring the intersection of robotics, ethics, and digital architecture. Peer-reviewed threads from our global community.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${newsreader.variable} ${manrope.variable}`}>
      <body>
        <Providers>
          <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
            <Suspense fallback={null}>
              <Header />
            </Suspense>
            <main style={{ flex: 1 }}>{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
