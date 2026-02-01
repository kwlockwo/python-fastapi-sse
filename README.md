# Python FastAPI SSE Example

A simple example demonstrating Server-Sent Events (SSE) with FastAPI and a web client.

## Features

- FastAPI server with SSE endpoint
- Real-time data streaming from server to client
- Simple HTML/CSS/JavaScript frontend
- CORS enabled for development

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install fastapi uvicorn
```

3. Run the server:
```bash
uvicorn main:app --reload
```

4. Open your browser to `http://localhost:8000/static/index.html`

## Project Structure

```
.
├── main.py           # FastAPI server with SSE implementation
├── static/
│   ├── index.html    # Frontend client
│   └── styles.css    # Styling
└── venv/             # Virtual environment
```

## Deploy to Render

1. Fork this repository to your GitHub account

2. Go to [Render Dashboard](https://dashboard.render.com/) and create a new account or sign in

3. Click "New +" and select "Blueprint"

4. Connect your forked repository

5. Render will automatically detect the `render.yaml` file and deploy your application

6. Once deployed, access your app at the provided Render URL (e.g., `https://your-app.onrender.com/static/index.html`)

The `render.yaml` configuration file handles all deployment settings automatically.

## How It Works

The server streams events to connected clients using Server-Sent Events (SSE). Clients connect via the EventSource API and receive real-time updates without polling.
