import { Trash2 } from "lucide-react";
import type { TrackedKeyword, SerpSnapshot } from "../../types";
import { useI18n } from "../../i18n";

export function KeywordList({
  keywords,
  serpData,
  onDelete,
}: {
  keywords: TrackedKeyword[];
  serpData: SerpSnapshot[];
  onDelete: (id: number) => void;
}) {
  const serpMap = Object.fromEntries(serpData.map((s) => [s.keyword, s]));
  const { t } = useI18n();

  if (!keywords.length) {
    return <p className="py-3 text-sm text-gray-500">{t("keywords.noKeywords")}</p>;
  }

  return (
    <table className="mt-3 w-full text-sm">
      <thead>
        <tr className="border-b text-left text-gray-500">
          <th className="py-2 font-medium">{t("keywords.keyword")}</th>
          <th className="py-2 font-medium">{t("keywords.position")}</th>
          <th className="py-2 font-medium">{t("keywords.lastChecked")}</th>
          <th className="py-2 font-medium"></th>
        </tr>
      </thead>
      <tbody>
        {keywords.map((kw) => {
          const serp = serpMap[kw.keyword];
          return (
            <tr key={kw.id} className="border-b last:border-0">
              <td className="py-2 font-medium">{kw.keyword}</td>
              <td className="py-2">
                {serp?.position ? (
                  <span className="rounded bg-blue-50 px-2 py-0.5 text-blue-700">#{serp.position}</span>
                ) : serp?.error ? (
                  <span className="text-red-500">{t("common.error")}</span>
                ) : (
                  <span className="text-gray-400">&mdash;</span>
                )}
              </td>
              <td className="py-2 text-gray-500">{serp?.checked_at?.slice(0, 10) ?? "&mdash;"}</td>
              <td className="py-2 text-right">
                <button
                  onClick={() => onDelete(kw.id)}
                  className="rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500"
                >
                  <Trash2 size={14} />
                </button>
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
