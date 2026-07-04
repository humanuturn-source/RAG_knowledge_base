

# Local Knowledge Base RAG Setup Guide

---

## Part 1: Infrastructure & Dependency Setup
---

### Step 1: Install & Launch Docker Desktop
	1.	Download and install Docker Desktop for your machine.
	2.	Launch Docker Desktop and verify it is actively running. 

### Step 2: Initialize Local Ollama Models

```bash
ollama pull gemma4
ollama pull nomic-embed-text
```
### Step 3: Spin Up Persistent ChromaDB Container

Run the following command to deploy ChromaDB as a background service. This maps the container to port 8000 and 
safely persists your data to your home directory (~/.chroma_data):

```bash
docker run -d \
  --name chroma-server \
  -p 8000:8000 \
  -v ~/.chroma_data:/chroma/chroma \
  -e IS_PERSISTENT=TRUE \
  --restart unless-stopped \
  chromadb/chroma:latest

```

Verification: 
Open your browser and navigate to http://localhost:8000/api/v1/heartbeat. If it returns a timestamp, your database 
container is healthy and running.

### Step 4: Install Python Packages

Execute the following pip command to install core utilities, file system event listeners, and the Model Context Protocol (MCP) 
framework:

```bash
pip install langchain langchain-community langchain-chroma chromadb watchdog pypdf mcp

```

---

## Part 2: Claude Desktop Integration (MCP)

### Step 5: Download the MCP Bridge Script

To allow Claude Desktop to securely query your Dockerized vector database concurrently without database lockups, 
you need the MCP server utility script.
•	Download or copy ***mcp_chroma_server.py*** from the link provided in video description.
•	Place it in a secure, permanent directory on your machine.

### Step 6: Configure Claude Desktop App

Open your Claude Desktop configuration file using your terminal or a text editor. On macOS, this file is located at:
~/Library/Application Support/Claude/claude_desktop_config.json

Add or merge the following JSON payload, ensuring you supply the exact absolute path to your script:

```json
{
  "mcpServers": {
    "local-chroma-search": {
      "command": "python3",
      "args": [
        "/absolute/path/to/your/directory/mcp_chroma_server.py"
      ]
    }
  }
}

```

Restart Claude Desktop completely to apply changes. A hammer icon will appear if the MCP tool initializes successfully.

---

## Part 3: Live Document Sync Architecture

### Step 7: Create the Manifest Tracking File

Create a file named ***manifest.json*** in your local project workspace. Below is a sample schema demonstrating how to 
register structural business documentation, including project management structures like your Flask-based e-commerce initiatives.

```json
[
  {
    "id": "shopping_plan_001",
    "description": "Flask-Based Online Shopping Application Roadmap by Tom Cruise",
    "file_path": "/Users/shared/documents/Shopping_Project_Plan.pdf",
    "action": "add"
  },
  {
    "id": "doc_002",
    "description": "Employee Onboarding and Benefits Handbook",
    "file_path": "/Users/shared/documents/employee_handbook.txt",
    "action": "update"
  },
  {
    "id": "doc_003",
    "description": "Deprecating Legacy API Documentation",
    "file_path": "/Users/shared/documents/legacy_api.md",
    "action": "delete"
  }
]
```

### Step 8: Deploy the Automated Synchronization Daemon

The orchestration script relies on the watchdog library to listen directly for file saves performed on manifest.json. 
Upon any disk change, it automatically coordinates the targeted add, rewrite, or deletion rules natively inside Docker.

•	Download or copy ***automated_sync.py*** from the link in your description.
•	Place it in the exact same workspace directory as your manifest.json.

---

## Part 4: Runtime Execution & Validation

### Step 9: Launch the Monitoring Core

```bash
python3 automated_sync.py

```
Upon launching, it will execute an initial verification loop, automatically reading manifest.json and indexing documents like Shopping_Project_Plan.pdf into your local persistent storage matrix.

### Step 10: Live Testing Strategy

	1.	Open manifest.json in any IDE or text editor.
	2.	Modify a path or change an execution "action" (e.g., switch a profile from "add" to "update" or "delete").
	3.	Save the file.
	4.	Watch your script terminal instantly output the background logs as it ingests, segments, or purges target chunks without interrupting open reader sessions in Claude Desktop.

### Step 11: Start Testing

Open Claude desktop and give prompts

"Do you have any documents in Chroma DB?"

---








