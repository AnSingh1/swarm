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
    liveUrl4: v.optional(v.string()),
    liveUrl5: v.optional(v.string()),
    liveUrl6: v.optional(v.string()),
    liveUrl7: v.optional(v.string()),
    liveUrl8: v.optional(v.string()),
    liveUrl9: v.optional(v.string()),
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
    if (args.liveUrl4) update.liveUrl4 = args.liveUrl4;
    if (args.liveUrl5) update.liveUrl5 = args.liveUrl5;
    if (args.liveUrl6) update.liveUrl6 = args.liveUrl6;
    if (args.liveUrl7) update.liveUrl7 = args.liveUrl7;
    if (args.liveUrl8) update.liveUrl8 = args.liveUrl8;
    if (args.liveUrl9) update.liveUrl9 = args.liveUrl9;
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
