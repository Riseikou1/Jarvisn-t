import Link from "next/link";
import { siteConfig } from "../content/site";

export default function Home() {
  return (
    <main id="main-content">
      <section className="hero shell">
        <div className="hero-copy">
          <p className="kicker"><span/>Independent language-model project</p>
          <h1><em>{siteConfig.name}</em> is a small language model being built all the way down.</h1>
          <p className="lede">No API wrapper. No mystery benchmark. Just the work of learning how tokenization, pretraining, fine-tuning, evaluation, and inference fit together.</p>
          <div className="actions">
            <Link className="button primary" href="/model">Explore the model <span>↗</span></Link>
            <Link className="button secondary" href="/training">See the training plan</Link>
          </div>
          <p className="honesty-note">The model has not been trained yet. This site documents the build, not imaginary results.</p>
        </div>
        <div className="hero-signal" aria-hidden="true">
          <div className="signal-meta"><span>BUILD / 00</span><span>STATE / UNTRAINED</span></div>
          <div className="signal-orbit orbit-one"/><div className="signal-orbit orbit-two"/>
          <div className="signal-core">J<span>?</span></div>
          <div className="signal-label label-a">TOKEN</div><div className="signal-label label-b">WEIGHTS</div>
        </div>
      </section>

      <section className="status-section shell section-rule" aria-labelledby="status-title">
        <div className="section-intro">
          <p className="kicker">Current state</p>
          <h2 id="status-title">Progress, without theatre.</h2>
          <p>Infrastructure is taking shape. Training claims can wait until training actually happens.</p>
        </div>
        <div className="status-grid">
          {siteConfig.status.map((item, index) => (
            <article className={`status-card ${item.tone}`} key={item.label}>
              <span className="index">0{index + 1}</span>
              <div><h3>{item.label}</h3><p>{item.state}</p></div>
              <i aria-hidden="true"/>
            </article>
          ))}
        </div>
      </section>

      <section className="purpose shell section-rule">
        <div className="section-intro">
          <p className="kicker">Why build it?</p>
          <h2>Understanding the stack means touching the stack.</h2>
        </div>
        <div className="purpose-copy">
          <p>Jarvisn't exists to explore how modern language models are actually assembled: the tokenizer, the data pipeline, the Transformer, the training loop, the evaluations, and the inference runtime.</p>
          <p>It is a technical and educational project by {siteConfig.creator}, built for learning in public and keeping the code small enough to reason about.</p>
          <Link className="arrow-link" href="/about">Why the project exists <span>→</span></Link>
        </div>
      </section>

      <section className="technical shell section-rule" aria-labelledby="technical-title">
        <div className="section-heading-row">
          <div><p className="kicker">Technical overview</p><h2 id="technical-title">Concrete defaults. Flexible scale.</h2></div>
          <Link className="arrow-link" href="/model">Full model notes <span>→</span></Link>
        </div>
        <div className="fact-grid">
          <article><span>01 / TOKENIZER</span><strong>{siteConfig.model.vocabulary}</strong><p>RustBPE vocabulary with explicit chat special tokens.</p></article>
          <article><span>02 / CONTEXT</span><strong>{siteConfig.model.context}</strong><p>Configurable by run; not a deployed-model promise.</p></article>
          <article><span>03 / CORE</span><strong>{siteConfig.model.architecture}</strong><p>RoPE, RMSNorm, QK norm, GQA support, and KV caching.</p></article>
          <article><span>04 / RUNTIME</span><strong>{siteConfig.model.framework}</strong><p>Distributed training paths and hardware-aware attention fallbacks.</p></article>
        </div>
      </section>

      <section className="source-callout shell section-rule">
        <div><p className="kicker">Open foundations</p><h2>Its own project. An acknowledged lineage.</h2></div>
        <div><p>Jarvisn't is built on Andrej Karpathy's nanochat project. The package and identity are new; the upstream technical contribution is credited plainly.</p><Link className="button secondary" href="/credits">Read the credits</Link></div>
      </section>
    </main>
  );
}
