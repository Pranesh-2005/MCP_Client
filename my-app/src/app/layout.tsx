import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import "@copilotkit/react-ui/styles.css";
import React from "react";
import { CopilotKit } from "@copilotkit/react-core";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Weather & GitHub Assistant",
  description: "AI assistant with weather and GitHub data access",
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/android-icon-36x36.png", sizes: "36x36", type: "image/png" },
      { url: "/android-icon-48x48.png", sizes: "48x48", type: "image/png" },
      { url: "/android-icon-72x72.png", sizes: "72x72", type: "image/png" },
      { url: "/android-icon-96x96.png", sizes: "96x96", type: "image/png" },
      { url: "/android-icon-144x144.png", sizes: "144x144", type: "image/png" },
      { url: "/android-icon-192x192.png", sizes: "192x192", type: "image/png" },
      { url: "/android-icon-512x512.png", sizes: "512x512", type: "image/png" },
    ],
    apple: [
      { url: "/android-icon-192x192.png", sizes: "192x192", type: "image/png" },
    ],
    shortcut: "/android-icon-48x48.png",
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#6366f1',
  colorScheme: 'light',
};

const runtimeUrl = process.env.NEXT_PUBLIC_COPILOTKIT_RUNTIME_URL
const publicApiKey = process.env.NEXT_PUBLIC_COPILOT_API_KEY;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <CopilotKit
          runtimeUrl={runtimeUrl}
          publicApiKey={publicApiKey}
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}