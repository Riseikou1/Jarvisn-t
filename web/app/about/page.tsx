import Link from "next/link";
import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.about);

export default function About() {
  return <main id="main-content" className="shell page">
    <header className="page-hero"><p className="kicker">01 / About</p><h1>Learning the whole system, not just the last API call.</h1><p>Jarvisn't is an independent small language-model project in development by {siteConfig.creator}.</p></header>
    <section className="editorial-split section-rule">
      <div><p className="kicker">The project</p><h2>A practical route through modern language modeling.</h2></div>
      <div className="rich-copy"><p>The project began with a simple question: what changes when you stop treating language models as black boxes and build the pipeline yourself?</p><p>Jarvisn't follows that question from raw text and tokenization through model architecture, pretraining, supervised fine-tuning, evaluation, and eventual inference. The goal is technical understanding, expressed in code that can still fit in one person's head.</p><p>The current phase is infrastructure and dataset preparation. No Jarvisn't checkpoint has been trained, and no capabilities or benchmarks are being claimed.</p></div>
    </section>
    <section className="creator-card section-rule">
      <div className="creator-mark" aria-hidden="true">T</div>
      <div><p className="kicker">Creator</p><h2>{siteConfig.creator}</h2><p>{siteConfig.creatorBio}</p><Link className="arrow-link" href="/contact">Contact and project links <span>→</span></Link></div>
    </section>
    <section className="principle-grid section-rule">
      <article><span>01</span><h3>Readable</h3><p>The system should remain small enough to inspect, change, and explain.</p></article>
      <article><span>02</span><h3>Grounded</h3><p>Status and claims come from the repository, not aspirational marketing.</p></article>
      <article><span>03</span><h3>Curious</h3><p>The point is to understand each stage by building and testing it directly.</p></article>
    </section>
  </main>;
}
