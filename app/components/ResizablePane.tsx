"use client";

/**
 * ResizablePane — A horizontal split layout with a draggable divider.
 * Left pane width is controlled by dragging the handle.
 */

import { useState, useCallback, useRef, useEffect, type ReactNode } from "react";

interface ResizablePaneProps {
  left: ReactNode;
  right: ReactNode;
  defaultWidth?: number;
  minWidth?: number;
  maxWidth?: number;
}

export function ResizablePane({
  left,
  right,
  defaultWidth = 480,
  minWidth = 280,
  maxWidth = 900,
}: ResizablePaneProps) {
  const [width, setWidth] = useState(defaultWidth);
  const isDragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      isDragging.current = true;
      startX.current = e.clientX;
      startWidth.current = width;
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    },
    [width]
  );

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDragging.current) return;
      const delta = e.clientX - startX.current;
      const next = Math.min(maxWidth, Math.max(minWidth, startWidth.current + delta));
      setWidth(next);
    };

    const handleMouseUp = () => {
      if (!isDragging.current) return;
      isDragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };

    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [minWidth, maxWidth]);

  return (
    <div style={{ display: "flex", width: "100%", height: "100%", overflow: "hidden" }}>
      {/* Left pane */}
      <div
        style={{
          width,
          flexShrink: 0,
          height: "100%",
          overflow: "hidden",
          position: "relative",
        }}
      >
        {left}
      </div>

      {/* Drag handle */}
      <div
        onMouseDown={handleMouseDown}
        style={{
          width: 6,
          flexShrink: 0,
          cursor: "col-resize",
          position: "relative",
          zIndex: 20,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div
          style={{
            width: 1,
            height: "100%",
            background: "#141822",
            position: "absolute",
          }}
        />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 3,
            zIndex: 1,
          }}
        >
          {[0, 1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                width: 3,
                height: 3,
                borderRadius: "50%",
                background: "#2a2f3e",
              }}
            />
          ))}
        </div>
        <div
          style={{
            position: "absolute",
            inset: "-0 -4px",
            cursor: "col-resize",
          }}
        />
      </div>

      {/* Right pane */}
      <div
        style={{
          flex: 1,
          height: "100%",
          overflow: "hidden",
          position: "relative",
          minWidth: 0,
        }}
      >
        {right}
      </div>
    </div>
  );
}
