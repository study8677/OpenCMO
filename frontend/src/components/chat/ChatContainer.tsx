import type { ChatMessage } from "../../types";
import { MessageList } from "./MessageList";
import { ChatInput } from "./ChatInput";
import { AgentGrid } from "./AgentGrid";
import { useI18n } from "../../i18n";

export function ChatContainer({
  messages,
  isStreaming,
  currentAgent,
  sendMessage,
  hasMessages,
}: {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentAgent: string;
  sendMessage: (content: string) => void;
  hasMessages: boolean;
}) {
  const { t } = useI18n();

  return (
    <div className="flex flex-1 min-h-0 flex-col">
      {/* Agent badge */}
      <div className="mb-3">
        <p className="text-xs text-slate-400">
          {t("chat.agent", { name: currentAgent })}
        </p>
      </div>

      {/* When no messages: show agent grid as quick-start */}
      {!hasMessages ? (
        <div className="flex flex-1 flex-col mx-auto w-full max-w-3xl">
          <div className="flex-1 overflow-y-auto p-2">
            <AgentGrid onSelect={(prompt) => sendMessage(prompt)} />
          </div>
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
        </div>
      ) : (
        <>
          <MessageList messages={messages} isStreaming={isStreaming} />
          <ChatInput onSend={sendMessage} disabled={isStreaming} />
        </>
      )}
    </div>
  );
}
