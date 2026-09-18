import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.contact);

export default function Contact() {
  return <main id="main-content" className="shell page contact-page">
    <header className="page-hero"><p className="kicker">04 / Contact</p><h1>Questions, bugs, collaboration, or technical discussion.</h1><p>Jarvisn't is an independent project by {siteConfig.creator}.</p></header>
    <section className="contact-card section-rule">
      <div><div className="creator-mark" aria-hidden="true">T</div><p className="kicker">Project contact</p><h2>{siteConfig.creator}</h2><p>{siteConfig.creatorBio}</p></div>
      <dl>
        <div><dt>Email</dt><dd>{siteConfig.email ? <a href={`mailto:${siteConfig.email}`}>{siteConfig.email}</a> : <span>Not publicly configured</span>}</dd></div>
        <div><dt>GitHub</dt><dd>{siteConfig.github ? <a href={siteConfig.github}>Project repository ↗</a> : <span>Repository link not yet configured</span>}</dd></div>
        <div><dt>Best for</dt><dd>Project questions, bug reports, collaboration, and technical discussion.</dd></div>
      </dl>
    </section>
    <p className="page-footnote">Contact values are intentionally centralized in <code>web/content/site.ts</code>. No email address or social profile has been invented for this page.</p>
  </main>;
}
