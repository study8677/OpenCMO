import { useQuery } from "@tanstack/react-query";
import { getTask } from "../api/tasks";

export function useTaskPoll(taskId: string | null) {
  return useQuery({
    queryKey: ["task", taskId],
    queryFn: () => getTask(taskId!),
    enabled: !!taskId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status === "completed" || status === "failed") return false;
      return 2000;
    },
  });
}
