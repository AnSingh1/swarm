import { mutation } from "./_generated/server";

export const deleteAllMissions = mutation({
  args: {},
  handler: async (ctx) => {
    const missions = await ctx.db.query("missions").collect();
    for (const mission of missions) {
      await ctx.db.delete(mission._id);
    }
    return `Deleted ${missions.length} missions`;
  },
});

export const deleteAllAgents = mutation({
  args: {},
  handler: async (ctx) => {
    const agents = await ctx.db.query("agents").collect();
    for (const agent of agents) {
      await ctx.db.delete(agent._id);
    }
    return `Deleted ${agents.length} agents`;
  },
});

export const deleteAllDiscoveries = mutation({
  args: {},
  handler: async (ctx) => {
    const discoveries = await ctx.db.query("discoveries").collect();
    for (const discovery of discoveries) {
      await ctx.db.delete(discovery._id);
    }
    return `Deleted ${discoveries.length} discoveries`;
  },
});

export const deleteAllLivestreams = mutation({
  args: {},
  handler: async (ctx) => {
    const livestreams = await ctx.db.query("livestream").collect();
    for (const livestream of livestreams) {
      await ctx.db.delete(livestream._id);
    }
    return `Deleted ${livestreams.length} livestream frames`;
  },
});

export const deleteAllLogs = mutation({
  args: {},
  handler: async (ctx) => {
    const logs = await ctx.db.query("logs").collect();
    for (const log of logs) {
      await ctx.db.delete(log._id);
    }
    return `Deleted ${logs.length} logs`;
  },
});

export const deleteAllControlCommands = mutation({
  args: {},
  handler: async (ctx) => {
    const commands = await ctx.db.query("control").collect();
    for (const command of commands) {
      await ctx.db.delete(command._id);
    }
    return `Deleted ${commands.length} control commands`;
  },
});

/**
 * Reset everything - delete all data
 * NOTE: We don't send stop_all command here because:
 * 1. If there's no running orchestrator, the command will linger and stop the NEXT mission
 * 2. The orchestrator should handle cleanup via the handleStopAll UI button, not reset
 */
export const resetAll = mutation({
  args: {},
  handler: async (ctx) => {
    // Delete all data including any pending stop commands
    const missions = await ctx.db.query("missions").collect();
    const agents = await ctx.db.query("agents").collect();
    const discoveries = await ctx.db.query("discoveries").collect();
    const logs = await ctx.db.query("logs").collect();
    const livestreams = await ctx.db.query("livestream").collect();
    const commands = await ctx.db.query("control").collect();
    
    for (const mission of missions) await ctx.db.delete(mission._id);
    for (const agent of agents) await ctx.db.delete(agent._id);
    for (const discovery of discoveries) await ctx.db.delete(discovery._id);
    for (const log of logs) await ctx.db.delete(log._id);
    for (const livestream of livestreams) await ctx.db.delete(livestream._id);
    for (const command of commands) await ctx.db.delete(command._id);
    
    // DO NOT insert stop_all - it causes issues with new missions
    // If user wants to stop running sessions, they should use Stop All button first
    
    return {
      missions: missions.length,
      agents: agents.length,
      discoveries: discoveries.length,
      logs: logs.length,
      livestreams: livestreams.length,
      commands: commands.length,
    };
  },
});
