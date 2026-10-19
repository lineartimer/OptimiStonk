"use client";

import { useEffect, useId, useRef, useState } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import markdown from "./markdown.module.css";
import styles from "./reference-preview.module.css";

export default function ReferencePreview({ title, text }) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const previewRef = useRef(null);
  const previewId = useId();

  useEffect(() => {
    if (expanded) return;

    const preview = previewRef.current;
    const updateOverflow = () => {
      setCanExpand(preview.scrollHeight > preview.clientHeight);
    };
    const observer = new ResizeObserver(updateOverflow);

    updateOverflow();
    observer.observe(preview);
    return () => observer.disconnect();
  }, [text, expanded]);

  return (
    <>
      <h3>
        {title}{" "}
        {canExpand && (
          <button
            type="button"
            className={styles.referenceToggle}
            aria-label={`${expanded ? "Collapse" : "Expand"} ${title}`}
            aria-expanded={expanded}
            aria-controls={previewId}
            onClick={() => setExpanded((value) => !value)}
          >
            {expanded ? "−" : "+"}
          </button>
        )}
      </h3>
      <div
        id={previewId}
        ref={previewRef}
        className={`${markdown.markdown} ${styles.referencePreview} ${expanded ? "" : styles.referencePreviewCollapsed}`}
      >
        <Markdown remarkPlugins={[remarkGfm]}>{text}</Markdown>
      </div>
    </>
  );
}
