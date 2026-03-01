import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const logDiscovery = mutation({
  args: {
    video_url: v.string(),
    thumbnail: v.string(),
    found_by_agent_id: v.number(),
    keywords: v.optional(v.string()),  // 2-3 defining keywords
    likes: v.optional(v.number()),
    views: v.optional(v.number()),
    comments: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const discoveryId = await ctx.db.insert("discoveries", {
      video_url: args.video_url,
      thumbnail: args.thumbnail,
      found_by_agent_id: args.found_by_agent_id,
      keywords: args.keywords,
      likes: args.likes,
      views: args.views,
      comments: args.comments,
    });
    return discoveryId;
  },
});

export const getDiscoveries = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("discoveries").order("desc").collect();
  },
});

export const deleteAllDiscoveries = mutation({
  args: {},
  handler: async (ctx) => {
    const discoveries = await ctx.db.query("discoveries").collect();
    for (const discovery of discoveries) {
      await ctx.db.delete(discovery._id);
    }
    return { deleted: discoveries.length };
  },
});

// Get the most recent discovery (for Blackboard Architecture)
export const getLatestDiscovery = query({
  args: {},
  handler: async (ctx) => {
    const discoveries = await ctx.db.query("discoveries").order("desc").take(1);
    return discoveries[0] ?? null;
  },
});
