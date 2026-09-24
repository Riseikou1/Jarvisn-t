import "./globals.css";
import type { Metadata } from "next";
import { headers } from "next/headers";
import { Nav } from "../components/Nav";
import { Footer } from "../components/Footer";
import { siteConfig } from "../content/site";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("host") ?? "localhost:3000";
  const protocol = host.includes("localhost") || host.startsWith("127.") ? "http" : "https";
  const baseUrl = process.env.NEXT_PUBLIC_SITE_URL ?? `${protocol}://${host}`;

  return {
    metadataBase: new URL(baseUrl),
    title: { default: `${siteConfig.name} — ${siteConfig.tagline}`, template: `%s — ${siteConfig.name}` },
    description: siteConfig.description,
    applicationName: siteConfig.name,
    authors: [{ name: siteConfig.creator }],
    keywords: ["Jarvisn't", "small language model", "LLM training", "PyTorch", "nanochat"],
    manifest: "/manifest.webmanifest",
    icons: {
      icon: [
        { url: "/favicon.ico" },
        { url: "/icon.png", type: "image/png" },
      ],
      apple: "/apple-icon.png",
    },
    openGraph: {
      type: "website",
      siteName: siteConfig.name,
      title: `${siteConfig.name} — ${siteConfig.tagline}`,
      description: siteConfig.description,
      images: [{ url: `${baseUrl}/og.png`, width: 1672, height: 941, alt: `${siteConfig.name}: ${siteConfig.tagline}` }],
    },
    twitter: {
      card: "summary_large_image",
      title: `${siteConfig.name} — ${siteConfig.tagline}`,
      description: siteConfig.description,
      images: [`${baseUrl}/og.png`],
    },
  };
}

export default function RootLayout({children}:{children:React.ReactNode}) {
  return <html lang="en" suppressHydrationWarning><head><script dangerouslySetInnerHTML={{__html: `try { const t = localStorage.getItem('jarvisnt-theme') || 'dark'; document.documentElement.dataset.theme = t === 'light' ? 'light' : 'dark'; document.documentElement.style.colorScheme = document.documentElement.dataset.theme; } catch { document.documentElement.dataset.theme = 'dark'; }`}} /></head><body>
    <a className="skip-link" href="#main-content">Skip to content</a>
    <div className="page-grid" aria-hidden="true"/>
    <Nav/>
    {children}
    <Footer/>
  </body></html>
}
