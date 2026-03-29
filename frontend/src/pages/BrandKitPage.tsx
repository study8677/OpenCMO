import { useState, useEffect, useCallback, useRef } from "react";
import { useParams } from "react-router";
import {
  Palette, Users, Shield, Ban, Sparkles, FileText,
  Check, Loader2, X,
} from "lucide-react";
import { useBrandKit, useSaveBrandKit } from "../hooks/useBrandKit";
import { LoadingSpinner } from "../components/common/LoadingSpinner";
import { ErrorAlert } from "../components/common/ErrorAlert";

function TagInput({
  tags,
  onChange,
}: {
  tags: string[];
  onChange: (tags: string[]) => void;
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
        placeholder={tags.length === 0 ? "Type and press Enter to add..." : "Add more..."}
        className="flex-1 min-w-[120px] bg-transparent text-sm outline-none placeholder:text-slate-400"
      />
    </div>
  );
}

interface FieldConfig {
  key: string;
  label: string;
  icon: React.ElementType;
  placeholder: string;
  description: string;
  type: "textarea" | "tags";
  gradient: string;
}

const FIELDS: FieldConfig[] = [
  {
    key: "tone_of_voice",
    label: "Brand Tone of Voice",
    icon: Palette,
    placeholder: "e.g. Professional yet approachable, technically confident, uses analogies from daily life...",
    description: "Describe the personality and voice that should be consistent across all AI-generated content.",
    type: "textarea",
    gradient: "from-violet-500/10 to-purple-500/10",
  },
  {
    key: "target_audience",
    label: "Target Audience",
    icon: Users,
    placeholder: "e.g. Indie developers and solo founders building B2B SaaS, age 25-45, tech-savvy...",
    description: "Who are you creating content for? Be as specific as possible.",
    type: "textarea",
    gradient: "from-blue-500/10 to-cyan-500/10",
  },
  {
    key: "core_values",
    label: "Core Value Proposition",
    icon: Shield,
    placeholder: "e.g. Open-source, privacy-first analytics — no data ever leaves the user's server...",
    description: "What makes your product unique? What's the key message every piece of content should reinforce?",
    type: "textarea",
    gradient: "from-emerald-500/10 to-teal-500/10",
  },
  {
    key: "forbidden_words",
    label: "Forbidden Words & Phrases",
    icon: Ban,
    placeholder: "",
    description: "Words or phrases your brand should NEVER use in any content (PR-sensitive terms, competitor names, etc.).",
    type: "tags",
    gradient: "from-red-500/10 to-orange-500/10",
  },
  {
    key: "best_examples",
    label: "Best Content Examples",
    icon: Sparkles,
    placeholder: "Paste your best-performing tweet, Reddit post, or blog excerpt here...",
    description: "Provide 1-3 examples of content that perfectly captures your brand voice.",
    type: "textarea",
    gradient: "from-amber-500/10 to-yellow-500/10",
  },
  {
    key: "custom_instructions",
    label: "Custom Instructions",
    icon: FileText,
    placeholder: "e.g. Always mention the open-source nature. Never compare directly to X competitor...",
    description: "Any additional rules or context that agents should follow when generating content.",
    type: "textarea",
    gradient: "from-slate-500/10 to-zinc-500/10",
  },
];

export function BrandKitPage() {
  const { id } = useParams();
  const projectId = Number(id);
  const { data: kit, isLoading, error } = useBrandKit(projectId);
  const saveMutation = useSaveBrandKit(projectId);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [saved, setSaved] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

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

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorAlert message={error.message} />;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out max-w-3xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-900">
              Brand Kit
            </h1>
            <p className="text-sm text-zinc-500 mt-1">
              Define your brand's DNA. Every AI agent will follow these guidelines when
              generating content.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {saveMutation.isPending && (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500">
                <Loader2 size={14} className="animate-spin" />
                Saving...
              </span>
            )}
            {saved && (
              <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 shadow-sm animate-in fade-in zoom-in-95 duration-300">
                <Check size={14} />
                Saved
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
              <div className="flex items-center gap-2.5 mb-2">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white shadow-sm">
                  <Icon size={16} className="text-slate-600" />
                </div>
                <h3 className="text-sm font-semibold text-slate-800">
                  {field.label}
                </h3>
              </div>
              <p className="text-xs text-slate-500 mb-3 ml-[42px]">
                {field.description}
              </p>
              <div className="ml-[42px]">
                {field.type === "tags" ? (
                  <TagInput
                    tags={(form[field.key] as string[]) || []}
                    onChange={(tags) => updateField(field.key, tags)}
                  />
                ) : (
                  <textarea
                    value={(form[field.key] as string) || ""}
                    onChange={(e) => updateField(field.key, e.target.value)}
                    placeholder={field.placeholder}
                    rows={3}
                    className="w-full rounded-xl border border-slate-200 bg-white p-3 text-sm text-slate-800 placeholder:text-slate-400 transition-all focus:border-purple-300 focus:outline-none focus:ring-2 focus:ring-purple-100 resize-none"
                  />
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
