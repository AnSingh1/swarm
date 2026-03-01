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
      v.literal("reassigning")
    ),
    current_url: v.string(),
    profile_id: v.string(),
  }).index("by_agent_id", ["agent_id"]),
  
  discoveries: defineTable({
    video_url: v.string(),
    thumbnail: v.string(),
    found_by_agent_id: v.number(),
  }),
});
