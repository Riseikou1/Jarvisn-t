export const siteConfig = {
  name: "Jarvisn't",
  creator: "Temuujin",
  description:
    "A small language model being built from the ground up, from tokenizer to training and evaluation.",
  tagline: "Small model. Full stack. Still learning.",
  github: null as string | null,
  email: null as string | null,
  creatorBio:
    "I'm Temuujin, a university student focused on artificial intelligence and software engineering. I built Jarvisn't to learn what it actually takes to build and train a language model rather than treating modern AI as a black box.",
  status: [
    { label: "Tokenizer", state: "Tooling ready", tone: "ready" },
    { label: "Pretraining", state: "Not started", tone: "pending" },
    { label: "SFT", state: "Dataset prepared", tone: "progress" },
    { label: "Evaluation", state: "Pending", tone: "pending" },
  ],
  model: {
    vocabulary: "32,768 tokens",
    context: "2,048 tokens by default",
    architecture: "Decoder-only Transformer",
    framework: "PyTorch",
  },
  technicalFeatures: [
    "Rotary position embeddings",
    "RMSNorm and QK normalization",
    "Grouped-query attention support",
    "ReLU-squared MLPs",
    "Sliding-window attention",
    "Flash Attention 3 with SDPA fallback",
  ],
  pipeline: [
    { step: "01", name: "Dataset", detail: "Prepare and stream ClimbMix parquet shards.", status: "Tooling ready" },
    { step: "02", name: "Tokenizer", detail: "Train and inspect a 32,768-token RustBPE vocabulary.", status: "Tooling ready" },
    { step: "03", name: "Pretraining", detail: "Train the decoder-only base model and save checkpoints.", status: "Not started" },
    { step: "04", name: "Evaluation", detail: "Measure bits per byte, CORE tasks, and generation behavior.", status: "Pending" },
    { step: "05", name: "SFT", detail: "Fine-tune for instruction following after a base checkpoint exists.", status: "Dataset prepared" },
  ],
} as const;

export const pageMeta = {
  about: {
    title: "About",
    description: "What Jarvisn't is, why it exists, and who is building it.",
  },
  model: {
    title: "Model",
    description: "The current Jarvisn't architecture, tokenizer defaults, and checkpoint status.",
  },
  training: {
    title: "Training",
    description: "The intended Jarvisn't tokenizer, pretraining, evaluation, and SFT pipeline.",
  },
  contact: {
    title: "Contact",
    description: "Contact information and project links for Jarvisn't and its creator, Temuujin.",
  },
  credits: {
    title: "Credits",
    description: "Upstream attribution and important open-source dependencies behind Jarvisn't.",
  },
} as const;

export function createPageMetadata(meta: (typeof pageMeta)[keyof typeof pageMeta]) {
  const title = `${meta.title} — ${siteConfig.name}`;
  return {
    title: meta.title,
    description: meta.description,
    openGraph: {
      title,
      description: meta.description,
      images: [],
    },
    twitter: {
      title,
      description: meta.description,
      images: [],
    },
  };
}

export const primaryNav = [
  { href: "/chat", label: "Chat" },
  { href: "/about", label: "About" },
  { href: "/model", label: "Model" },
  { href: "/training", label: "Training" },
  { href: "/contact", label: "Contact" },
  { href: "/credits", label: "Credits" },
] as const;
