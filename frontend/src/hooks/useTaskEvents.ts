import { useEffect, useRef, useState, useCallback } from "react";

export interface TaskEvent {
  type: "progress" | "done" | "error";
  stage?: string;
  status?: string;
  agent?: string;
  summary?: string;
  detail?: string;
  /* done-specific fields */
  run_id?: number;
  findings_count?: number;
  recommendations_count?: number;
  error?: string | null;
  message?: string;
}

interface UseTaskEventsOptions {
  /** Called when the task finishes (status == done). */
  onDone?: (event: TaskEvent) => void;
  /** Enable/disable the connection. Defaults to true. */
  enabled?: boolean;
}

/**
 * Subscribe to real-time task progress via Server-Sent Events.
 *
 * Returns an array of received events and a boolean indicating whether
 * the connection is still active.
 */
export function useTaskEvents(
  taskId: string | null | undefined,
  options: UseTaskEventsOptions = {},
) {
  const { onDone, enabled = true } = options;
  const [events, setEvents] = useState<TaskEvent[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  const reset = useCallback(() => {
    setEvents([]);
    setIsStreaming(false);
  }, []);

  useEffect(() => {
    if (!taskId || !enabled) {
      return;
    }

    const es = new EventSource(`/api/v1/tasks/${taskId}/events`);
    eventSourceRef.current = es;
    setIsStreaming(true);
    setEvents([]);

    es.onmessage = (msg) => {
      try {
        const event: TaskEvent = JSON.parse(msg.data);
        setEvents((prev) => [...prev, event]);

        if (event.type === "done" || event.type === "error") {
          setIsStreaming(false);
          es.close();
          onDoneRef.current?.(event);
        }
      } catch {
        // Ignore malformed events
      }
    };

    es.onerror = () => {
      setIsStreaming(false);
      es.close();
    };

    return () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, [taskId, enabled]);

  return { events, isStreaming, reset };
}
