import { motion, type Transition } from "framer-motion";
import type { ReactNode } from "react";

interface AnimatedPageProps {
  children: ReactNode;
  className?: string;
}

const enterTransition: Transition = {
  duration: 0.4,
  ease: [0.25, 0.46, 0.45, 0.94],
};

const exitTransition: Transition = {
  duration: 0.2,
  ease: [0.55, 0.06, 0.68, 0.19],
};

/**
 * Wrap a page component with smooth enter/exit animations.
 */
export function AnimatedPage({ children, className = "" }: AnimatedPageProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0, transition: enterTransition }}
      exit={{ opacity: 0, y: -8, transition: exitTransition }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
