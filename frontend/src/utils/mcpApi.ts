// MCP Backend API utilities
const MCP_BACKEND_URL = 'http://localhost:8001'; // MCP server endpoint

// MCP tool call interface
interface MCPToolCall {
    name: string;
    arguments: Record<string, any>;
}

interface MCPResponse {
    content?: Array<{
        type: string;
        text?: string;
        data?: string;
        mimeType?: string;
    }>;
    isError?: boolean;
    _meta?: Record<string, any>;
}

// Function to handle exponential backoff for API calls
export const fetchWithExponentialBackoff = async (
    url: string, 
    options: RequestInit, 
    retries = 3, 
    delay = 1000
): Promise<Response> => {
    try {
        const response = await fetch(url, options);
        if (!response.ok) {
            throw new Error(`API call failed with status: ${response.status}`);
        }
        return response;
    } catch (error) {
        if (retries > 0) {
            console.log(`Retrying in ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
            return fetchWithExponentialBackoff(url, options, retries - 1, delay * 2);
        } else {
            throw error;
        }
    }
};

// Call MCP tool via backend
export const callMCPTool = async (toolCall: MCPToolCall): Promise<MCPResponse> => {
    const response = await fetchWithExponentialBackoff(`${MCP_BACKEND_URL}/mcp/tools/call`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(toolCall)
    });

    return await response.json();
};

// Test MCP backend connection
export const testMCPConnection = async (): Promise<boolean> => {
    try {
        const response = await callMCPTool({
            name: 'test_connection',
            arguments: {}
        });
        return !response.isError;
    } catch (error) {
        console.error('MCP connection test failed:', error);
        return false;
    }
};

// Get available models from MCP backend
export const getMCPModels = async (modelType?: string): Promise<string[]> => {
    try {
        const response = await callMCPTool({
            name: 'blackbox_models',
            arguments: modelType ? { model_type: modelType } : {}
        });

        if (response.content?.[0]?.text) {
            const models = JSON.parse(response.content[0].text);
            return models.map((model: any) => model.id || model.name);
        }
        return [];
    } catch (error) {
        console.error('Failed to get MCP models:', error);
        return [];
    }
};

// Rephrase post content using MCP backend (Blackbox AI)
export const rephraseWithMCP = async (content: string, tone: number): Promise<string> => {
    let tonePrompt = "neutral and professional";
    if (tone < 30) {
        tonePrompt = "very formal and serious";
    } else if (tone < 70) {
        tonePrompt = "friendly and professional";
    } else {
        tonePrompt = "fun and creative";
    }

    try {
        const response = await callMCPTool({
            name: 'blackbox_chat',
            arguments: {
                model: 'blackboxai/openai/gpt-4',
                messages: [
                    {
                        role: 'system',
                        content: `You are an expert social media manager. Your task is to rewrite the provided text to be more ${tonePrompt}. Do not add any new information, just rephrase the existing content. Do not output anything other than the new text.`
                    },
                    {
                        role: 'user',
                        content: `Original Text: "${content}"`
                    }
                ],
                temperature: 0.7,
                max_tokens: 512
            }
        });

        if (response.content?.[0]?.text) {
            const result = JSON.parse(response.content[0].text);
            return result.choices?.[0]?.message?.content || content;
        }
        
        throw new Error('Failed to rephrase content');
    } catch (error) {
        console.error('MCP rephrase failed:', error);
        
        // Fallback to simple mock rephrasing
        let newContent = content;
        if (tone < 30) {
            newContent = content.replace(/🚀|🔥|❤️|✨/g, '').replace(/!/g, '.').toLowerCase();
        } else if (tone > 70) {
            newContent = content + ' 🎉🚀✨';
        }
        return newContent;
    }
};

// Generate TTS audio using MCP backend (if available)
export const generateTTSWithMCP = async (content: string): Promise<string> => {
    try {
        // First try to get available models to see if TTS is supported
        const models = await getMCPModels('speech');
        
        if (models.length === 0) {
            throw new Error('No TTS models available in MCP backend');
        }

        // Use the first available TTS model
        const response = await callMCPTool({
            name: 'blackbox_chat', // Assuming TTS might be available through chat models
            arguments: {
                model: models[0],
                messages: [
                    {
                        role: 'user',
                        content: `Generate speech for: ${content}`
                    }
                ],
                response_format: 'audio'
            }
        });

        if (response.content?.[0]?.data && response.content[0].mimeType?.startsWith('audio/')) {
            // Convert base64 audio data to blob URL
            const audioData = response.content[0].data;
            const byteCharacters = atob(audioData);
            const byteNumbers = new Array(byteCharacters.length);
            for (let i = 0; i < byteCharacters.length; i++) {
                byteNumbers[i] = byteCharacters.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNumbers);
            const blob = new Blob([byteArray], { type: response.content[0].mimeType });
            return URL.createObjectURL(blob);
        }
        
        throw new Error('No audio data received');
    } catch (error) {
        console.error('MCP TTS failed:', error);
        throw new Error('TTS not available - using mock mode');
    }
};
