import { ChevronDown, ChevronRight, FolderKanban } from "lucide-react";
import { useState, type ReactNode } from "react";
import type { Project } from "../types";

interface Props {
  project: Project;
  count: number;
  label: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export function ProjectDisclosure({
  project,
  count,
  label,
  children,
  defaultOpen = false,
}: Props) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <details
      className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900/50"
      open={open}
      onToggle={(event) => setOpen(event.currentTarget.open)}
    >
      <summary className="flex cursor-pointer list-none items-center gap-3 px-5 py-4 hover:bg-slate-800/50">
        {open ? (
          <ChevronDown size={17} className="text-cyan" />
        ) : (
          <ChevronRight size={17} className="text-slate-500" />
        )}
        <span className="rounded-lg bg-cyan/10 p-2 text-cyan">
          <FolderKanban size={17} />
        </span>
        <span className="min-w-0 flex-1">
          <span className="block truncate font-semibold text-white">
            {project.engagement_name}
          </span>
          <span className="block truncate text-xs text-slate-500">
            {project.client_name}
          </span>
        </span>
        <span className="rounded-full border border-slate-700 bg-slate-950 px-3 py-1 text-xs text-slate-400">
          {count} {label}
        </span>
      </summary>
      <div className="border-t border-slate-800">{children}</div>
    </details>
  );
}
