"use client";

import { useEffect, useId, useRef, useState } from "react";
import styles from "./company-summary.module.css";

export default function CompanySummary({ text }) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const summaryRef = useRef(null);
  const summaryId = useId();

  useEffect(() => {
    if (expanded) return;

    const summary = summaryRef.current;
    const updateOverflow = () => {
      setCanExpand(summary.scrollHeight > summary.clientHeight);
    };
    const observer = new ResizeObserver(updateOverflow);

    updateOverflow();
    observer.observe(summary);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <>
      <p
        id={summaryId}
        ref={summaryRef}
        className={`${styles.summary} ${expanded ? "" : styles.summaryCollapsed}`}
      >
        {text}
      </p>
      {canExpand && (
        <button
          type="button"
          className={styles.summaryToggle}
          aria-expanded={expanded}
          aria-controls={summaryId}
          onClick={() => setExpanded((value) => !value)}
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}
    </>
  );
}
