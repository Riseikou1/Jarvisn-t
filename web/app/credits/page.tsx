import { createPageMetadata, pageMeta } from "../../content/site";

export const metadata = createPageMetadata(pageMeta.credits);

export default function Credits() {
  return <main id="main-content" className="shell page">
    <header className="page-hero"><p className="kicker">05 / Credits</p><h1>A new identity, with its technical roots left visible.</h1><p>Jarvisn't is Temuujin's project. It also stands on thoughtful open-source work that deserves direct credit.</p></header>
    <section className="credit-feature section-rule"><div><p className="kicker">Technical foundation</p><h2>nanochat</h2></div><div><p>Jarvisn't is built on top of nanochat, an open-source language-model training project by Andrej Karpathy. Its compact end-to-end training stack remains the technical foundation of this repository.</p><a className="button secondary" href="https://github.com/karpathy/nanochat">Visit upstream repository ↗</a></div></section>
    <section className="credit-feature section-rule"><div><p className="kicker">Ideas and experimentation</p><h2>modded-nanogpt</h2></div><div><p>I also looked at modded-nanogpt for ideas and inspiration while building Jarvisn't, especially around efficient model training and optimization.</p><a className="button secondary" href="https://github.com/KellerJordan/modded-nanogpt" target="_blank" rel="noopener noreferrer">Explore modded-nanogpt ↗</a></div></section>
    <section className="credit-list section-rule">
      <article><span>01</span><div><h2>PyTorch</h2><p>Tensor operations, model definition, optimization, and distributed execution. See the <a href="https://docs.pytorch.org/docs/stable/" target="_blank" rel="noopener noreferrer">official PyTorch documentation ↗</a>.</p></div></article>
      <article><span>02</span><div><h2>RustBPE</h2><p>The tokenizer implementation used by the training pipeline.</p></div></article>
      <article><span>03</span><div><h2>FlashAttention</h2><p>Hardware-aware attention acceleration, with a PyTorch SDPA fallback.</p></div></article>
      <article><span>04</span><div><h2>Next.js</h2><p>The framework behind this documentation website.</p></div></article>
      <article><span>05</span><div><h2>RunPod</h2><p>Serverless infrastructure hosting CPU inference for the chat service. The worker loads the trained model checkpoint on demand, so the service can scale down when idle.</p><a href="https://www.runpod.io/serverless-gpu" target="_blank" rel="noopener noreferrer">RunPod Serverless ↗</a></div></article>
    </section>
    <p className="page-footnote">Implementation citations, dataset-source URLs, and historical comments remain in the code where they provide useful provenance.</p>
  </main>;
}
