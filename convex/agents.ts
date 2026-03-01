import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const updateAgentState = mutation({
  args: {
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
    profile_id: v.optional(v.string()),
    energy: v.optional(v.number()),  // Optional energy update
  },
  handler: async (ctx, args) => {
    // Check if agent exists
    const existingAgent = await ctx.db
      .query("agents")
      .withIndex("by_agent_id", (q) => q.eq("agent_id", args.agent_id))
      .first();

    if (existingAgent) {
      // Update existing agent
      await ctx.db.patch(existingAgent._id, {
        status: args.status,
        current_url: args.current_url,
        ...(args.profile_id !== undefined && { profile_id: args.profile_id }),
        ...(args.energy !== undefined && { energy: args.energy }),
      });
      return existingAgent._id;
    } else {
      // Create new agent with default energy of 100
      const agentId = await ctx.db.insert("agents", {
        agent_id: args.agent_id,
        status: args.status,
        current_url: args.current_url,
        profile_id: args.profile_id ?? "",
        energy: args.energy ?? 100,  // Default energy
      });
      return agentId;
    }
  },
});

export const getAllAgents = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("agents").collect();
  },
});

export const deleteAllAgents = mutation({
  args: {},
  handler: async (ctx) => {
    const agents = await ctx.db.query("agents").collect();
    for (const agent of agents) {
      await ctx.db.delete(agent._id);
    }
    return { deleted: agents.length };
  },
});

// Get all weak agents (energy <= 0) for swarm reassignment
export const getWeakAgents = query({
  args: {},
  handler: async (ctx) => {
    const agents = await ctx.db.query("agents").collect();
    return agents.filter(agent => agent.energy <= 0);
  },
});

// Update agent energy (for risk/reward system)
export const updateAgentEnergy = mutation({
  args: {
    agent_id: v.number(),
    energy: v.number(),
  },
  handler: async (ctx, args) => {
    const agent = await ctx.db
      .query("agents")
      .withIndex("by_agent_id", (q) => q.eq("agent_id", args.agent_id))
      .first();
    
    if (agent) {
      await ctx.db.patch(agent._id, { energy: args.energy });
      return agent._id;
    }
    return null;
  },
});
