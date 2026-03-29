import { motion } from "framer-motion";

interface SkeletonCardProps {
  /** Number of skeleton cards to render. */
  count?: number;
}

function SingleCard() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="rounded-xl border border-slate-100 bg-white p-5 shadow-sm"
    >
      {/* Header skeleton */}
      <div className="flex items-center gap-3 mb-4">
        <div className="h-10 w-10 rounded-lg bg-slate-100 animate-pulse" />
        <div className="flex-1 space-y-2">
          <div className="h-4 w-3/5 rounded-md bg-slate-100 animate-pulse" />
          <div className="h-3 w-2/5 rounded-md bg-slate-50 animate-pulse" />
        </div>
      </div>

      {/* Metric row skeleton */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            className="rounded-lg bg-slate-50 p-3 space-y-2"
          >
            <div className="h-3 w-12 rounded bg-slate-100 animate-pulse" />
            <div
              className="h-5 w-16 rounded bg-slate-100 animate-pulse"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          </div>
        ))}
      </div>

      {/* Bottom bar skeleton */}
      <div className="flex justify-between items-center pt-3 border-t border-slate-50">
        <div className="h-3 w-24 rounded bg-slate-100 animate-pulse" />
        <div className="h-3 w-16 rounded bg-slate-100 animate-pulse" />
      </div>
    </motion.div>
  );
}

/**
 * Premium skeleton loading cards that match the ProjectCard layout.
 * Uses staggered animation delays for a polished shimmer effect.
 */
export function SkeletonCard({ count = 3 }: SkeletonCardProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            delay: i * 0.08,
            duration: 0.4,
            ease: [0.25, 0.46, 0.45, 0.94] as const,
          }}
        >
          <SingleCard />
        </motion.div>
      ))}
    </div>
  );
}
