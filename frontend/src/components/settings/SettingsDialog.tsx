import { useState, useEffect } from "react";
import { X, Key, Check, ChevronDown, ChevronRight } from "lucide-react";
import { getSettings, saveSettings } from "../../api/settings";
import { useI18n } from "../../i18n";
import type { AISettings } from "../../types";

function StatusBadge({ ok, okText, noText }: { ok: boolean; okText: string; noText: string }) {
  return (
    <div
      className={`flex items-center gap-2 rounded-xl px-3 py-2 text-xs font-medium ${
        ok ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"
      }`}
    >
      <Key size={14} />
      {ok ? okText : noText}
    </div>
  );
}

function Section({
  title,
  defaultOpen = false,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-t border-slate-100 pt-4">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="mb-3 flex w-full items-center gap-1.5 text-sm font-semibold text-slate-800"
      >
        {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        {title}
      </button>
      {open && <div className="space-y-3">{children}</div>}
    </div>
  );
}

function Field({
  label,
  hint,
  type = "text",
  placeholder,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  type?: string;
  placeholder?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  const inputClass =
    "w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm shadow-sm placeholder:text-slate-400 focus:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-100";
  return (
    <div>
      <label className="mb-1 block text-xs font-medium text-slate-600">{label}</label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={inputClass}
      />
      {hint && <p className="mt-1 text-[10px] text-slate-400">{hint}</p>}
    </div>
  );
}

function Toggle({
  label,
  hint,
  value,
  onChange,
}: {
  label: string;
  hint?: string;
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2.5">
      <div>
        <p className="text-xs font-medium text-slate-700">{label}</p>
        {hint && <p className="text-[10px] text-slate-400">{hint}</p>}
      </div>
      <button
        type="button"
        onClick={() => onChange(!value)}
        className={`relative inline-flex h-5 w-9 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
          value ? "bg-indigo-600" : "bg-slate-300"
        }`}
      >
        <span
          className={`pointer-events-none inline-block h-4 w-4 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
            value ? "translate-x-4" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}

export function SettingsDialog({ onClose }: { onClose: () => void }) {
  const { t } = useI18n();
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [status, setStatus] = useState<AISettings | null>(null);

  // AI Provider
  const [apiKey, setApiKey] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [model, setModel] = useState("");

  // Reddit
  const [redditClientId, setRedditClientId] = useState("");
  const [redditClientSecret, setRedditClientSecret] = useState("");
  const [redditUsername, setRedditUsername] = useState("");
  const [redditPassword, setRedditPassword] = useState("");
  const [autoPublish, setAutoPublish] = useState(false);

  // Twitter
  const [twitterApiKey, setTwitterApiKey] = useState("");
  const [twitterApiSecret, setTwitterApiSecret] = useState("");
  const [twitterAccessToken, setTwitterAccessToken] = useState("");
  const [twitterAccessSecret, setTwitterAccessSecret] = useState("");

  // GEO
  const [anthropicKey, setAnthropicKey] = useState("");
  const [googleAiKey, setGoogleAiKey] = useState("");
  const [geoChatgpt, setGeoChatgpt] = useState(false);

  // SEO
  const [pagespeedKey, setPagespeedKey] = useState("");

  // Search (Tavily)
  const [tavilyKey, setTavilyKey] = useState("");

  // SERP
  const [dataforseoLogin, setDataforseoLogin] = useState("");
  const [dataforseoPassword, setDataforseoPassword] = useState("");

  // Email
  const [smtpHost, setSmtpHost] = useState("");
  const [smtpPort, setSmtpPort] = useState("");
  const [smtpUser, setSmtpUser] = useState("");
  const [smtpPass, setSmtpPass] = useState("");
  const [reportEmail, setReportEmail] = useState("");

  useEffect(() => {
    getSettings().then((s) => {
      setStatus(s);
      setBaseUrl(s.base_url);
      setModel(s.model);
      setAutoPublish(s.auto_publish);
      setGeoChatgpt(s.geo_chatgpt_enabled);
      setSmtpHost(s.smtp_host);
      setSmtpPort(s.smtp_port);
      setSmtpUser(s.smtp_user);
      setReportEmail(s.report_email);
    });
  }, []);

  const handleSave = async () => {
    setLoading(true);
    setSaved(false);
    try {
      await saveSettings({
        // AI Provider
        OPENAI_API_KEY: apiKey || undefined,
        OPENAI_BASE_URL: baseUrl,
        OPENCMO_MODEL_DEFAULT: model,
        // Reddit
        REDDIT_CLIENT_ID: redditClientId || undefined,
        REDDIT_CLIENT_SECRET: redditClientSecret || undefined,
        REDDIT_USERNAME: redditUsername || undefined,
        REDDIT_PASSWORD: redditPassword || undefined,
        OPENCMO_AUTO_PUBLISH: autoPublish ? "1" : "0",
        // Twitter
        TWITTER_API_KEY: twitterApiKey || undefined,
        TWITTER_API_SECRET: twitterApiSecret || undefined,
        TWITTER_ACCESS_TOKEN: twitterAccessToken || undefined,
        TWITTER_ACCESS_SECRET: twitterAccessSecret || undefined,
        // GEO
        ANTHROPIC_API_KEY: anthropicKey || undefined,
        GOOGLE_AI_API_KEY: googleAiKey || undefined,
        OPENCMO_GEO_CHATGPT: geoChatgpt ? "1" : "0",
        // SEO
        PAGESPEED_API_KEY: pagespeedKey || undefined,
        // Search (Tavily)
        TAVILY_API_KEY: tavilyKey || undefined,
        // SERP
        DATAFORSEO_LOGIN: dataforseoLogin || undefined,
        DATAFORSEO_PASSWORD: dataforseoPassword || undefined,
        // Email
        OPENCMO_SMTP_HOST: smtpHost || undefined,
        OPENCMO_SMTP_PORT: smtpPort || undefined,
        OPENCMO_SMTP_USER: smtpUser || undefined,
        OPENCMO_SMTP_PASS: smtpPass || undefined,
        OPENCMO_REPORT_EMAIL: reportEmail || undefined,
      });
      setSaved(true);
      // Clear sensitive fields
      setApiKey("");
      setRedditClientId("");
      setRedditClientSecret("");
      setRedditUsername("");
      setRedditPassword("");
      setTwitterApiKey("");
      setTwitterApiSecret("");
      setTwitterAccessToken("");
      setTwitterAccessSecret("");
      setAnthropicKey("");
      setGoogleAiKey("");
      setPagespeedKey("");
      setTavilyKey("");
      setDataforseoLogin("");
      setDataforseoPassword("");
      setSmtpPass("");
      // Refresh status
      const s = await getSettings();
      setStatus(s);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm">
      <div className="w-full max-w-md max-h-[85vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl">
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
          {/* ── AI Provider (always open) ── */}
          {status && (
            <StatusBadge
              ok={status.api_key_set}
              okText={`${t("settings.apiKeySet")} (${status.api_key_masked})`}
              noText={t("settings.apiKeyNotSet")}
            />
          )}
          <Field
            label={t("settings.apiKey")}
            type="password"
            placeholder={t("settings.apiKeyPlaceholder")}
            hint={t("settings.apiKeyHint")}
            value={apiKey}
            onChange={setApiKey}
          />
          <Field
            label={t("settings.baseUrl")}
            type="url"
            placeholder={t("settings.baseUrlPlaceholder")}
            hint={t("settings.baseUrlHint")}
            value={baseUrl}
            onChange={setBaseUrl}
          />
          <Field
            label={t("settings.model")}
            placeholder={t("settings.modelPlaceholder")}
            hint={t("settings.modelHint")}
            value={model}
            onChange={setModel}
          />

          {/* ── Reddit ── */}
          <Section title={t("settings.redditSection")} defaultOpen={false}>
            {status && (
              <StatusBadge
                ok={status.reddit_configured}
                okText={`${t("settings.redditConfigured")} (u/${status.reddit_username})`}
                noText={t("settings.redditNotConfigured")}
              />
            )}
            <Field label={t("settings.redditClientId")} placeholder={t("settings.redditClientIdPlaceholder")} value={redditClientId} onChange={setRedditClientId} />
            <Field label={t("settings.redditClientSecret")} type="password" placeholder={t("settings.redditClientSecretPlaceholder")} value={redditClientSecret} onChange={setRedditClientSecret} />
            <Field label={t("settings.redditUsername")} placeholder={t("settings.redditUsernamePlaceholder")} value={redditUsername} onChange={setRedditUsername} />
            <Field label={t("settings.redditPassword")} type="password" placeholder={t("settings.redditPasswordPlaceholder")} value={redditPassword} onChange={setRedditPassword} />
            <p className="text-[10px] text-slate-400">{t("settings.redditHint")}</p>
            <Toggle label={t("settings.autoPublish")} hint={t("settings.autoPublishHint")} value={autoPublish} onChange={setAutoPublish} />
          </Section>

          {/* ── Twitter ── */}
          <Section title={t("settings.twitterSection")}>
            {status && (
              <StatusBadge
                ok={status.twitter_configured}
                okText={`${t("settings.twitterConfigured")} (${status.twitter_api_key_masked})`}
                noText={t("settings.twitterNotConfigured")}
              />
            )}
            <Field label={t("settings.twitterApiKey")} type="password" placeholder="API Key" value={twitterApiKey} onChange={setTwitterApiKey} />
            <Field label={t("settings.twitterApiSecret")} type="password" placeholder="API Secret" value={twitterApiSecret} onChange={setTwitterApiSecret} />
            <Field label={t("settings.twitterAccessToken")} type="password" placeholder="Access Token" value={twitterAccessToken} onChange={setTwitterAccessToken} />
            <Field label={t("settings.twitterAccessSecret")} type="password" placeholder="Access Token Secret" value={twitterAccessSecret} onChange={setTwitterAccessSecret} />
            <p className="text-[10px] text-slate-400">{t("settings.twitterHint")}</p>
          </Section>

          {/* ── GEO Detection ── */}
          <Section title={t("settings.geoSection")}>
            {status && (
              <>
                <StatusBadge
                  ok={status.anthropic_key_set}
                  okText={`Claude ${t("settings.configured")} (${status.anthropic_key_masked})`}
                  noText={`Claude ${t("settings.notConfigured")}`}
                />
                <StatusBadge
                  ok={status.google_ai_key_set}
                  okText={`Gemini ${t("settings.configured")} (${status.google_ai_key_masked})`}
                  noText={`Gemini ${t("settings.notConfigured")}`}
                />
              </>
            )}
            <Field label={t("settings.anthropicKey")} type="password" placeholder="sk-ant-..." value={anthropicKey} onChange={setAnthropicKey} />
            <Field label={t("settings.googleAiKey")} type="password" placeholder="AIza..." value={googleAiKey} onChange={setGoogleAiKey} />
            <Toggle label={t("settings.geoChatgpt")} hint={t("settings.geoChatgptHint")} value={geoChatgpt} onChange={setGeoChatgpt} />
            <p className="text-[10px] text-slate-400">{t("settings.geoHint")}</p>
          </Section>

          {/* ── SEO ── */}
          <Section title={t("settings.seoSection")}>
            {status && (
              <StatusBadge
                ok={status.pagespeed_key_set}
                okText={`PageSpeed ${t("settings.configured")} (${status.pagespeed_key_masked})`}
                noText={t("settings.pagespeedNotConfigured")}
              />
            )}
            <Field label={t("settings.pagespeedKey")} type="password" placeholder="AIza..." hint={t("settings.pagespeedHint")} value={pagespeedKey} onChange={setPagespeedKey} />
          </Section>

          {/* ── Search (Tavily) ── */}
          <Section title={t("settings.tavilySection")}>
            {status && (
              <StatusBadge
                ok={status.tavily_key_set}
                okText={`Tavily ${t("settings.configured")} (${status.tavily_key_masked})`}
                noText={t("settings.tavilyNotConfigured")}
              />
            )}
            <Field
              label={t("settings.tavilyKey")}
              type="password"
              placeholder="tvly-..."
              hint={t("settings.tavilyHint")}
              value={tavilyKey}
              onChange={setTavilyKey}
            />
          </Section>

          {/* ── SERP ── */}
          <Section title={t("settings.serpSection")}>
            {status && (
              <StatusBadge
                ok={status.dataforseo_configured}
                okText={`DataForSEO ${t("settings.configured")} (${status.dataforseo_login})`}
                noText={t("settings.dataforseoNotConfigured")}
              />
            )}
            <Field label={t("settings.dataforseoLogin")} placeholder="login@example.com" value={dataforseoLogin} onChange={setDataforseoLogin} />
            <Field label={t("settings.dataforseoPassword")} type="password" placeholder="Password" value={dataforseoPassword} onChange={setDataforseoPassword} />
            <p className="text-[10px] text-slate-400">{t("settings.dataforseoHint")}</p>
          </Section>

          {/* ── Email Reports ── */}
          <Section title={t("settings.emailSection")}>
            {status && (
              <StatusBadge
                ok={status.email_configured}
                okText={`${t("settings.emailConfigured")} (${status.smtp_user})`}
                noText={t("settings.emailNotConfigured")}
              />
            )}
            <Field label={t("settings.smtpHost")} placeholder="smtp.gmail.com" value={smtpHost} onChange={setSmtpHost} />
            <Field label={t("settings.smtpPort")} placeholder="587" value={smtpPort} onChange={setSmtpPort} />
            <Field label={t("settings.smtpUser")} placeholder="user@example.com" value={smtpUser} onChange={setSmtpUser} />
            <Field label={t("settings.smtpPass")} type="password" placeholder="App password" value={smtpPass} onChange={setSmtpPass} />
            <Field label={t("settings.reportEmail")} placeholder="report@example.com" hint={t("settings.reportEmailHint")} value={reportEmail} onChange={setReportEmail} />
          </Section>
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
