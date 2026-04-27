import type { TranslationKey } from "../i18n";
import type { SeoLocale } from "../utils/publicRoutes";
import { getLocalizedPublicPath } from "../utils/publicRoutes";

export type PublicNavItem = {
  href: string;
  label: TranslationKey;
};

export type MarketingItem = {
  title: TranslationKey;
  description: TranslationKey;
};

export type MarketingMention = {
  source: TranslationKey;
  title: TranslationKey;
  description: TranslationKey;
  href: string;
  publishedAt: string;
};

export type BlogArticle = {
  slug: string;
  index: string;
  category: TranslationKey;
  title: TranslationKey;
  summary: TranslationKey;
  readTime: TranslationKey;
  highlight: TranslationKey;
  audience: TranslationKey;
  thesis: TranslationKey;
  takeawayKeys: TranslationKey[];
  sections: Array<{
    title: TranslationKey;
    body: TranslationKey;
  }>;
  accentClass: string;
};

export const PUBLIC_HOME_NAV: PublicNavItem[] = [
  { href: "/b2b-leads", label: "landing.navLeads" },
  { href: "/seo-geo", label: "landing.navSeoGeo" },
  { href: "/workspace", label: "landing.navOpenSource" },
  { href: "/data-policy", label: "landing.navDataPolicy" },
  { href: "/contact", label: "landing.navContact" },
  { href: "/blog", label: "landing.navBlog" },
];

export const PUBLIC_BLOG_NAV: PublicNavItem[] = [
  { href: "/", label: "blog.homeCta" },
  { href: "/blog", label: "landing.navBlog" },
];

export const LANDING_PLATFORM_ITEMS: MarketingItem[] = [
  {
    title: "landing.platform1Title",
    description: "landing.platform1Desc",
  },
  {
    title: "landing.platform2Title",
    description: "landing.platform2Desc",
  },
  {
    title: "landing.platform3Title",
    description: "landing.platform3Desc",
  },
  {
    title: "landing.platform4Title",
    description: "landing.platform4Desc",
  },
  {
    title: "landing.platform5Title",
    description: "landing.platform5Desc",
  },
];

export const LANDING_LEARNING_LOOP_ITEMS: MarketingItem[] = [
  {
    title: "landing.learningLoop1Title",
    description: "landing.learningLoop1Desc",
  },
  {
    title: "landing.learningLoop2Title",
    description: "landing.learningLoop2Desc",
  },
  {
    title: "landing.learningLoop3Title",
    description: "landing.learningLoop3Desc",
  },
  {
    title: "landing.learningLoop4Title",
    description: "landing.learningLoop4Desc",
  },
];

export const LANDING_WORKFLOW_STEPS: MarketingItem[] = [
  {
    title: "landing.stage1",
    description: "landing.workflow1Desc",
  },
  {
    title: "landing.stage2",
    description: "landing.workflow2Desc",
  },
  {
    title: "landing.stage3",
    description: "landing.workflow3Desc",
  },
  {
    title: "landing.stage4",
    description: "landing.workflow4Desc",
  },
  {
    title: "landing.stage5",
    description: "landing.workflow5Desc",
  },
  {
    title: "landing.stage6",
    description: "landing.workflow6Desc",
  },
];

export const LANDING_FAQS: Array<{ question: TranslationKey; answer: TranslationKey }> = [
  {
    question: "landing.faq1Question",
    answer: "landing.faq1Answer",
  },
  {
    question: "landing.faq2Question",
    answer: "landing.faq2Answer",
  },
  {
    question: "landing.faq3Question",
    answer: "landing.faq3Answer",
  },
];

export const LANDING_CAPABILITY_KEYS: TranslationKey[] = [
  "landing.capabilitySeo",
  "landing.capabilityGeo",
  "landing.capabilityCommunity",
];

export const LANDING_CRAWLER_BULLETS: TranslationKey[] = [
  "landing.crawlerBullet1",
  "landing.crawlerBullet2",
  "landing.crawlerBullet3",
];

export const LANDING_PROOF_ITEMS: MarketingItem[] = [
  {
    title: "landing.proofResearchTitle",
    description: "landing.proofResearchDesc",
  },
  {
    title: "landing.proofCrawlerTitle",
    description: "landing.proofCrawlerDesc",
  },
  {
    title: "landing.proofWorkflowTitle",
    description: "landing.proofWorkflowDesc",
  },
];

export const LANDING_TRUST_ITEMS: MarketingItem[] = [
  {
    title: "landing.trust1Title",
    description: "landing.trust1Desc",
  },
  {
    title: "landing.trust2Title",
    description: "landing.trust2Desc",
  },
  {
    title: "landing.trust3Title",
    description: "landing.trust3Desc",
  },
  {
    title: "landing.trust4Title",
    description: "landing.trust4Desc",
  },
];

