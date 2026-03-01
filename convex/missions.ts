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
    liveUrl2: v.optional(v.string()),
    liveUrl3: v.optional(v.string()),
    sessionId: v.string(),
    shareUrl: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const update: any = {
      liveUrl: args.liveUrl,
      sessionId: args.sessionId,
    };
    if (args.liveUrl2) update.liveUrl2 = args.liveUrl2;
    if (args.liveUrl3) update.liveUrl3 = args.liveUrl3;
    if (args.shareUrl) update.shareUrl = args.shareUrl;
    
    await ctx.db.patch(args.missionId, update);
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
