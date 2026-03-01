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

export const updateMissionLivestream = mutation({
  args: {
    missionId: v.id("missions"),
    liveUrl: v.string(),
    sessionId: v.string(),
    shareUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.missionId, {
      liveUrl: args.liveUrl,
      sessionId: args.sessionId,
      shareUrl: args.shareUrl,
    });
  },
});

export const deleteAllMissions = mutation({
  args: {},
  handler: async (ctx) => {
    const missions = await ctx.db.query("missions").collect();
    for (const mission of missions) {
      await ctx.db.delete(mission._id);
    }
    return { deleted: missions.length };
  },
});
