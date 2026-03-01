import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const logDiscovery = mutation({
  args: {
    video_url: v.string(),
    thumbnail: v.string(),
    found_by_agent_id: v.number(),
  },
  handler: async (ctx, args) => {
    const discoveryId = await ctx.db.insert("discoveries", {
      video_url: args.video_url,
      thumbnail: args.thumbnail,
      found_by_agent_id: args.found_by_agent_id,
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
