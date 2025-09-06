// MCP Backend API utilities
const MCP_BACKEND_URL = 'http://localhost:8000'; // MCP server endpoint

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

// Converts base64 to an array buffer
export const base64ToArrayBuffer = (base64: string): ArrayBuffer => {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
};

// Converts PCM audio data to a playable WAV file blob
export const pcmToWav = (pcmData: Int16Array, sampleRate: number): Blob => {
    const wavBuffer = new ArrayBuffer(44 + pcmData.length * 2);
    const view = new DataView(wavBuffer);

    let offset = 0;
    const writeString = (str: string) => {
        for (let i = 0; i < str.length; i++) {
            view.setUint8(offset++, str.charCodeAt(i));
        }
    };

    writeString('RIFF');
    view.setUint32(offset, 36 + pcmData.length * 2, true);
    offset += 4;
    writeString('WAVE');
    writeString('fmt ');
    view.setUint32(offset, 16, true);
    offset += 4;
    view.setUint16(offset, 1, true); // Audio format (PCM)
    offset += 2;
    view.setUint16(offset, 1, true); // Num channels
    offset += 2;
    view.setUint32(offset, sampleRate, true);
    offset += 4;
    view.setUint32(offset, sampleRate * 2, true); // Byte rate
    offset += 4;
    view.setUint16(offset, 2, true); // Block align
    offset += 2;
    view.setUint16(offset, 16, true); // Bits per sample
    offset += 2;
    writeString('data');
    view.setUint32(offset, pcmData.length * 2, true);
    offset += 4;

    for (let i = 0; i < pcmData.length; i++) {
        view.setInt16(offset, pcmData[i], true);
        offset += 2;
    }

    return new Blob([wavBuffer], { type: 'audio/wav' });
};

// Rephrase post content using Gemini API
export const rephraseWithGemini = async (content: string, tone: number): Promise<string> => {
    let tonePrompt = "neutral and professional";
    if (tone < 30) {
        tonePrompt = "very formal and serious";
    } else if (tone < 70) {
        tonePrompt = "friendly and professional";
    } else {
        tonePrompt = "fun and creative";
    }

    if (!apiKey) {
        // Mock implementation when no API key is provided
        return new Promise((resolve) => {
            setTimeout(() => {
                let newContent = content;
                if (tone < 30) {
                    newContent = content.replace(/🚀|🔥|❤️|✨/g, '').replace(/!/g, '.').toLowerCase();
                } else if (tone > 70) {
                    newContent = content + ' 🎉🚀✨';
                }
                resolve(newContent);
            }, 2000);
        });
    }

    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key=${apiKey}`;
    const systemPrompt = `You are an expert social media manager. Your task is to rewrite the provided text to be more ${tonePrompt}. Do not add any new information, just rephrase the existing content. Do not output anything other than the new text.`;
    const userQuery = `Original Text: "${content}"`;

    const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
    };

    const response = await fetchWithExponentialBackoff(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const result = await response.json();
    const newText = result.candidates?.[0]?.content?.parts?.[0]?.text;

    if (!newText) {
        throw new Error('Failed to rephrase content');
    }

    return newText.trim();
};

// Generate TTS audio using Gemini API
export const generateTTSWithGemini = async (content: string): Promise<string> => {
    if (!apiKey) {
        // Mock TTS when no API key is provided
        throw new Error('Mock TTS mode - no actual audio generated');
    }

    const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    const payload = {
        contents: [{ parts: [{ text: content }] }],
        generationConfig: {
            responseModalities: ["AUDIO"],
            speechConfig: {
                voiceConfig: {
                    prebuiltVoiceConfig: { voiceName: "Puck" }
                }
            }
        },
    };

    const response = await fetchWithExponentialBackoff(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    const result = await response.json();
    const audioData = result?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
    const mimeType = result?.candidates?.[0]?.content?.parts?.[0]?.inlineData?.mimeType;

    if (!audioData || !mimeType || !mimeType.startsWith("audio/")) {
        throw new Error('Failed to generate audio');
    }

    const sampleRate = parseInt(mimeType.match(/rate=(\d+)/)?.[1] || '16000', 10);
    const pcmData = new Int16Array(base64ToArrayBuffer(audioData));
    const wavBlob = pcmToWav(pcmData, sampleRate);
    return URL.createObjectURL(wavBlob);
};
