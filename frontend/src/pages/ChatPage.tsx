import { useChat } from "../hooks/useChat";
import { ChatContainer } from "../components/chat/ChatContainer";
import { ChatSidebar } from "../components/chat/ChatSidebar";
import { LoadingSpinner } from "../components/common/LoadingSpinner";

export function ChatPage() {
  const chat = useChat();

  if (!chat.sessionReady) return <LoadingSpinner />;

  return (
    <div className="flex h-[calc(100vh-7rem)] gap-4">
      <ChatSidebar
        sessions={chat.sessions}
        activeSessionId={chat.sessionId}
        onSelect={chat.loadSession}
        onDelete={chat.removeSession}
        onNewChat={chat.resetChat}
      />
      <div className="flex-1 min-w-0">
        <ChatContainer
          messages={chat.messages}
          isStreaming={chat.isStreaming}
          currentAgent={chat.currentAgent}
          sendMessage={chat.sendMessage}
          hasMessages={chat.messages.length > 0}
        />
      </div>
    </div>
  );
}
