import { Link, useLocation } from "react-router";
import { useI18n } from "../../i18n";
import type { TranslationKey } from "../../i18n";

const TABS: { path: string; labelKey: TranslationKey }[] = [
  { path: "", labelKey: "project.overview" },
  { path: "/seo", labelKey: "project.seo" },
  { path: "/geo", labelKey: "project.geo" },
  { path: "/serp", labelKey: "project.serp" },
  { path: "/community", labelKey: "project.community" },
];

export function ProjectTabs({ projectId }: { projectId: number }) {
  const { pathname } = useLocation();
  const { t } = useI18n();
  const base = `/projects/${projectId}`;

  return (
    <div className="mb-6 flex gap-1 border-b">
      {TABS.map(({ path, labelKey }) => {
        const to = `${base}${path}`;
        const active = pathname === to;
        return (
          <Link
            key={path}
            to={to}
            className={`border-b-2 px-4 py-2 text-sm font-medium transition-colors ${
              active
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            {t(labelKey)}
          </Link>
        );
      })}
    </div>
  );
}
