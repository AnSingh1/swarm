import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  missions: defineTable({
    prompt: v.string(),
    status: v.union(v.literal("active"), v.literal("completed")),
    liveUrl: v.optional(v.string()),
    liveUrl2: v.optional(v.string()),
    liveUrl3: v.optional(v.string()),
    liveUrl4: v.optional(v.string()),
    liveUrl5: v.optional(v.string()),
    liveUrl6: v.optional(v.string()),
    liveUrl7: v.optional(v.string()),
    liveUrl8: v.optional(v.string()),
    liveUrl9: v.optional(v.string()),
    sessionId: v.optional(v.string()),
    shareUrl: v.optional(v.string()),
  }),
  
  agents: defineTable({
    agent_id: v.number(),
    status: v.union(
      v.literal("idle"),
      v.literal("searching"),
      v.literal("found_trend"),
      v.literal("weak"),
      v.literal("reassigning"),
      v.literal("exploiting")
    ),
    current_url: v.string(),
    profile_id: v.string(),
    energy: v.number(),  // Energy level (0-100) for risk/reward system
  }).index("by_agent_id", ["agent_id"]),
  
  discoveries: defineTable({
    video_url: v.string(),
    thumbnail: v.string(),
    found_by_agent_id: v.number(),
    keywords: v.optional(v.string()),  // 2-3 defining keywords extracted by LLM
  }),
  
  logs: defineTable({
    agent_id: v.number(),
    message: v.string(),
    type: v.union(
      v.literal("search"),        // Started searching for term
      v.literal("analysis"),      // Analyzing a video
      v.literal("likes"),         // Found likes count
      v.literal("discovery"),     // Made a discovery
      v.literal("energy_gain"),   // Energy increased
      v.literal("energy_loss"),   // Energy decreased
      v.literal("task_swap"),     // Swapped to exploitation mode
      v.literal("status"),        // Status change
      v.literal("error")          // Error occurred
    ),
    timestamp: v.number(),        // Unix timestamp
    metadata: v.optional(v.string()),  // JSON string for extra data
  }).index("by_agent_id", ["agent_id"])
    .index("by_timestamp", ["timestamp"]),
  
  control: defineTable({
    command: v.union(
      v.literal("stop_all"),      // Stop all sessions
      v.literal("restart"),        // Restart orchestrator
      v.literal("pause")           // Pause all agents
    ),
    status: v.union(
      v.literal("pending"),
      v.literal("processing"),
      v.literal("completed")
    ),
    timestamp: v.number(),
    metadata: v.optional(v.string()),
  }).index("by_status", ["status"])
    .index("by_timestamp", ["timestamp"]),
  
  signals: defineTable({
    fromAgent: v.number(),      // Source agent (0 = blackboard center)
    toAgent: v.number(),        // Target agent (0 = blackboard center)
    message: v.string(),        // Event message
    signalType: v.string(),     // Type of signal (log, discovery, etc)
    timestamp: v.number(),      // Unix timestamp
  }).index("by_timestamp", ["timestamp"]),
});
