"use client";

/**
 * ContentWhiteboard — A React Flow canvas that shows discovered content.
 * Each piece of scraped content appears as a draggable node.
 */

import { useEffect, useMemo, useRef } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type Node,
  type Edge,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import { ContentNode } from "./ContentNode";
import { AgentClusterNode } from "./AgentClusterNode";
import { getAgentById, type DiscoveredContent } from "../hooks/useAgentData";

const nodeTypes: NodeTypes = {
  content: ContentNode,
  agentCluster: AgentClusterNode,
};

const NODE_W = 280;
const NODE_H = 220;
const GAP_X = 40;
const GAP_Y = 40;
const COLS = 3;
const ORIGIN_X = 80;
const ORIGIN_Y = 80;

interface ContentWhiteboardProps {
  content: DiscoveredContent[];
  isRunning: boolean;
}

export function ContentWhiteboard({ content, isRunning }: ContentWhiteboardProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const knownIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (content.length === 0) {
      knownIds.current.clear();
      setNodes([]);
      setEdges([]);
      return;
    }

    const newItems = content.filter((c) => !knownIds.current.has(c._id));
    if (newItems.length === 0 && nodes.length > 0) return;

    // Add all items to known set
    content.forEach((c) => knownIds.current.add(c._id));

    // Build content nodes with grid placement
    const contentNodes: Node[] = content.map((item, idx) => {
      const col = idx % COLS;
      const row = Math.floor(idx / COLS);
      return {
        id: item._id,
        type: "content",
        position: {
          x: ORIGIN_X + col * (NODE_W + GAP_X),
          y: ORIGIN_Y + row * (NODE_H + GAP_Y),
        },
        data: { ...item } as unknown as Record<string, unknown>,
      };
    });

    // Build agent cluster nodes
    const agentGroups = new Map<number, DiscoveredContent[]>();
    content.forEach((c) => {
      const list = agentGroups.get(c.found_by_agent_id) || [];
      list.push(c);
      agentGroups.set(c.found_by_agent_id, list);
    });

    const clusterNodes: Node[] = [];
    let clusterY = ORIGIN_Y;
    const clusterX = ORIGIN_X + COLS * (NODE_W + GAP_X) + 80;

    agentGroups.forEach((items, agentId) => {
      const agent = getAgentById(agentId);
      clusterNodes.push({
        id: `cluster-${agentId}`,
        type: "agentCluster",
        position: { x: clusterX, y: clusterY },
        data: {
          agentId,
          agentName: agent.name,
          agentColor: agent.color,
          count: items.length,
        } as unknown as Record<string, unknown>,
        draggable: true,
      });
      clusterY += 80;
    });

    setNodes([...contentNodes, ...clusterNodes]);

    // Build edges: content -> its agent cluster
    const newEdges: Edge[] = content.map((c) => {
      const agent = getAgentById(c.found_by_agent_id);
      return {
        id: `edge-${c._id}`,
        source: c._id,
        target: `cluster-${c.found_by_agent_id}`,
        type: "default",
        animated: true,
        style: {
          stroke: agent?.color || "#334",
          strokeWidth: 1,
          opacity: 0.25,
        },
      };
    });
    setEdges(newEdges);
  }, [content, setNodes, setEdges, nodes.length]);

  const rfStyle = useMemo(
    () => ({
      background: "#020408",
    }),
    []
  );

  const minimapStyle = useMemo(
    () => ({
      backgroundColor: "#080a10",
      maskColor: "rgba(0, 0, 0, 0.7)",
    }),
    []
  );

  return (
    <div style={{ width: "100%", height: "100%", position: "relative" }}>
      {/* Header bar */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          zIndex: 10,
          padding: "8px 12px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          background: "linear-gradient(180deg, #020408 0%, transparent 100%)",
          pointerEvents: "none",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: isRunning ? "#00f0ff" : "#334",
              boxShadow: isRunning ? "0 0 6px #00f0ff" : "none",
            }}
          />
          <span
            style={{
              fontSize: 9,
              fontWeight: 700,
              color: "#00f0ff",
              letterSpacing: 2,
              textTransform: "uppercase",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            Discoveries
          </span>
          <span
            style={{
              fontSize: 9,
              color: "#334",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {content.length} items
          </span>
        </div>
      </div>

      {/* Empty state */}
      {content.length === 0 && (
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            zIndex: 5,
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              border: "1px solid #141822",
              borderRadius: 3,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                width: 12,
                height: 12,
                border: "1px dashed #2a2f3e",
                borderRadius: 2,
              }}
            />
          </div>
          <span
            style={{
              fontSize: 10,
              color: "#334",
              letterSpacing: 1,
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            {isRunning ? "Agents are scanning..." : "Start a mission to discover content"}
          </span>
        </div>
      )}

      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        colorMode="dark"
        fitView
        fitViewOptions={{ padding: 0.2 }}
        style={rfStyle}
        proOptions={{ hideAttribution: true }}
        minZoom={0.15}
        maxZoom={2}
        defaultEdgeOptions={{
          type: "default",
          animated: true,
        }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={0.8}
          color="#141822"
        />
        <Controls
          showInteractive={false}
          style={{
            background: "#080a10",
            border: "1px solid #141822",
            borderRadius: 3,
          }}
        />
        <MiniMap
          style={minimapStyle}
          nodeColor={(n) => {
            if (n.type === "agentCluster") {
              return (n.data as { agentColor?: string })?.agentColor || "#334";
            }
            const agentId = (n.data as { found_by_agent_id?: number })?.found_by_agent_id;
            const agent = agentId ? getAgentById(agentId) : null;
            return agent?.color || "#445";
          }}
          pannable
          zoomable
        />
      </ReactFlow>
    </div>
  );
}
