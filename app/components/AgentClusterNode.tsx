"use client";

/**
 * AgentClusterNode — A small node representing an agent in the whiteboard.
 * Content nodes discovered by this agent connect to it via edges.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Bot } from "lucide-react";

const MONO = "'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace";

export const AgentClusterNode = memo(function AgentClusterNode({ data }: NodeProps) {
  const { agentName, agentColor, count } = data as Record<string, unknown>;

  return (
    <div
      style={{
        padding: "6px 12px",
        borderRadius: 3,
        background: `${agentColor as string}08`,
        border: `1px solid ${agentColor as string}25`,
        fontFamily: MONO,
        display: "flex",
        alignItems: "center",
        gap: 6,
        cursor: "grab",
        minWidth: 100,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{
          width: 5,
          height: 5,
          background: agentColor as string,
          border: "1px solid #0a0c14",
          borderRadius: "50%",
        }}
      />

      <div
        style={{
          width: 18,
          height: 18,
          borderRadius: 2,
          background: `${agentColor as string}15`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
        }}
      >
        <Bot size={10} style={{ color: agentColor as string }} />
      </div>

      <div>
        <div
          style={{
            fontSize: 9,
            fontWeight: 700,
            color: agentColor as string,
            letterSpacing: 1,
            textTransform: "uppercase",
            lineHeight: "12px",
          }}
        >
          {agentName as string}
        </div>
        <div
          style={{
            fontSize: 8,
            color: "#445",
            lineHeight: "10px",
          }}
        >
          {count as number} item{(count as number) !== 1 ? "s" : ""} found
        </div>
      </div>
    </div>
  );
});
