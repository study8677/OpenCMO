import { useState, useEffect, useCallback, useRef } from "react";
import { Link, useParams } from "react-router";
import {
  Palette, Users, Shield, Ban, Sparkles, FileText,
  Check, Loader2, X, ArrowLeft,
} from "lucide-react";
import { useBrandKit, useSaveBrandKit } from "../hooks/useBrandKit";
import { useProjectSummary } from "../hooks/useProject";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";
import { ProjectHeader } from "../components/project/ProjectHeader";
import { ProjectTabs } from "../components/project/ProjectTabs";
import { useI18n } from "../i18n";
import type { TranslationKey } from "../i18n";

function TagInput({
  tags,
  onChange,
  placeholder,
  morePlaceholder,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder: string;
  morePlaceholder: string;
}) {
  const [input, setInput] = useState("");

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.key === "Enter" || e.key === ",") && input.trim()) {
      e.preventDefault();
      if (!tags.includes(input.trim())) {
        onChange([...tags, input.trim()]);
      }
      setInput("");
    }
    if (e.key === "Backspace" && !input && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  return (
    <div className="flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white p-3 transition-all focus-within:border-purple-300 focus-within:ring-2 focus-within:ring-purple-100">
      {tags.map((tag, i) => (
        <span
          key={i}
          className="inline-flex items-center gap-1 rounded-lg bg-red-50 px-2.5 py-1 text-sm font-medium text-red-700"
        >
          {tag}
          <button
            type="button"
            onClick={() => onChange(tags.filter((_, idx) => idx !== i))}
            className="text-red-400 hover:text-red-600 transition"
          >
            <X size={14} />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : morePlaceholder}
        className="flex-1 min-w-[120px] bg-transparent text-sm outline-none placeholder:text-slate-400"
      />
    </div>
  );
}

interface FieldConfig {
  key: string;
  labelKey: TranslationKey;
  icon: React.ElementType;
  placeholderKey: TranslationKey;
  descKey: TranslationKey;
  type: "textarea" | "tags";
  gradient: string;
}

const FIELDS: FieldConfig[] = [
  {
    key: "tone_of_voice",
    labelKey: "brandKit.toneLabel",
    icon: Palette,
    placeholderKey: "brandKit.tonePlaceholder",
    descKey: "brandKit.toneDesc",
    type: "textarea",
    gradient: "from-violet-500/10 to-purple-500/10",
  },
  {
    key: "target_audience",
    labelKey: "brandKit.audienceLabel",
    icon: Users,
    placeholderKey: "brandKit.audiencePlaceholder",
    descKey: "brandKit.audienceDesc",
    type: "textarea",
    gradient: "from-blue-500/10 to-cyan-500/10",
  },
  {
    key: "core_values",
    labelKey: "brandKit.valuesLabel",
    icon: Shield,
    placeholderKey: "brandKit.valuesPlaceholder",
    descKey: "brandKit.valuesDesc",
    type: "textarea",
    gradient: "from-emerald-500/10 to-teal-500/10",
  },
  {
    key: "forbidden_words",
    labelKey: "brandKit.forbiddenLabel",
    icon: Ban,
    placeholderKey: "brandKit.tagPlaceholder",
    descKey: "brandKit.forbiddenDesc",
    type: "tags",
    gradient: "from-red-500/10 to-orange-500/10",
  },
  {
    key: "best_examples",
    labelKey: "brandKit.examplesLabel",
    icon: Sparkles,
    placeholderKey: "brandKit.examplesPlaceholder",
    descKey: "brandKit.examplesDesc",
    type: "textarea",
    gradient: "from-amber-500/10 to-yellow-500/10",
  },
  {
    key: "custom_instructions",
    labelKey: "brandKit.instructionsLabel",
    icon: FileText,
    placeholderKey: "brandKit.instructionsPlaceholder",
    descKey: "brandKit.instructionsDesc",
    type: "textarea",
    gradient: "from-slate-500/10 to-zinc-500/10",
  },
];

export function BrandKitPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: summary, isLoading: isLoadingSummary } = useProjectSummary(projectId);
  const { data: kit, isLoading, error } = useBrandKit(projectId);
  const saveMutation = useSaveBrandKit(projectId);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { t } = useI18n();

  useEffect(() => {
    if (kit) {
      setForm({
        tone_of_voice: kit.tone_of_voice || "",
        target_audience: kit.target_audience || "",
        core_values: kit.core_values || "",
        forbidden_words: kit.forbidden_words || [],
        best_examples: kit.best_examples || "",
        custom_instructions: kit.custom_instructions || "",
      });
    }
  }, [kit]);

  const debouncedSave = useCallback(
    (updatedForm: Record<string, unknown>) => {
      clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        saveMutation.mutate(updatedForm as any, {
          onSuccess: () => {
            setSaved(true);
            setTimeout(() => setSaved(false), 2000);
          },
        });
      }, 1200);
    },
    [saveMutation],
  );

  const updateField = (key: string, value: unknown) => {
    const next = { ...form, [key]: value };
    setForm(next);
    debouncedSave(next);
  };

  if (isLoading || isLoadingSummary) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;
  if (!summary) return <ErrorAlert message={t("common.projectNotFound")} />;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <div className="mb-6 flex flex-wrap items-center gap-3">
        <Link
          to="/workspace"
          className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:border-slate-300 hover:text-slate-900"
        >
          <ArrowLeft size={16} />
          {t("brandKit.backToDashboard")}
        </Link>
        <Link
          to={`/projects/${projectId}`}
          className="text-sm font-medium text-slate-500 transition-colors hover:text-slate-900"
        >
          {t("brandKit.backToProject")}
        </Link>
      </div>

      <ProjectHeader project={summary.project} isPaused={summary.is_paused} />
      <ProjectTabs projectId={projectId} />

      <div className="mx-auto max-w-3xl">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
                {t("brandKit.title")}
              </h1>
              <p className="mt-1 text-sm text-zinc-500">
                {t("brandKit.subtitle")}
              </p>
            </div>
            <div className="flex items-center gap-2">
              {saveMutation.isPending && (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                  <Loader2 size={14} className="animate-spin" />
                  {t("brandKit.saving")}
                </span>
              )}
              {saved && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 shadow-sm animate-in fade-in zoom-in-95 duration-300">
                  <Check size={14} />
                  {t("brandKit.saved")}
                </span>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-5">
          {FIELDS.map((field) => {
            const Icon = field.icon;
            return (
              <div
                key={field.key}
                className={`rounded-2xl border border-slate-200/70 bg-gradient-to-br ${field.gradient} p-5 shadow-sm transition-all hover:shadow-md`}
              >
                <div className="mb-2 flex items-center gap-2.5">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
                    <Icon size={16} className="text-slate-600" />
                  </div>
                  <h3 className="text-sm font-semibold text-slate-800">
                    {t(field.labelKey)}
                  </h3>
                </div>
                <p className="mb-3 ml-[42px] text-xs text-slate-500">
                  {t(field.descKey)}
                </p>
                <div className="ml-[42px]">
                  {field.type === "tags" ? (
                    <TagInput
                      tags={(form[field.key] as string[]) || []}
                      onChange={(tags) => updateField(field.key, tags)}
                      placeholder={t(field.placeholderKey)}
                      morePlaceholder={t("brandKit.tagMore")}
                    />
                  ) : (
                    <textarea
                      value={(form[field.key] as string) || ""}
                      onChange={(e) => updateField(field.key, e.target.value)}
                      placeholder={t(field.placeholderKey)}
                      rows={3}
                      className="w-full resize-none rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 placeholder:text-slate-400 transition-all focus:border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-100"
                    />
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
