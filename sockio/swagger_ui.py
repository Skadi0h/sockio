import os
from sockio.openapi_spec import get_openapi_json
from sockio.websocket_docs import get_websocket_docs
import json


def get_swagger_html() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Chat API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin:0;
            background: #fafafa;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: '/api/openapi.json',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                validatorUrl: null,
                tryItOutEnabled: true,
                supportedSubmitMethods: ['get', 'post', 'put', 'delete', 'patch'],
                onComplete: function() {{
                    console.log('Swagger UI loaded');
                }},
                requestInterceptor: function(request) {{
                    console.log('Request:', request);
                    return request;
                }},
                responseInterceptor: function(response) {{
                    console.log('Response:', response);
                    return response;
                }}
            }});
        }};
    </script>
</body>
</html>
"""


def get_redoc_html() -> str:
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Chat API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url='/api/openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
</body>
</html>
"""


class SwaggerHandler:
    def __init__(self, app):
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        self.app.get("/api/openapi.json", self.serve_openapi_json)
        self.app.get("/api/websocket-docs.json", self.serve_websocket_docs)
        self.app.get("/docs", self.serve_swagger_ui)
        self.app.get("/redoc", self.serve_redoc)
        self.app.get("/api/docs", self.serve_swagger_ui)
        self.app.get("/websocket-docs", self.serve_websocket_docs_html)
    
    def serve_openapi_json(self, res, req):
        try:
            openapi_json = get_openapi_json()
            res.write_header("Access-Control-Allow-Origin", "*")
            res.write_header("Content-Type", "application/json")
            res.end(openapi_json)
        except Exception as e:
            res.write_header("Content-Type", "application/json")
            res.write_status("500 Internal Server Error")
            res.end('{"error": "Failed to generate OpenAPI specification"}')
    
    def serve_swagger_ui(self, res, req):
        try:
            html = get_swagger_html()
            res.write_header("Access-Control-Allow-Origin", "*")
            res.write_header("Content-Type", "text/html")
            res.end(html)
        except Exception as e:
            res.write_header("Content-Type", "text/html")
            res.write_status("500 Internal Server Error")
            res.end("<h1>Error loading Swagger UI</h1>")
    
    def serve_redoc(self, res, req):
        try:
            html = get_redoc_html()
            res.write_header("Access-Control-Allow-Origin", "*")
            res.write_header("Content-Type", "text/html")
            res.end(html)
        except Exception as e:
            res.write_header("Content-Type", "text/html")
            res.write_status("500 Internal Server Error")
            res.end("<h1>Error loading ReDoc</h1>")
    
    def serve_websocket_docs(self, res, req):
        try:
            docs = get_websocket_docs()
            docs_json = json.dumps(docs, indent=2)
            res.write_header("Access-Control-Allow-Origin", "*")
            res.write_header("Content-Type", "application/json")
            res.end(docs_json)
        except Exception as e:
            res.write_header("Content-Type", "application/json")
            res.write_status("500 Internal Server Error")
            res.end('{"error": "Failed to generate WebSocket documentation"}')
    
    def serve_websocket_docs_html(self, res, req):
        try:
            html = self.get_websocket_docs_html()
            res.write_header("Access-Control-Allow-Origin", "*")
            res.write_header("Content-Type", "text/html")
            res.end(html)
        except Exception as e:
            res.write_header("Content-Type", "text/html")
            res.write_status("500 Internal Server Error")
            res.end("<h1>Error loading WebSocket Documentation</h1>")
    
    def get_websocket_docs_html(self) -> str:
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WebSocket Protocol Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3 {
            color: #2c3e50;
        }
        h1 {
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }
        .endpoint {
            background: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }
        .method {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
            font-size: 12px;
            margin-right: 10px;
        }
        .client-server { background: #e74c3c; color: white; }
        .server-client { background: #27ae60; color: white; }
        pre {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
        }
        .nav {
            background: #34495e;
            padding: 15px;
            margin: -30px -30px 30px -30px;
            border-radius: 8px 8px 0 0;
        }
        .nav a {
            color: #ecf0f1;
            text-decoration: none;
            margin-right: 20px;
            padding: 8px 12px;
            border-radius: 4px;
            transition: background 0.3s;
        }
        .nav a:hover {
            background: #2c3e50;
        }
        .error-code {
            background: #e74c3c;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="nav">
            <a href="/docs">REST API Docs</a>
            <a href="/redoc">ReDoc</a>
            <a href="/websocket-docs">WebSocket Docs</a>
            <a href="/api/openapi.json">OpenAPI JSON</a>
            <a href="/api/websocket-docs.json">WebSocket JSON</a>
        </div>
        
        <h1>WebSocket Protocol Documentation</h1>
        
        <div class="endpoint">
            <h2>Connection</h2>
            <p><strong>URL:</strong> <code>/ws</code></p>
            <p>WebSocket endpoint for real-time communication. Authentication is required for most operations.</p>
        </div>
        
        <h2>Authentication</h2>
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>authenticate</h3>
            <p>Authenticate the WebSocket connection using a session token obtained from the REST API login endpoint.</p>
            <pre>{
  "type": "authenticate",
  "data": {
    "session_token": "your-session-token-here"
  }
}</pre>
            <p><strong>Response:</strong></p>
            <pre>{
  "type": "auth_success",
  "data": {
    "user_id": "string",
    "username": "string"
  }
}</pre>
        </div>
        
        <h2>Messaging</h2>
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>send_message</h3>
            <p>Send a message to a conversation.</p>
            <pre>{
  "type": "send_message",
  "data": {
    "conversation_id": "string",
    "content": "string",
    "message_type": "text|image|video|audio|file",
    "attachments": []
  }
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>edit_message</h3>
            <p>Edit an existing message.</p>
            <pre>{
  "type": "edit_message",
  "data": {
    "message_id": "string",
    "content": "string"
  }
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>delete_message</h3>
            <p>Delete a message.</p>
            <pre>{
  "type": "delete_message",
  "data": {
    "message_id": "string"
  }
}</pre>
        </div>
        
        <h2>Conversations</h2>
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>join_conversation</h3>
            <p>Join a conversation to receive messages.</p>
            <pre>{
  "type": "join_conversation",
  "data": {
    "conversation_id": "string"
  }
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method client-server">CLIENT → SERVER</span>
            <h3>create_group</h3>
            <p>Create a new group conversation.</p>
            <pre>{
  "type": "create_group",
  "data": {
    "name": "string",
    "description": "string",
    "participant_ids": ["user_id1", "user_id2"]
  }
}</pre>
        </div>
        
        <h2>Server Events</h2>
        <div class="endpoint">
            <span class="method server-client">SERVER → CLIENT</span>
            <h3>new_message</h3>
            <p>Broadcast when a new message is received.</p>
            <pre>{
  "type": "new_message",
  "data": {
    "message_id": "string",
    "conversation_id": "string",
    "sender_id": "string",
    "content": "string",
    "message_type": "string",
    "created_at": "string",
    "attachments": []
  }
}</pre>
        </div>
        
        <div class="endpoint">
            <span class="method server-client">SERVER → CLIENT</span>
            <h3>user_typing</h3>
            <p>Broadcast when a user starts typing.</p>
            <pre>{
  "type": "user_typing",
  "data": {
    "user_id": "string",
    "conversation_id": "string",
    "username": "string"
  }
}</pre>
        </div>
        
        <h2>Error Codes</h2>
        <ul>
            <li><span class="error-code">AUTH_REQUIRED</span> - Authentication required for this operation</li>
            <li><span class="error-code">INVALID_TOKEN</span> - Invalid or expired session token</li>
            <li><span class="error-code">CONVERSATION_NOT_FOUND</span> - Conversation not found or access denied</li>
            <li><span class="error-code">MESSAGE_NOT_FOUND</span> - Message not found or access denied</li>
            <li><span class="error-code">PERMISSION_DENIED</span> - Insufficient permissions for this operation</li>
            <li><span class="error-code">RATE_LIMITED</span> - Too many requests, please slow down</li>
        </ul>
        
        <h2>Connection States</h2>
        <ul>
            <li><strong>connecting</strong> - Initial connection state</li>
            <li><strong>authenticating</strong> - Waiting for authentication</li>
            <li><strong>authenticated</strong> - Successfully authenticated</li>
            <li><strong>disconnected</strong> - Connection closed</li>
        </ul>
    </div>
</body>
</html>
"""

