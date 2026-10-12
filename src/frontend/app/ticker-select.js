"use client";

import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import styles from "./ticker-select.module.css";

export default function TickerSelect({ tickers, value, onChange, disabled }) {
  const options = ["", ...tickers];
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const containerRef = useRef(null);
  const buttonRef = useRef(null);
  const listRef = useRef(null);
  const typedRef = useRef({ text: "", time: 0 });
  const listId = useId();

  useEffect(() => {
    if (disabled) setOpen(false);
  }, [disabled]);

  useEffect(() => {
    if (!open) return;

    function closeOutside(event) {
      if (!containerRef.current.contains(event.target)) setOpen(false);
    }

    document.addEventListener("pointerdown", closeOutside);
    return () => document.removeEventListener("pointerdown", closeOutside);
  }, [open]);

  useLayoutEffect(() => {
    if (!open) return;

    const list = listRef.current;
    const option = list?.children[activeIndex];
    if (!option) return;

    // Scroll only the list, keeping the control and the page in place.
    const bottom = option.offsetTop + option.offsetHeight;
    if (option.offsetTop < list.scrollTop) {
      list.scrollTop = option.offsetTop;
    } else if (bottom > list.scrollTop + list.clientHeight) {
      list.scrollTop = bottom - list.clientHeight;
    }
  }, [open, activeIndex]);

  function showList(fallbackIndex = 0) {
    const selectedIndex = options.indexOf(value);
    setActiveIndex(selectedIndex < 0 ? fallbackIndex : selectedIndex);
    typedRef.current = { text: "", time: 0 };
    setOpen(true);
  }

  function selectTicker(index) {
    if (options[index] === undefined) return;
    onChange(options[index]);
    setOpen(false);
    buttonRef.current.focus({ preventScroll: true });
  }

  function handleKeyDown(event) {
    if (event.key === "Escape" || event.key === "Tab") {
      if (open && event.key === "Escape") event.preventDefault();
      setOpen(false);
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (open) selectTicker(activeIndex);
      else showList();
      return;
    }

    if (["ArrowDown", "ArrowUp", "Home", "End", "PageDown", "PageUp"].includes(event.key)) {
      event.preventDefault();
      typedRef.current = { text: "", time: 0 };
      const last = options.length - 1;

      if (event.key === "Home" || event.key === "End") {
        setActiveIndex(event.key === "Home" ? 0 : last);
        setOpen(true);
      } else if (!open) {
        showList(event.key === "ArrowUp" ? last : 0);
      } else {
        const pageSize = Math.max(1, Math.floor(
          listRef.current.clientHeight / listRef.current.children[0].offsetHeight
        ));
        const step = event.key.startsWith("Page") ? pageSize : 1;
        const direction = event.key.endsWith("Down") ? 1 : -1;
        setActiveIndex((index) => Math.max(0, Math.min(last, index + step * direction)));
      }
      return;
    }

    if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
      event.preventDefault();
      const now = Date.now();
      const previous = now - typedRef.current.time < 700 ? typedRef.current.text : "";
      const text = previous + event.key.toUpperCase();
      typedRef.current = { text, time: now };

      // Repeating a letter cycles through matching tickers.
      const prefix = [...text].every((letter) => letter === text[0]) ? text[0] : text;
      const start = prefix.length === 1 && open ? activeIndex + 1 : 0;
      for (let offset = 0; offset < options.length; offset += 1) {
        const index = (start + offset) % options.length;
        if ((options[index] || "Ticker").toUpperCase().startsWith(prefix)) {
          setActiveIndex(index);
          setOpen(true);
          break;
        }
      }
    }
  }

  return (
    <div ref={containerRef} className={styles.container}>
      <button
        ref={buttonRef}
        type="button"
        role="combobox"
        aria-label="Ticker"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={listId}
        aria-activedescendant={open ? `${listId}-${activeIndex}` : undefined}
        disabled={disabled}
        className={styles.trigger}
        onClick={() => open ? setOpen(false) : showList()}
        onKeyDown={handleKeyDown}
      >
        {value || "Ticker"}
        <span aria-hidden="true" className={styles.arrow}>▾</span>
      </button>
      {open && (
        <div
          ref={listRef}
          id={listId}
          role="listbox"
          aria-label="Tickers"
          className={styles.list}
        >
          {options.map((ticker, index) => (
            <div
              key={ticker}
              id={`${listId}-${index}`}
              role="option"
              aria-selected={ticker === value}
              className={`${styles.option} ${index === activeIndex ? styles.active : ""}`}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => selectTicker(index)}
            >
              {ticker || "Ticker"}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
