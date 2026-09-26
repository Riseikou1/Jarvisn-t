"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { primaryNav, siteConfig } from "../content/site";

export function Nav(){
  const path=usePathname();
  const [theme, setTheme] = useState<"dark" | "light">("dark");

  useEffect(() => {
    const activeTheme = document.documentElement.dataset.theme === "light" ? "light" : "dark";
    setTheme(activeTheme);
  }, []);

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = nextTheme;
    document.documentElement.style.colorScheme = nextTheme;
    window.localStorage.setItem("jarvisnt-theme", nextTheme);
    setTheme(nextTheme);
  }
  const isActive = (href: string) => path === href || (href === "/chat" && path === "/");
  const navLinks = <>
      {primaryNav.map(({href,label}) =>
        <Link className={isActive(href) ? "active" : ""} aria-current={isActive(href) ? "page" : undefined} href={href} key={href}>{label}</Link>
      )}
  </>;
  return <header className="site-header">
    <Link className="brand" href="/" aria-label={`${siteConfig.name} home`}><img className="brand-logo" src="/icon.png" alt=""/><span>{siteConfig.name}</span></Link>
    <nav className="desktop-nav" aria-label="Primary navigation">{navLinks}</nav>
    <div className="header-actions">
      <span className="status-link"><span/>In development</span>
      <button className="theme-toggle" type="button" role="switch" aria-checked={theme === "dark"} onClick={toggleTheme} aria-label="Dark mode" title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}>
        <span className="theme-thumb" aria-hidden="true">
          <svg className="theme-icon sun" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="3.5"/><path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42"/></svg>
          <svg className="theme-icon moon" viewBox="0 0 24 24" fill="none"><path d="M20.2 15.2A8.5 8.5 0 0 1 8.8 3.8 8.6 8.6 0 1 0 20.2 15.2Z"/><path d="m16.5 4 .45 1.05L18 5.5l-1.05.45L16.5 7l-.45-1.05L15 5.5l1.05-.45L16.5 4Z"/></svg>
        </span>
      </button>
    </div>
    <details className="mobile-menu">
      <summary aria-label="Open navigation">Menu</summary>
      <nav aria-label="Mobile navigation">{navLinks}</nav>
    </details>
  </header>
}
