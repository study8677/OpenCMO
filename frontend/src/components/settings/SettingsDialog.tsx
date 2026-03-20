import { useState, useEffect } from "react";
import { X, Key, Check } from "lucide-react";
import { getSettings, saveSettings } from "../../api/settings";
import { useI18n } from "../../i18n";

export function SettingsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useI18n();
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentStatus, setCurrentStatus] = useState<{
    api_key_set: boolean;
    api_key_masked: string;
  } | null>(null);

  useEffect(() => {
    getSettings().then((s) => {
      setCurrentStatus({ api_key_set: s.api_key_set, api_key_masked: s.api_key_masked });
      setBaseUrl(s.base_url);
      setModel(s.model);
    });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setSaved(false);
    try {
      await saveSettings({
        OPENAI_API_KEY: apiKey || undefined,
        OPENAI_BASE_URL: baseUrl,
        OPENCMO_MODEL_DEFAULT: model,
      });
      setSaved(true);
      setApiKey("");
      const s = await getSettings();
      setCurrentStatus({ api_key_set: s.api_key_set, api_key_masked: s.api_key_masked });
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl">
        <div className="mb-5 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">{t("settings.title")}</h2>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4">
          {/* API Key Status */}
          {currentStatus && (
            <div
              className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium ${
                currentStatus.api_key_set
                  ? "bg-emerald-50 text-emerald-700"
                  : "bg-amber-50 text-amber-700"
              }`}
            >
              <Key size={14} />
              {currentStatus.api_key_set
                ? `${t("settings.apiKeySet")} (${currentStatus.api_key_masked})`
                : t("settings.apiKeyNotSet")}
            </div>
          )}

          {/* API Key */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.apiKey")}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={t("settings.apiKeyPlaceholder")}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.apiKeyHint")}
            </p>
          </div>

          {/* Base URL */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.baseUrl")}
            </label>
            <input
              type="url"
              value={baseUrl}
              onChange={(e) => setBaseUrl(e.target.value)}
              placeholder={t("settings.baseUrlPlaceholder")}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.baseUrlHint")}
            </p>
          </div>

          {/* Model */}
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">
              {t("settings.model")}
            </label>
            <input
              value={model}
              onChange={(e) => setModel(e.target.value)}
              placeholder={t("settings.modelPlaceholder")}
              className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100"
            />
            <p className="mt-1 text-[10px] text-slate-400">
              {t("settings.modelHint")}
            </p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-xl border border-slate-200 px-4 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            {t("common.cancel")}
          </button>
          <button
            onClick={handleSave}
            disabled={loading}
            className="flex items-center gap-2 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition-all hover:bg-indigo-700 disabled:opacity-50"
          >
            {saved ? (
              <>
                <Check size={14} />
                {t("settings.saved")}
              </>
            ) : (
              t("settings.save")
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
