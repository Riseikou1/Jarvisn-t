export const siteConfig = {
  name: "Jarvisn't",
  creator: "Temuujin",
  description:
    "Chat with Jarvisn't, an independent experimental language model trained from scratch.",
  tagline: "A small model, learning in public.",
  github: "https://github.com/Riseikou1",
  email: "temka4705@gmail.com",
  phone: "+821080893208",
  portfolio: "https://portfolio-quinx.vercel.app",
  linkedin: "https://www.linkedin.com/in/temuujin-gerelt-och/",
  resume: "/temuujin_resume.pdf",
  creatorBio:
    "I'm Temuujin, a university student focused on artificial intelligence and software engineering. I built Jarvisn't to learn what it actually takes to build and train a language model rather than treating modern AI as a black box.",
  status: [
    { label: "Tokenizer", state: "Tooling ready", tone: "ready" },
    { label: "Pretraining", state: "Complete · checkpoints available", tone: "ready" },
    { label: "SFT", state: "Dataset prepared", tone: "progress" },
    { label: "Evaluation", state: "Pending", tone: "pending" },
  ],
  technicalFeatures: [
    "Rotary position embeddings",
    "RMSNorm and QK normalization",
    "Grouped-query attention support",
    "ReLU-squared MLPs",
    "Sliding-window attention",
    "Flash Attention 3 with SDPA fallback",
  ],
  technicalOverview: {
    vocabulary: "32,768 tokens",
    context: "2,048 tokens",
    architecture: "Decoder-only Transformer",
    framework: "PyTorch",
  },
} as const;

export const pageMeta = {
  about: {
    title: "About",
    description: "What Jarvisn't is, why it exists, and who is building it.",
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
  { href: "/contact", label: "Contact" },
  { href: "/credits", label: "Credits" },
] as const;