export const LANDING_MENTION_ITEMS: MarketingMention[] = [
  {
    source: "landing.mention1Source",
    title: "landing.mention1Title",
    description: "landing.mention1Desc",
    href: "https://x.com/chuanliang/status/2035869753978519764",
    publishedAt: "2026-03-23",
  },
  {
    source: "landing.mention2Source",
    title: "landing.mention2Title",
    description: "landing.mention2Desc",
    href: "https://www.80aj.com/2026/04/05/openai-marketing-tools-update/",
    publishedAt: "2026-04-05",
  },
];

export const BLOG_PRINCIPLES: MarketingItem[] = [
  {
    title: "blog.principle1Title",
    description: "blog.principle1Desc",
  },
  {
    title: "blog.principle2Title",
    description: "blog.principle2Desc",
  },
  {
    title: "blog.principle3Title",
    description: "blog.principle3Desc",
  },
];

export const BLOG_READER_PATHS: MarketingItem[] = [
  {
    title: "blog.reader1Title",
    description: "blog.reader1Desc",
  },
  {
    title: "blog.reader2Title",
    description: "blog.reader2Desc",
  },
  {
    title: "blog.reader3Title",
    description: "blog.reader3Desc",
  },
];

export const BLOG_DECISION_ARTICLE_SLUGS = [
  "opencmo-vs-mautic-posthog",
  "who-should-use-opencmo",
] as const;

export const BLOG_FEATURED_ARTICLE_SLUG = "opencmo-vs-mautic-posthog" as const;

