"use client";

import { useEffect, useRef } from "react";
import controls from "../shared/controls.module.css";
import styles from "./delete-stock-dialog.module.css";

export default function DeleteStockDialog({ ticker, returnFocusRef, onCancel, onConfirm }) {
  const cancelButtonRef = useRef(null);

  useEffect(() => {
    const previousFocus = returnFocusRef.current;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    cancelButtonRef.current?.focus();

    return () => {
      document.body.style.overflow = previousOverflow;
      if (previousFocus?.isConnected && !previousFocus.matches(":disabled")) {
        previousFocus.focus();
      } else {
        document.getElementById("tab-stock-details")?.focus();
      }
    };
  }, [returnFocusRef]);

  return (
    <div className={styles.confirmationOverlay}>
      <div
        className={styles.confirmationDialog}
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="delete-confirmation-title"
        aria-describedby="delete-confirmation-description"
        onKeyDown={(event) => {
          if (event.key === "Tab") {
            const buttons = event.currentTarget.querySelectorAll("button");
            const first = buttons[0];
            const last = buttons[buttons.length - 1];
            if (event.shiftKey && document.activeElement === first) {
              event.preventDefault();
              last.focus();
            } else if (!event.shiftKey && document.activeElement === last) {
              event.preventDefault();
              first.focus();
            }
          }
        }}
      >
        <h2 id="delete-confirmation-title">Are you sure?</h2>
        <p id="delete-confirmation-description">
          This will delete <strong>{ticker}</strong>.
        </p>
        <div className={styles.confirmationActions}>
          <button
            ref={cancelButtonRef}
            type="button"
            className={`${controls.button} ${controls.secondary}`}
            onClick={onCancel}
          >
            Cancel
          </button>
          <button type="button" className={`${controls.button} ${controls.danger}`} onClick={onConfirm}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}
