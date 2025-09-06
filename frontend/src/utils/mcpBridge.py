#!/usr/bin/env python3
"""
Simple HTTP bridge for MCP server
Converts HTTP requests to MCP STDIO calls
"""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import os

class MCPBridgeHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        """Handle MCP tool calls"""
        if self.path == '/mcp/tools/call':
            try:
                # Read request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                tool_call = json.loads(post_data.decode('utf-8'))
                
                # Call MCP server
                result = self.call_mcp_tool(tool_call)
                
                # Send response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode('utf-8'))
                
            except Exception as e:
                self.send_error_response(str(e))
        else:
            self.send_error_response("Not found", 404)

    def call_mcp_tool(self, tool_call):
        """Execute MCP tool via subprocess"""
        try:
            # Change to MCP server directory
            mcp_dir = os.path.join(os.path.dirname(__file__), '../../bbai_mcp_server')
            
            # Prepare MCP request
            mcp_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": tool_call["name"],
                    "arguments": tool_call.get("arguments", {})
                }
            }
            
            # Run MCP server
            process = subprocess.Popen(
                ['uv', 'run', 'blackbox-mcp-server'],
                cwd=mcp_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send request and get response
            stdout, stderr = process.communicate(
                input=json.dumps(mcp_request) + '\n',
                timeout=30
            )
            
            if process.returncode != 0:
                raise Exception(f"MCP server error: {stderr}")
            
            # Parse response
            for line in stdout.strip().split('\n'):
                if line.strip():
                    try:
                        response = json.loads(line)
                        if 'result' in response:
                            return response['result']
                        elif 'error' in response:
                            return {"isError": True, "content": [{"type": "text", "text": response['error']['message']}]}
                    except json.JSONDecodeError:
                        continue
            
            return {"isError": True, "content": [{"type": "text", "text": "No valid response from MCP server"}]}
            
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": str(e)}]}

    def send_error_response(self, message, code=500):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error_response = {"isError": True, "content": [{"type": "text", "text": message}]}
        self.wfile.write(json.dumps(error_response).encode('utf-8'))

def run_bridge_server(port=8000):
    """Run the MCP bridge server"""
    server = HTTPServer(('localhost', port), MCPBridgeHandler)
    print(f"MCP Bridge server running on http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_bridge_server(port)
