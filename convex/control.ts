import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

/**
 * Send a control command (like stop_all)
 */
export const sendCommand = mutation({
  args: {
    command: v.union(
      v.literal("stop_all"),
      v.literal("restart"),
      v.literal("pause")
    ),
    metadata: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const commandId = await ctx.db.insert("control", {
      command: args.command,
      status: "pending",
      timestamp: Date.now(),
      metadata: args.metadata,
    });
    
    return commandId;
  },
});

/**
 * Get pending commands (for orchestrator to process)
 */
export const getPendingCommands = query({
  args: {},
  handler: async (ctx) => {
    const commands = await ctx.db
      .query("control")
      .withIndex("by_status", (q) => q.eq("status", "pending"))
      .order("asc")
      .collect();
    
    return commands;
  },
});

/**
 * Mark a command as processing
 */
export const markCommandProcessing = mutation({
  args: {
    commandId: v.id("control"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.commandId, {
      status: "processing",
    });
  },
});

/**
 * Update command status (generic)
 */
export const updateCommandStatus = mutation({
  args: {
    commandId: v.string(),
    status: v.union(
      v.literal("pending"),
      v.literal("processing"),
      v.literal("completed")
    ),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.commandId as any, {
      status: args.status,
    });
  },
});

/**
 * Mark a command as completed
 */
export const markCommandCompleted = mutation({
  args: {
    commandId: v.id("control"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.commandId, {
      status: "completed",
    });
  },
});

/**
 * Clear all completed commands (cleanup)
 */
export const clearCompletedCommands = mutation({
  args: {},
  handler: async (ctx) => {
    const completed = await ctx.db
      .query("control")
      .withIndex("by_status", (q) => q.eq("status", "completed"))
      .collect();
    
    for (const cmd of completed) {
      await ctx.db.delete(cmd._id);
    }
    
    return completed.length;
  },
});
