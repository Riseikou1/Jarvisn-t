import { createPageMetadata, pageMeta, siteConfig } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.model);

export default function ModelPage() {
  const facts = [
    ["Architecture", siteConfig.model.architecture, "Autoregressive causal language modeling in PyTorch."],
    ["Vocabulary", siteConfig.model.vocabulary, "A RustBPE tokenizer trained separately from the model."],
    ["Context", siteConfig.model.context, "The training script can override this for each run."],
    ["Scale", "Configured per run", "Depth drives width and attention-head configuration."],
    ["Checkpoint", "None yet", "Pretraining has not started; there is no released model."],
    ["Benchmarks", "Pending", "Evaluation begins only after a real checkpoint exists."],
  ];
  return <main id="main-content" className="shell page">
    <header className="page-hero"><p className="kicker">02 / Model</p><h1>A compact Transformer with no imaginary checkpoint.</h1><p>The architecture is implemented and configurable. The weights are not trained yet.</p></header>
    <section className="model-facts section-rule" aria-label="Model facts">
      {facts.map(([label, value, detail], index) => <article key={label}><span>0{index + 1} / {label}</span><strong>{value}</strong><p>{detail}</p></article>)}
    </section>
    <section className="editorial-split section-rule">
      <div><p className="kicker">Inside the stack</p><h2>Modern pieces, kept legible.</h2></div>
      <ul className="feature-list">{siteConfig.technicalFeatures.map((feature, index) => <li key={feature}><span>0{index + 1}</span>{feature}</li>)}</ul>
    </section>
    <aside className="truth-panel"><span className="status-dot"/> <div><strong>Training status</strong><p>Jarvisn't has not been pretrained or fine-tuned. Parameter totals, quality claims, and benchmark results will belong here only after a concrete run is selected and completed.</p></div></aside>
  </main>;
}
