import { useQuery } from "@tanstack/react-query";
import { getChatContext } from "../api/chatContext";
import type { ChatProjectContext } from "../api/chatContext";

export type { ChatProjectContext };

export function useChatContext(projectId: number | null) {
  return useQuery<ChatProjectContext>({
    queryKey: ["chat-context", projectId],
    queryFn: () => getChatContext(projectId!),
    enabled: projectId != null,
    staleTime: 60_000,
    refetchOnWindowFocus: false,
  });
}
