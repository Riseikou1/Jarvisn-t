import Link from "next/link";
import { primaryNav, siteConfig } from "../content/site";

export function Footer() {
  return (
    <footer className="site-footer">
      <div className="footer-brand">
        <Link href="/">{siteConfig.name}</Link>
        <p>Built by {siteConfig.creator}. Still untrained. Intentionally honest.</p>
      </div>
      <nav aria-label="Footer navigation">
        {primaryNav.map((item) => (
          <Link href={item.href} key={item.href}>{item.label}</Link>
        ))}
        {siteConfig.github && <a href={siteConfig.github}>GitHub</a>}
      </nav>
      <p className="footer-note">Built on nanochat. See Credits for attribution.</p>
    </footer>
  );
}
