"use client";

import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "framer-motion";

interface AnimatedNumberProps {
  value: number;
  prefix?: string;
  suffix?: string;
}

const STEP_MS = 16;
const DURATION_MS = 900;

export function AnimatedNumber({
  value,
  prefix = "",
  suffix = "",
}: AnimatedNumberProps) {
  const prefersReducedMotion = useReducedMotion();
  const [display, setDisplay] = useState(prefersReducedMotion ? value : 0);

  useEffect(() => {
    if (prefersReducedMotion) {
      // Skip the count-up entirely and jump straight to the final
      // value - this is the reduced-motion fallback, not a render loop.
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDisplay(value);
      return;
    }

    // setTimeout rather than requestAnimationFrame: rAF can be
    // suspended entirely while the tab/pane isn't actively
    // compositing (e.g. backgrounded), which would leave this stuck
    // at 0 indefinitely. setTimeout still fires (throttled) there.
    const start = Date.now();
    let timer: ReturnType<typeof setTimeout>;

    const tick = () => {
      const progress = Math.min((Date.now() - start) / DURATION_MS, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(eased * value));

      if (progress < 1) {
        timer = setTimeout(tick, STEP_MS);
      }
    };

    tick();
    return () => clearTimeout(timer);
  }, [value, prefersReducedMotion]);

  return (
    <motion.span>
      {prefix}
      {display}
      {suffix}
    </motion.span>
  );
}
