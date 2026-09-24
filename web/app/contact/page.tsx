import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.contact);

export default function Contact() {
  return <main id="main-content" className="shell page contact-page">
    <div className="contact-layout">
      <div className="contact-left">
        <div className="contact-intro"><p className="kicker">Contact</p><h1>Let&apos;s talk language models.</h1><p className="lede">Questions, thoughtful feedback, and conversations about Jarvis&apos;nt are welcome.</p></div>
        <div className="contact-links">
          <a className="contact-item" href={`mailto:${siteConfig.email}`}><div className="contact-item-top"><span className="contact-label">Email</span><span className="contact-arrow">↗</span></div><strong>{siteConfig.email}</strong></a>
          <a className="contact-item" href={`tel:${siteConfig.phone}`}><div className="contact-item-top"><span className="contact-label">Phone</span><span className="contact-arrow">↗</span></div><strong>+82 10-8089-3208</strong></a>
          <a className="contact-item" href={siteConfig.portfolio} target="_blank" rel="noopener noreferrer"><div className="contact-item-top"><span className="contact-label">Portfolio</span><span className="contact-arrow">↗</span></div><strong>Selected work</strong></a>
          <a className="contact-item" href={siteConfig.linkedin} target="_blank" rel="noopener noreferrer"><div className="contact-item-top"><span className="contact-label">LinkedIn</span><span className="contact-arrow">↗</span></div><strong>Temuujin Gerelt-Och</strong></a>
          <a className="contact-item" href={siteConfig.github} target="_blank" rel="noopener noreferrer"><div className="contact-item-top"><span className="contact-label">GitHub</span><span className="contact-arrow">↗</span></div><strong>Riseikou1</strong></a>
        </div>
      </div>
      <section className="contact-resume" aria-labelledby="resume-title">
        <div className="contact-resume-heading"><div><p className="kicker">Resume</p><h2 id="resume-title">Temuujin Gerelt-Och</h2></div><span>PDF · A4</span></div>
        <a className="resume-preview" href={siteConfig.resume} target="_blank" rel="noopener noreferrer"><img src="/resume-preview.png" alt="Preview of Temuujin Gerelt-Och&apos;s resume"/><span className="resume-preview-hint">Open full resume ↗</span></a>
        <div className="contact-resume-actions"><a className="button secondary" href={siteConfig.resume} download="temuujin_resume.pdf">Download resume</a><span>Updated 2026</span></div>
      </section>
    </div>
  </main>;
}
