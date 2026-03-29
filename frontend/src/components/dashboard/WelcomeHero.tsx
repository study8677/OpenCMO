import { useState } from "react";
import { ArrowRight, CheckCircle2, KeyRound, Search, Globe, Users, Sparkles } from "lucide-react";
import { hasEssentialKeys } from "../../api/userKeys";
import { useI18n } from "../../i18n";
import { useCreateMonitor } from "../../hooks/useMonitors";
import { SettingsDialog } from "../settings/SettingsDialog";

const FEATURES = [
  { iconKey: "seo", icon: Search, labelKey: "welcome.featureSeo" as const, descKey: "welcome.featureSeoDesc" as const, color: "bg-sky-50 text-sky-600" },
  { iconKey: "geo", icon: Globe, labelKey: "welcome.featureGeo" as const, descKey: "welcome.featureGeoDesc" as const, color: "bg-emerald-50 text-emerald-600" },
  { iconKey: "community", icon: Users, labelKey: "welcome.featureCommunity" as const, descKey: "welcome.featureCommunityDesc" as const, color: "bg-amber-50 text-amber-600" },
];

export function WelcomeHero({
  onTaskCreated,
}: {
  onTaskCreated?: (taskId: string, url: string) => void;
}) {
  const { t, locale } = useI18n();
  const [url, setUrl] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const createMonitor = useCreateMonitor();
  const keyStatus = hasEssentialKeys();
  const keysReady = keyStatus.llm && keyStatus.tavily;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;
    const result = await createMonitor.mutateAsync({ url: url.trim(), cron_expr: "0 9 * * *", locale });
    if (result.task_id && onTaskCreated) {
      onTaskCreated(result.task_id, url.trim());
    }
    setUrl("");
  };

  return (
    <>
      <div className="animate-in fade-in slide-in-from-bottom-6 duration-700 ease-out">
        {/* Hero card */}
        <div className="relative overflow-hidden rounded-3xl border border-slate-200/60 bg-[radial-gradient(ellipse_at_top,_rgba(99,102,241,0.12),_transparent_50%),linear-gradient(180deg,#ffffff_0%,#f8fafc_100%)] p-8 shadow-[0_20px_60px_rgba(15,23,42,0.08)] ring-1 ring-white/50 sm:p-10">
          {/* Decorative elements */}
          <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-indigo-100/40 blur-3xl" />
          <div className="absolute -left-8 bottom-0 h-32 w-32 rounded-full bg-violet-100/30 blur-2xl" />

          <div className="relative">
            {/* Badge */}
            <div className="mb-6 inline-flex items-center gap-2 rounded-full bg-indigo-50 px-4 py-2 text-sm font-medium text-indigo-700 ring-1 ring-indigo-100">
              <Sparkles size={16} />
              AI-Powered Marketing
            </div>

            {/* Title */}
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              {t("welcome.title")}
            </h1>
            <p className="mt-4 max-w-2xl text-lg leading-relaxed text-slate-500">
              {t("welcome.subtitle")}
            </p>

            {/* Step 1: API Keys status */}
            <div className="mt-8 space-y-4">
              <button
                onClick={() => setShowSettings(true)}
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 text-sm font-medium transition-all hover:shadow-sm ${
                  keysReady
                    ? "border-emerald-200 bg-emerald-50/80 text-emerald-700"
                    : "border-amber-200 bg-amber-50/80 text-amber-700 hover:border-amber-300"
                }`}
              >
                {keysReady ? (
                  <CheckCircle2 size={18} className="text-emerald-500" />
                ) : (
                  <KeyRound size={18} className="text-amber-500" />
                )}
                {keysReady ? t("welcome.step1Done") : t("welcome.step1")}
              </button>

              {/* Step 2: URL input */}
              <div>
                <p className="mb-2 text-sm font-medium text-slate-600">{t("welcome.step2")}</p>
                <form onSubmit={handleSubmit} className="flex gap-3">
                  <input
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    type="url"
                    required
                    placeholder={t("monitorForm.urlPlaceholder")}
                    className="flex-1 rounded-xl border border-slate-200 bg-white px-5 py-3.5 text-base shadow-sm transition-shadow placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                  />
                  <button
                    type="submit"
                    disabled={createMonitor.isPending || !url.trim()}
                    className="flex items-center gap-2 rounded-xl bg-slate-900 px-6 py-3.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-slate-800 hover:shadow-md disabled:opacity-50 active:scale-95"
                  >
                    {createMonitor.isPending ? t("monitorForm.analyzing") : t("monitorForm.startMonitoring")}
                    <ArrowRight size={16} />
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>

        {/* Feature cards */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {FEATURES.map((feature) => (
            <div
              key={feature.iconKey}
              className="rounded-2xl border border-slate-200/60 bg-white p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
            >
              <div className={`mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl ${feature.color}`}>
                <feature.icon size={20} />
              </div>
              <h3 className="text-sm font-semibold text-slate-900">{t(feature.labelKey)}</h3>
              <p className="mt-1 text-xs leading-relaxed text-slate-500">{t(feature.descKey)}</p>
            </div>
          ))}
        </div>
      </div>

      {showSettings && <SettingsDialog onClose={() => setShowSettings(false)} />}
    </>
  );
}
