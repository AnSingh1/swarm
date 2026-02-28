import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const createMission = mutation({
  args: {
    prompt: v.string(),
  },
  handler: async (ctx, args) => {
    const missionId = await ctx.db.insert("missions", {
      prompt: args.prompt,
      status: "active",
    });
    return missionId;
  },
});

export const getLatestMission = query({
  args: {},
  handler: async (ctx) => {
    const missions = await ctx.db.query("missions").order("desc").take(1);
    return missions[0] ?? null;
  },
});
