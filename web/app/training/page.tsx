import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.training);

export default function TrainingPage() {
  return <main id="main-content" className="shell page">
    <header className="page-hero"><p className="kicker">03 / Training</p><h1>From parquet shards to a model you can actually evaluate.</h1><p>The pipeline is implemented in stages. Expensive compute starts only when the inputs and configuration are ready.</p></header>
    <section className="pipeline section-rule">
      {siteConfig.pipeline.map((item) => <article key={item.step}><span className="pipeline-step">{item.step}</span><div><h2>{item.name}</h2><p>{item.detail}</p></div><span className="pipeline-status">{item.status}</span></article>)}
    </section>
    <section className="doc-grid section-rule">
      <article><p className="kicker">Data and tokenizer</p><h2>Prepare before spending compute.</h2><p>Dataset utilities stream ClimbMix parquet shards. The tokenizer pipeline trains a 32,768-token RustBPE vocabulary and checks round-trip encoding before saving artifacts.</p><code>python -m scripts.tok_train</code></article>
      <article><p className="kicker">Base model</p><h2>Depth is the main scale dial.</h2><p>The pretraining script derives model width and head counts from the selected depth, supports distributed execution, and records checkpoint metadata for later evaluation.</p><code>python -m scripts.base_train --help</code></article>
      <article><p className="kicker">SFT and evaluation</p><h2>Behavior follows a base checkpoint.</h2><p>A local 1,320-example bootstrap SFT corpus is prepared. The inherited chat-training pipeline and evaluation tasks remain available, but neither has been run for Jarvisn't.</p><code>python sft_dataset/validate.py …</code></article>
    </section>
    <p className="page-footnote">Commands are documentation, not automated actions on this site. Dataset downloads and training require deliberate local execution.</p>
  </main>;
}
