import {
  CopilotRuntime,
  OpenAIAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { NextRequest } from "next/server";
import { MCPClient } from "@/app/utils/mcp-client";
import OpenAI from "openai";

const openai = new OpenAI({
  apiKey: process.env.AZURE_OPENAI_API_KEY!,
  baseURL: `${process.env.AZURE_OPENAI_ENDPOINT}/openai/deployments/${process.env.AZURE_OPENAI_DEPLOYMENT_NAME}`,
  defaultQuery: { 
    'api-version': process.env.AZURE_OPENAI_API_VERSION!
  },
  defaultHeaders: {
    'api-key': process.env.AZURE_OPENAI_API_KEY!,
  },
});

const serviceAdapter = new OpenAIAdapter({
  openai,
});

const runtime = new CopilotRuntime({
  createMCPClient: async (config) => {
    const mcpClient = new MCPClient({
      serverUrl: config.endpoint,
    });
    await mcpClient.connect();
    return mcpClient;
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter,
    endpoint: "/api/copilotkit",
  });

  return handleRequest(req);
};
