import { apiJson } from "./client";
import type { SiteStats } from "../types";

export function getSiteStats(): Promise<SiteStats> {
  return apiJson<SiteStats>("/site/stats");
}
