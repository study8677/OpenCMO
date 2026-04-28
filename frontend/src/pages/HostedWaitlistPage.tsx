import { PublicSiteHeader } from "../components/marketing/PublicSiteHeader";
import { SiteFooter } from "../components/layout/SiteFooter";
import { Link } from "react-router";
import { ArrowRight } from "lucide-react";
import { useI18n } from "../i18n";
import { usePublicPageMetadata } from "../hooks/usePublicPageMetadata";
import { PUBLIC_HOME_NAV } from "../content/marketing";

/**
 * Standalone /hosted compatibility page that routes visitors to the
 * already-deployed OpenCMO workspace.
 */
export function HostedWaitlistPage() {
  const { t } = useI18n();

  usePublicPageMetadata({
    title: t("landing.hosted.title"),
    description: t("landing.hosted.subtitle"),
    basePath: "/hosted",
  });

  return (
    <div className="min-h-screen bg-[#08141f] text-white">
      <PublicSiteHeader items={PUBLIC_HOME_NAV} theme="dark" />

      <main className="mx-auto max-w-5xl px-4 py-24 text-center lg:px-8 lg:py-32">
        <p className="text-sm font-semibold uppercase tracking-wider text-white/55">
          {t("landing.pathDeployedTitle")}
        </p>
        <h1 className="font-display mx-auto mt-5 max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">
          {t("landing.workspaceCta")}
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-white/72">
          {t("landing.pathDeployedDesc")}
        </p>
        <Link
          to="/workspace"
          className="mt-10 inline-flex items-center gap-2 rounded-full bg-[#f7ecde] px-7 py-4 text-sm font-semibold text-[#082032] transition-colors hover:bg-white"
        >
          {t("landing.workspaceCta")}
          <ArrowRight size={16} />
        </Link>
      </main>

      <SiteFooter />
    </div>
  );
}
