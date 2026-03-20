import { ExternalLink } from "lucide-react";
import type { Project } from "../../types";

export function ProjectHeader({ project }: { project: Project }) {
  return (
    <div className="mb-4">
      <h1 className="text-2xl font-bold">{project.brand_name}</h1>
      <a
        href={project.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
      >
        {project.url} <ExternalLink size={12} />
      </a>
      <span className="ml-3 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
        {project.category}
      </span>
    </div>
  );
}
