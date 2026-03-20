import ReactMarkdown from "react-markdown";
import type { ChatMessage } from "../../types";
import { Bot, User, CheckCircle, Loader2 } from "lucide-react";

export function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ${
          isUser
            ? "bg-indigo-100"
            : "bg-gradient-to-br from-slate-100 to-slate-50"
        }`}
      >
        {isUser ? (
          <User size={16} className="text-indigo-600" />
        ) : (
          <Bot size={16} className="text-slate-600" />
        )}
      </div>
      <div className={`max-w-[80%] ${isUser ? "text-right" : ""}`}>
        {!isUser && message.agent && (
          <span className="mb-1 inline-block rounded-lg bg-violet-50 px-2 py-0.5 text-[10px] font-semibold text-violet-600">
            {message.agent}
          </span>
        )}
        {message.tools && message.tools.length > 0 && (
          <div className="mb-2 flex flex-wrap gap-1">
            {message.tools.map((tool, i) => (
              <span
                key={i}
                className={`inline-flex items-center gap-1 rounded-lg px-2 py-0.5 text-[10px] font-medium ${
                  tool.done
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-amber-50 text-amber-700"
                }`}
              >
                {tool.done ? (
                  <CheckCircle size={10} />
                ) : (
                  <Loader2 size={10} className="animate-spin" />
                )}
                {tool.name}
              </span>
            ))}
          </div>
        )}
        <div
          className={`inline-block rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-indigo-600 text-white"
              : "bg-slate-50 text-slate-800 ring-1 ring-inset ring-slate-100"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm prose-slate max-w-none">
              <ReactMarkdown>{message.content || "\u200B"}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
