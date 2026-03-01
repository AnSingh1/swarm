"use client";

/**
 * ContentNode — Custom React Flow node for a discovered content item.
 * Shows the thumbnail, video URL, and which agent found it.
 */

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  ExternalLink,
  Eye,
  Play,
} from "lucide-react";
import { getAgentById, PLATFORM_COLORS } from "../hooks/useAgentData";

const MONO = "'JetBrains Mono', 'SF Mono', 'Cascadia Code', monospace";

function getPlatformFromUrl(url: string): string {
  if (url.includes("tiktok")) return "tiktok";
  if (url.includes("youtube") || url.includes("youtu.be")) return "youtube";
  if (url.includes("twitter") || url.includes("x.com")) return "twitter";
  if (url.includes("instagram")) return "instagram";
  if (url.includes("linkedin")) return "linkedin";
  return "blog";
}

const PLATFORM_ICONS: Record<string, string> = {
  youtube: "YT",
  tiktok: "TK",
  twitter: "X",
  linkedin: "LI",
  instagram: "IG",
  blog: "BG",
  duckduckgo: "DDG",
};

function timeAgo(ts: number): string {
  const diff = Math.floor((Date.now() - ts * 1000) / 1000);
  if (diff < 5) return "just now";
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  return `${Math.floor(diff / 3600)}h ago`;
}

export const ContentNode = memo(function ContentNode({ data }: NodeProps) {
  const {
    video_url,
    thumbnail,
    found_by_agent_id,
    keywords,
    _creationTime,
  } = data as Record<string, unknown>;

  const agent = getAgentById(found_by_agent_id as number);
  const platform = getPlatformFromUrl(video_url as string || "");
  const platformColor = PLATFORM_COLORS[platform] || "#666";
  const isVideo = platform === "youtube" || platform === "tiktok" || platform === "instagram";

  return (
    <div
      style={{
        width: 270,
        background: "#0a0c14",
        border: "1px solid #141822",
        borderRadius: 3,
        overflow: "hidden",
        fontFamily: MONO,
        cursor: "grab",
        transition: "border-color 0.15s ease",
      }}
      onMouseEnter={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = platformColor + "60";
      }}
      onMouseLeave={(e) => {
        (e.currentTarget as HTMLElement).style.borderColor = "#141822";
      }}
    >
      <Handle
        type="source"
        position={Position.Right}
        style={{
          width: 5,
          height: 5,
          background: agent?.color || "#334",
          border: "1px solid #0a0c14",
          borderRadius: "50%",
        }}
      />
      <Handle
        type="target"
        position={Position.Left}
        style={{
          width: 5,
          height: 5,
          background: "#334",
          border: "1px solid #0a0c14",
          borderRadius: "50%",
        }}
      />

      {/* Thumbnail / Media preview */}
      <div
        style={{
          width: "100%",
          height: 120,
          position: "relative",
          overflow: "hidden",
          background: "#080a10",
          borderBottom: "1px solid #141822",
        }}
      >
        {thumbnail ? (
          <img
            src={thumbnail as string}
            alt="Content thumbnail"
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              display: "block",
              opacity: 0.85,
            }}
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
        ) : (
          <div
            style={{
              width: "100%",
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: `${platformColor}08`,
            }}
          >
            <Eye size={20} style={{ color: "#2a2f3e" }} />
          </div>
        )}

        {/* Platform badge */}
        <div
          style={{
            position: "absolute",
            top: 6,
            left: 6,
            padding: "2px 6px",
            borderRadius: 2,
            background: `${platformColor}20`,
            border: `1px solid ${platformColor}30`,
            fontSize: 8,
            fontWeight: 700,
            color: platformColor,
            letterSpacing: 1,
          }}
        >
          {PLATFORM_ICONS[platform] || platform.toUpperCase()}
        </div>

        {/* Video play overlay */}
        {isVideo && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.2)",
              opacity: 0,
              transition: "opacity 0.15s ease",
              cursor: "pointer",
            }}
            onMouseEnter={(e) => {
              (e.currentTarget as HTMLElement).style.opacity = "1";
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLElement).style.opacity = "0";
            }}
            onClick={() => window.open(video_url as string, '_blank')}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: "rgba(0,0,0,0.6)",
                border: "1px solid rgba(255,255,255,0.15)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <Play size={12} fill="white" style={{ color: "white", marginLeft: 1 }} />
            </div>
          </div>
        )}
      </div>

      {/* Content info */}
      <div style={{ padding: 10 }}>
        {/* Keywords */}
        {typeof keywords === 'string' && keywords.length > 0 && (
          <div
            style={{
              fontSize: 9,
              color: "#c8d0e0",
              marginBottom: 6,
              lineHeight: "14px",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {keywords}
          </div>
        )}

        {/* URL */}
        <a
          href={video_url as string}
          target="_blank"
          rel="noopener noreferrer"
          style={{
            fontSize: 8,
            color: platformColor,
            textDecoration: "none",
            display: "flex",
            alignItems: "center",
            gap: 4,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <ExternalLink size={8} />
          <span style={{ overflow: "hidden", textOverflow: "ellipsis" }}>
            {(video_url as string)?.replace(/^https?:\/\//, '').slice(0, 35)}...
          </span>
        </a>

        {/* Footer */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginTop: 8,
            paddingTop: 8,
            borderTop: "1px solid #141822",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
            }}
          >
            <div
              style={{
                width: 4,
                height: 4,
                borderRadius: "50%",
                background: agent?.color || "#666",
              }}
            />
            <span
              style={{
                fontSize: 8,
                color: agent?.color || "#666",
                fontWeight: 600,
                letterSpacing: 0.5,
              }}
            >
              {agent?.name || `Agent ${found_by_agent_id}`}
            </span>
          </div>
          {typeof _creationTime === 'number' && (
            <span style={{ fontSize: 7, color: "#445" }}>
              {timeAgo(_creationTime / 1000)}
            </span>
          )}
        </div>
      </div>
    </div>
  );
});
