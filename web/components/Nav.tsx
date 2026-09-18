"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { primaryNav, siteConfig } from "../content/site";

export function Nav(){
  const path=usePathname();
  const navLinks = <>
      {primaryNav.map(({href,label}) =>
        <Link className={path===href?"active":""} aria-current={path===href?"page":undefined} href={href} key={href}>{label}</Link>
      )}
  </>;
  return <header className="site-header">
    <Link className="brand" href="/" aria-label={`${siteConfig.name} home`}><i aria-hidden="true">J?</i><span>{siteConfig.name}</span></Link>
    <nav className="desktop-nav" aria-label="Primary navigation">{navLinks}</nav>
    <Link className="status-link" href="/model"><span/>In development</Link>
    <details className="mobile-menu">
      <summary aria-label="Open navigation">Menu</summary>
      <nav aria-label="Mobile navigation">{navLinks}</nav>
    </details>
  </header>
}
