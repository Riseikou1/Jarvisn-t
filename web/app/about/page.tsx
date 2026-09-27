import Link from "next/link";
import Image from "next/image";
import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.about);

export default function About() {
  return <main id="main-content" className="shell page">
    <header className="page-hero"><p className="kicker">01 / About</p><h1>Learning the whole system, not just the last API call.</h1><p>Jarvisn't is an independent language-model project built and trained by {siteConfig.creator}.</p></header>
    <section className="editorial-split section-rule">
      <div><p className="kicker">The project</p><h2>A practical route through modern language modeling.</h2></div>
      <div className="rich-copy"><p>The project began with a simple question: what changes when you stop treating language models as black boxes and build the pipeline yourself?</p><p>Jarvisn't follows that question from raw text and tokenization through model architecture, pretraining, supervised fine-tuning, evaluation, and inference. The goal is technical understanding, expressed in code that can still fit in one person's head.</p><p>The model has now been trained, and its checkpoints are available. It is a small experimental model built to beat GPT-2, so its responses can still be unreliable and prone to hallucinations.</p></div>
    </section>
    <section className="creator-card section-rule">
      <Link className="creator-mark" href="/contact" aria-label={`Contact ${siteConfig.creator}`}><Image src="/creator-portrait.png" alt={`${siteConfig.creator}`} width={600} height={600} /></Link>
      <div><p className="kicker">Creator</p><h2>{siteConfig.creator}</h2><p>{siteConfig.creatorBio}</p><Link className="arrow-link" href="/contact">Contact and project links <span>→</span></Link></div>
    </section>
    <section className="principle-grid section-rule">
      <article><span>01</span><h3>Readable</h3><p>The system should remain small enough to inspect, change, and explain.</p></article>
      <article><span>02</span><h3>Grounded</h3><p>Status and claims come from the repository, not aspirational marketing.</p></article>
      <article><span>03</span><h3>Curious</h3><p>The point is to understand each stage by building and testing it directly.</p></article>
    </section>
  </main>;
}