export const BLOG_ARTICLES: BlogArticle[] = [
  {
    slug: "what-is-a-cmo",
    index: "01",
    category: "blog.post7.category",
    title: "blog.post7.title",
    summary: "blog.post7.summary",
    readTime: "blog.post7.readTime",
    highlight: "blog.post7.highlight",
    audience: "blog.post7.audience",
    thesis: "blog.post7.thesis",
    takeawayKeys: ["blog.post7.point1", "blog.post7.point2", "blog.post7.point3"],
    sections: [
      {
        title: "blog.post7.section1Title",
        body: "blog.post7.section1Body",
      },
      {
        title: "blog.post7.section2Title",
        body: "blog.post7.section2Body",
      },
      {
        title: "blog.post7.section3Title",
        body: "blog.post7.section3Body",
      },
      {
        title: "blog.post7.section4Title",
        body: "blog.post7.section4Body",
      },
    ],
    accentClass:
      "from-[#d7c7ff]/22 via-[#f8f1e7] to-[#86c8bc]/18",
  },
  {
    slug: "what-is-product-marketing",
    index: "02",
    category: "blog.post8.category",
    title: "blog.post8.title",
    summary: "blog.post8.summary",
    readTime: "blog.post8.readTime",
    highlight: "blog.post8.highlight",
    audience: "blog.post8.audience",
    thesis: "blog.post8.thesis",
    takeawayKeys: ["blog.post8.point1", "blog.post8.point2", "blog.post8.point3"],
    sections: [
      {
        title: "blog.post8.section1Title",
        body: "blog.post8.section1Body",
      },
      {
        title: "blog.post8.section2Title",
        body: "blog.post8.section2Body",
      },
      {
        title: "blog.post8.section3Title",
        body: "blog.post8.section3Body",
      },
      {
        title: "blog.post8.section4Title",
        body: "blog.post8.section4Body",
      },
    ],
    accentClass:
      "from-[#b9d9ff]/24 via-[#f8f5ee] to-[#cfe8dd]/24",
  },
  {
    slug: "what-is-go-to-market-strategy",
    index: "03",
    category: "blog.post9.category",
    title: "blog.post9.title",
    summary: "blog.post9.summary",
    readTime: "blog.post9.readTime",
    highlight: "blog.post9.highlight",
    audience: "blog.post9.audience",
    thesis: "blog.post9.thesis",
    takeawayKeys: ["blog.post9.point1", "blog.post9.point2", "blog.post9.point3"],
    sections: [
      {
        title: "blog.post9.section1Title",
        body: "blog.post9.section1Body",
      },
      {
        title: "blog.post9.section2Title",
        body: "blog.post9.section2Body",
      },
      {
        title: "blog.post9.section3Title",
        body: "blog.post9.section3Body",
      },
      {
        title: "blog.post9.section4Title",
        body: "blog.post9.section4Body",
      },
    ],
    accentClass:
      "from-[#ffe0b8]/28 via-[#f9f3ea] to-[#dce9f0]",
  },
  {
    slug: "what-is-brand-positioning",
    index: "04",
    category: "blog.post10.category",
    title: "blog.post10.title",
    summary: "blog.post10.summary",
    readTime: "blog.post10.readTime",
    highlight: "blog.post10.highlight",
    audience: "blog.post10.audience",
    thesis: "blog.post10.thesis",
    takeawayKeys: ["blog.post10.point1", "blog.post10.point2", "blog.post10.point3"],
    sections: [
      {
        title: "blog.post10.section1Title",
        body: "blog.post10.section1Body",
      },
      {
        title: "blog.post10.section2Title",
        body: "blog.post10.section2Body",
      },
      {
        title: "blog.post10.section3Title",
        body: "blog.post10.section3Body",
      },
      {
        title: "blog.post10.section4Title",
        body: "blog.post10.section4Body",
      },
    ],
    accentClass:
      "from-[#f3dcc9]/45 via-[#f8efe6] to-[#efe7ff]/32",
  },
  {
    slug: "demand-generation-vs-lead-generation",
    index: "05",
    category: "blog.post11.category",
    title: "blog.post11.title",
    summary: "blog.post11.summary",
    readTime: "blog.post11.readTime",
    highlight: "blog.post11.highlight",
    audience: "blog.post11.audience",
    thesis: "blog.post11.thesis",
    takeawayKeys: ["blog.post11.point1", "blog.post11.point2", "blog.post11.point3"],
    sections: [
      {
        title: "blog.post11.section1Title",
        body: "blog.post11.section1Body",
      },
      {
        title: "blog.post11.section2Title",
        body: "blog.post11.section2Body",
      },
      {
        title: "blog.post11.section3Title",
        body: "blog.post11.section3Body",
      },
      {
        title: "blog.post11.section4Title",
        body: "blog.post11.section4Body",
      },
    ],
    accentClass:
      "from-[#cde7d7]/28 via-[#f5f8ef] to-[#fff0d8]/28",
  },
  {
    slug: "ai-cmo-workspace",
    index: "06",
    category: "blog.post1.category",
    title: "blog.post1.title",
    summary: "blog.post1.summary",
    readTime: "blog.post1.readTime",
    highlight: "blog.post1.highlight",
    audience: "blog.post1.audience",
    thesis: "blog.post1.thesis",
    takeawayKeys: ["blog.post1.point1", "blog.post1.point2", "blog.post1.point3"],
    sections: [
      {
        title: "blog.post1.section1Title",
        body: "blog.post1.section1Body",
      },
      {
        title: "blog.post1.section2Title",
        body: "blog.post1.section2Body",
      },
      {
        title: "blog.post1.section3Title",
        body: "blog.post1.section3Body",
      },
      {
        title: "blog.post1.section4Title",
        body: "blog.post1.section4Body",
      },
    ],
    accentClass:
      "from-[#c96f45]/20 via-[#f7ecde] to-[#86c8bc]/20",
  },
  {
    slug: "visibility-operating-system",
    index: "07",
    category: "blog.post2.category",
    title: "blog.post2.title",
    summary: "blog.post2.summary",
    readTime: "blog.post2.readTime",
    highlight: "blog.post2.highlight",
    audience: "blog.post2.audience",
    thesis: "blog.post2.thesis",
    takeawayKeys: ["blog.post2.point1", "blog.post2.point2", "blog.post2.point3"],
    sections: [
      {
        title: "blog.post2.section1Title",
        body: "blog.post2.section1Body",
      },
      {
        title: "blog.post2.section2Title",
        body: "blog.post2.section2Body",
      },
      {
        title: "blog.post2.section3Title",
        body: "blog.post2.section3Body",
      },
      {
        title: "blog.post2.section4Title",
        body: "blog.post2.section4Body",
      },
    ],
    accentClass:
      "from-[#86c8bc]/25 via-[#eff7f5] to-[#082032]/8",
  },
  {
    slug: "crawler-readable-brand-surface",
    index: "08",
    category: "blog.post3.category",
    title: "blog.post3.title",
    summary: "blog.post3.summary",
    readTime: "blog.post3.readTime",
    highlight: "blog.post3.highlight",
    audience: "blog.post3.audience",
    thesis: "blog.post3.thesis",
    takeawayKeys: ["blog.post3.point1", "blog.post3.point2", "blog.post3.point3"],
    sections: [
      {
        title: "blog.post3.section1Title",
        body: "blog.post3.section1Body",
      },
      {
        title: "blog.post3.section2Title",
        body: "blog.post3.section2Body",
      },
      {
        title: "blog.post3.section3Title",
        body: "blog.post3.section3Body",
      },
      {
        title: "blog.post3.section4Title",
        body: "blog.post3.section4Body",
      },
    ],
    accentClass:
      "from-[#082032]/10 via-[#edf2f7] to-[#c96f45]/16",
  },
  {
    slug: "inside-opencmo-workspace",
    index: "09",
    category: "blog.post4.category",
    title: "blog.post4.title",
    summary: "blog.post4.summary",
    readTime: "blog.post4.readTime",
    highlight: "blog.post4.highlight",
    audience: "blog.post4.audience",
    thesis: "blog.post4.thesis",
    takeawayKeys: ["blog.post4.point1", "blog.post4.point2", "blog.post4.point3"],
    sections: [
      {
        title: "blog.post4.section1Title",
        body: "blog.post4.section1Body",
      },
      {
        title: "blog.post4.section2Title",
        body: "blog.post4.section2Body",
      },
      {
        title: "blog.post4.section3Title",
        body: "blog.post4.section3Body",
      },
      {
        title: "blog.post4.section4Title",
        body: "blog.post4.section4Body",
      },
    ],
    accentClass:
      "from-[#f3dcc9]/55 via-[#f7ecde] to-[#86c8bc]/18",
  },
  {
    slug: "opencmo-vs-mautic-posthog",
    index: "10",
    category: "blog.post12.category",
    title: "blog.post12.title",
    summary: "blog.post12.summary",
    readTime: "blog.post12.readTime",
    highlight: "blog.post12.highlight",
    audience: "blog.post12.audience",
    thesis: "blog.post12.thesis",
    takeawayKeys: ["blog.post12.point1", "blog.post12.point2", "blog.post12.point3"],
    sections: [
      {
        title: "blog.post12.section1Title",
        body: "blog.post12.section1Body",
      },
      {
        title: "blog.post12.section2Title",
        body: "blog.post12.section2Body",
      },
      {
        title: "blog.post12.section3Title",
        body: "blog.post12.section3Body",
      },
      {
        title: "blog.post12.section4Title",
        body: "blog.post12.section4Body",
      },
    ],
    accentClass:
      "from-[#c9e6df]/28 via-[#f5f1ea] to-[#d7e5ff]/26",
  },
  {
    slug: "who-should-use-opencmo",
    index: "11",
    category: "blog.post5.category",
    title: "blog.post5.title",
    summary: "blog.post5.summary",
    readTime: "blog.post5.readTime",
    highlight: "blog.post5.highlight",
    audience: "blog.post5.audience",
    thesis: "blog.post5.thesis",
    takeawayKeys: ["blog.post5.point1", "blog.post5.point2", "blog.post5.point3"],
    sections: [
      {
        title: "blog.post5.section1Title",
        body: "blog.post5.section1Body",
      },
      {
        title: "blog.post5.section2Title",
        body: "blog.post5.section2Body",
      },
      {
        title: "blog.post5.section3Title",
        body: "blog.post5.section3Body",
      },
      {
        title: "blog.post5.section4Title",
        body: "blog.post5.section4Body",
      },
    ],
    accentClass:
      "from-[#c96f45]/28 via-[#f8e6d7] to-[#f3dcc9]/52",
  },
  {
    slug: "first-30-days-with-opencmo",
    index: "12",
    category: "blog.post6.category",
    title: "blog.post6.title",
    summary: "blog.post6.summary",
    readTime: "blog.post6.readTime",
    highlight: "blog.post6.highlight",
    audience: "blog.post6.audience",
    thesis: "blog.post6.thesis",
    takeawayKeys: ["blog.post6.point1", "blog.post6.point2", "blog.post6.point3"],
    sections: [
      {
        title: "blog.post6.section1Title",
        body: "blog.post6.section1Body",
      },
      {
        title: "blog.post6.section2Title",
        body: "blog.post6.section2Body",
      },
      {
        title: "blog.post6.section3Title",
        body: "blog.post6.section3Body",
      },
      {
        title: "blog.post6.section4Title",
        body: "blog.post6.section4Body",
      },
    ],
    accentClass:
      "from-[#86c8bc]/20 via-[#eff7f5] to-[#dce9f0]",
  },
];

export function getBlogArticlePath(slug: string) {
  return `/blog/${slug}`;
}

export function getLandingPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/", locale) : "/";
}

export function getBlogIndexPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/blog", locale) : "/blog";
}

export function getLocalizedBlogArticlePath(slug: string, locale?: SeoLocale | null) {
  const path = getBlogArticlePath(slug);
  return locale ? getLocalizedPublicPath(path, locale) : path;
}

export function getSampleAuditPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/sample-audit", locale) : "/sample-audit";
}

export function getB2BLeadsPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/b2b-leads", locale) : "/b2b-leads";
}

export function getSeoGeoPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/seo-geo", locale) : "/seo-geo";
}

export function getOpenSourcePath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/open-source", locale) : "/open-source";
}

export function getSampleDataPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/sample-data", locale) : "/sample-data";
}

export function getContactPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/contact", locale) : "/contact";
}

export function getDataPolicyPath(locale?: SeoLocale | null) {
  return locale ? getLocalizedPublicPath("/data-policy", locale) : "/data-policy";
}

export function findBlogArticleBySlug(slug: string) {
  return BLOG_ARTICLES.find((article) => article.slug === slug);
}
