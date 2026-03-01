### **Swarm: A Self-Healing, Multi-Agent Hive Mind for Content Discovery**

**The Problem:** Content marketers and agency owners waste up to 80% of their week manually doom-scrolling to find viral formats and inspiration. Traditional web scrapers are dead—they are too slow, get trapped by dynamic UIs, hit CAPTCHA walls, and get instantly banned by platforms like Instagram.

**The Solution:** Swarm is a fully dynamic, collaborative web-agent network built for the modern internet. Instead of deploying a single AI to search linearly, Swarm deploys 10 concurrent, context-aware browser agents that hunt in parallel.

**How It Works:**
Swarm isn't just running scripts; it's orchestrating a hive mind. When a user enters a target niche, the 10 agents deploy across the web.

* **Real-Time Collaboration:** If Agent 2 finds a highly engaging reel format, it fires a signal through our central message bus. The system instantly alerts the other agents, pulling them off dead-end searches to swarm the newly discovered trend.
* **Dynamic Self-Healing:** By actively monitoring the LLM reasoning traces of every agent, the system knows when a browser is stuck. If an agent falls into an infinite scroll loop or burns tokens without results, the orchestrator kills the task and dynamically reassigns it to a successful node.
* **Visual Proof:** The entire process is mapped in real-time. A 3D orbital UI visualizes the swarm's live state, while a 2D infinite canvas seamlessly populates with the validated, ready-to-clone viral formats.

### **The Tech Stack**

* **Browser Use API:** Powers the 10 concurrent, headless browser agents. Utilizes persistent Cloud Profiles to naturally bypass Instagram's bot detection and CAPTCHAs.
* **Convex:** The central nervous system and real-time message bus. It instantly syncs discoveries and agent states between the backend orchestrator and the frontend UI with zero WebSocket overhead.
* **Laminar:** The observability and self-healing layer. Monitors real-time LLM traces to detect hallucinating, looping, or high-token-burn agents to trigger dynamic reassignment.
* **OpenAI (GPT 5.2):** The reasoning engines driving the browser actions and evaluating video engagement metrics.
* **Next.js & Vercel:** The core frontend framework and deployment infrastructure.
* **React Three Fiber:** Drives the real-time 3D visualization of the agent nodes and their communication pathways.
* **React Flow:** Powers the interactive, 2D whiteboard canvas that outputs the final, cloned content cards.
