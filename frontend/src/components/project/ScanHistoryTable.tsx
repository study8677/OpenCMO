import type { LatestScans } from "../../types";
import { useI18n } from "../../i18n";

export function ScanHistoryTable({ latest }: { latest: LatestScans }) {
  const { t } = useI18n();

  const rows = [
    { type: t("project.seo"), date: latest.seo?.scanned_at, detail: latest.seo?.score != null ? `${Math.round(latest.seo.score * 100)}%` : "—" },
    { type: t("project.geo"), date: latest.geo?.scanned_at, detail: latest.geo?.score != null ? `${latest.geo.score}/100` : "—" },
    { type: t("project.community"), date: latest.community?.scanned_at, detail: latest.community?.total_hits != null ? t("scan.hits", { count: latest.community.total_hits }) : "—" },
  ];

  return (
    <div className="rounded-xl border bg-white">
      <div className="border-b px-4 py-3">
        <h3 className="font-semibold">{t("scan.latestScans")}</h3>
      </div>
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="px-4 py-2 font-medium">{t("scan.type")}</th>
            <th className="px-4 py-2 font-medium">{t("scan.lastScanned")}</th>
            <th className="px-4 py-2 font-medium">{t("scan.result")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.type} className="border-b last:border-0">
              <td className="px-4 py-2 font-medium">{r.type}</td>
              <td className="px-4 py-2 text-gray-500">{r.date?.slice(0, 10) ?? t("common.never")}</td>
              <td className="px-4 py-2">{r.detail}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
