import { useState, useCallback, useEffect } from "react";
import {
  createSession,
  streamChat,
  listSessions,
  getSessionMessages,
  deleteSession,
} from "../api/chat";
import type { ChatMessage, ChatEvent, ToolStatus, ChatSessionSummary } from "../types";

let msgIdCounter = 0;
function nextId() {
  return `msg-${++msgIdCounter}`;
}

export function useChat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentAgent, setCurrentAgent] = useState("CMO Agent");

  const refreshSessions = useCallback(async () => {
    try {
      const list = await listSessions();
      setSessions(list);
    } catch {
      // ignore
    }
  }, []);

  // Load sessions + create initial session on mount
  useEffect(() => {
    refreshSessions();
    createSession().then(setSessionId).catch(console.error);
  }, [refreshSessions]);

  const loadSession = useCallback(
    async (id: string) => {
      if (isStreaming) return;
      try {
        const msgs = await getSessionMessages(id);
        setSessionId(id);
        setMessages(
          msgs.map((m) => ({
            id: nextId(),
            role: m.role as "user" | "assistant",
            content: m.content,
          })),
        );
        setCurrentAgent("CMO Agent");
      } catch {
        // session might be stale
      }
    },
    [isStreaming],
  );

  const sendMessage = useCallback(
    async (content: string) => {
      if (!sessionId || isStreaming || !content.trim()) return;

      const userMsg: ChatMessage = {
        id: nextId(),
        role: "user",
        content: content.trim(),
      };
      const assistantMsg: ChatMessage = {
        id: nextId(),
        role: "assistant",
        content: "",
        agent: currentAgent,
        tools: [],
      };

      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setIsStreaming(true);

      try {
        for await (const event of streamChat(sessionId, content.trim())) {
          handleEvent(event, assistantMsg.id);
        }
        // Refresh session list after completion (title may have changed)
        refreshSessions();
      } catch (err) {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantMsg.id
              ? {
                  ...m,
                  content:
                    m.content ||
                    `Error: ${err instanceof Error ? err.message : "Unknown error"}`,
                }
              : m,
          ),
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [sessionId, isStreaming, currentAgent, refreshSessions],
  );

  const handleEvent = useCallback(
    (event: ChatEvent, msgId: string) => {
      switch (event.type) {
        case "delta":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, content: m.content + (event.content ?? "") }
                : m,
            ),
          );
          break;
        case "agent":
          setCurrentAgent(event.name ?? "CMO Agent");
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId ? { ...m, agent: event.name } : m,
            ),
          );
          break;
        case "tool_call":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    tools: [
                      ...(m.tools ?? []),
                      { name: event.name ?? "tool", done: false },
                    ],
                  }
                : m,
            ),
          );
          break;
        case "tool_done":
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msgId) return m;
              const tools = [...(m.tools ?? [])];
              const last = tools.findLast((t: ToolStatus) => !t.done);
              if (last) last.done = true;
              return { ...m, tools };
            }),
          );
          break;
        case "handoff":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? {
                    ...m,
                    tools: [
                      ...(m.tools ?? []),
                      {
                        name: `Handing off to ${event.target}`,
                        done: false,
                      },
                    ],
                  }
                : m,
            ),
          );
          break;
        case "handoff_done":
          setMessages((prev) =>
            prev.map((m) => {
              if (m.id !== msgId) return m;
              const tools = [...(m.tools ?? [])];
              const last = tools.findLast((t: ToolStatus) => !t.done);
              if (last) last.done = true;
              return { ...m, tools };
            }),
          );
          break;
        case "done":
          if (event.agent_name) setCurrentAgent(event.agent_name);
          break;
        case "error":
          setMessages((prev) =>
            prev.map((m) =>
              m.id === msgId
                ? { ...m, content: m.content || `Error: ${event.message}` }
                : m,
            ),
          );
          break;
      }
    },
    [],
  );

  const resetChat = useCallback(async () => {
    setMessages([]);
    setCurrentAgent("CMO Agent");
    try {
      const newId = await createSession();
      setSessionId(newId);
    } catch (e) {
      console.error("Failed to create new session", e);
    }
  }, []);

  const removeSession = useCallback(
    async (id: string) => {
      try {
        await deleteSession(id);
        setSessions((prev) => prev.filter((s) => s.id !== id));
        // If deleted session is the active one, reset
        if (id === sessionId) {
          await resetChat();
        }
      } catch {
        // ignore
      }
    },
    [sessionId, resetChat],
  );

  return {
    messages,
    isStreaming,
    currentAgent,
    sendMessage,
    resetChat,
    sessionReady: !!sessionId,
    sessionId,
    sessions,
    loadSession,
    removeSession,
  };
}
