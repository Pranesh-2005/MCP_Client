"use client";

import { useEffect, useState } from "react";

import { useCopilotChat, useCopilotAction, CatchAllActionRenderProps } from "@copilotkit/react-core";
import { CopilotKitCSSProperties, CopilotSidebar, useCopilotChatSuggestions } from "@copilotkit/react-ui";
import { MCPEndpointConfig } from "@copilotkit/runtime";
import { DefaultToolRender } from "@/components/default-tool-render";

const themeColor = "#6366f1";

export default function Home() {
  return (
    <main style={{ "--copilot-kit-primary-color": themeColor } as CopilotKitCSSProperties}>
      <YourMainContent />
      <CopilotSidebar
        clickOutsideToClose={false}
        defaultOpen={true}
        labels={{
          title: "MCP Client",
          initial: "👋 Hi! I'm a MCP client like Claude Desktop and Cursor, I can assist you by calling MCP tools available.\n\n**Available tools:**\n- Weather alerts and forecasts (US)\n- GitHub user and repository information\n- Indian Rail train schedules\n\nTry asking me:\n- 'What's the weather forecast for New York?'\n- 'Show me repositories for microsoft'\n- 'Get train schedule for train 12345'\n\nWhat can I help you with?"
        }}
      />
    </main>
  );
}

function YourMainContent() {
  const { mcpServers, setMcpServers } = useCopilotChat();
  const [newMcpServer, setNewMcpServer] = useState("");

  useEffect(() => {
    setMcpServers([
      {
        endpoint: "https://mcpclientbackend.onrender.com/sse"  // Change this to your local MCP server
      }
    ]);
  }, []);

  const removeMcpServer = (url: string) => {
    setMcpServers(mcpServers.filter((server) => server.endpoint !== url));
  }

  const addMcpServer = (server: MCPEndpointConfig) => {
    setMcpServers([...mcpServers, server]);
  }

  useCopilotChatSuggestions({
    maxSuggestions: 3,
    instructions: "Give the user a short and concise suggestion based on the conversation and your available tools. Focus on weather, GitHub, or Indian Rail queries.",
  })

  useCopilotAction({
    name: "*",
    render: ({ name, status, args, result }: CatchAllActionRenderProps<[]>) => (
      <DefaultToolRender status={status} name={name} args={args} result={result} />
    ),
  });

  const classes = {
    wrapper: "h-screen w-screen flex justify-center items-center flex-col transition-colors duration-300",
    container: "bg-white/20 backdrop-blur-md p-8 rounded-2xl shadow-xl max-w-2xl w-full",
    server: "bg-white/15 p-4 rounded-xl text-white relative group hover:bg-white/20 transition-all",
    deleteButton: "absolute right-3 top-3 opacity-0 group-hover:opacity-100 transition-opacity bg-red-500 hover:bg-red-600 text-white rounded-full h-6 w-6 flex items-center justify-center",
    input: "bg-white/20 p-4 rounded-xl text-white relative group hover:bg-white/30 transition-all focus:outline-none focus:ring-2 focus:ring-indigo-500",
    submitButton: "w-full p-4 rounded-xl bg-indigo-500 text-white hover:bg-indigo-600 transition-all",
  }

  return (
    <div
      style={{ backgroundColor: themeColor }}
      className={classes.wrapper}
    >
      <div className={classes.container}>
        <h1 className="text-4xl font-bold text-white mb-2 text-center">MCP Client</h1>
        <p className="text-gray-200 text-center">Your AI assistant with access to MCP tools present in the MCP server.</p>
        <hr className="border-white/20 my-6" />

        <div className="flex flex-col gap-6">
          {mcpServers.map((server, index) => (
            <div key={index} className={classes.server}>
              <p className="pr-8 truncate">{server.endpoint}</p>
              <button className={classes.deleteButton} onClick={() => removeMcpServer(server.endpoint)}>
                ✕
              </button>
            </div>
          ))}
          <input 
            type="text" 
            placeholder="Enter MCP server URL" 
            className={classes.input} 
            value={newMcpServer}
            onChange={(e) => setNewMcpServer(e.target.value)}
          />
          <button className={classes.submitButton} onClick={() => {
            if (newMcpServer) {
              addMcpServer({ endpoint: newMcpServer });
              setNewMcpServer("");
            }
          }} >
            Add MCP Server
          </button>
        </div>
      </div>
    </div>
  );
}