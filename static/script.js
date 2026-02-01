// Store event source instances
let basicSource, logsSource, progressSource, multiSource, chatSource;

// Basic Stream Functions
function connectBasic() {
    if (basicSource) basicSource.close();
    basicSource = new EventSource('/stream/basic');
    document.getElementById('basic-status').className = 'connected';
    document.getElementById('basic-status').textContent = 'Connected';
    
    basicSource.addEventListener('update', (e) => {
        const data = JSON.parse(e.data);
        addEvent('basic-output', `[${e.type}] ${data.message} at ${data.timestamp}`);
    });
    
    basicSource.addEventListener('done', (e) => {
        const data = JSON.parse(e.data);
        addEvent('basic-output', `[COMPLETE] Total: ${data.total}`, 'warning');
        basicSource.close();
    });
    
    basicSource.onerror = () => {
        document.getElementById('basic-status').className = 'disconnected';
        document.getElementById('basic-status').textContent = 'Error/Disconnected';
    };
}

function disconnectBasic() {
    if (basicSource) {
        basicSource.close();
        document.getElementById('basic-status').className = 'disconnected';
        document.getElementById('basic-status').textContent = 'Disconnected';
    }
}

// Log Stream Functions
function connectLogs() {
    if (logsSource) logsSource.close();
    document.getElementById('logs-output').innerHTML = '';
    logsSource = new EventSource('/stream/logs');
    document.getElementById('logs-status').className = 'connected';
    document.getElementById('logs-status').textContent = 'Streaming...';
    
    logsSource.addEventListener('log', (e) => {
        const data = JSON.parse(e.data);
        const className = data.level === 'ERROR' ? 'error' : 
                        data.level === 'WARNING' ? 'warning' : '';
        addEvent('logs-output', 
            `[${data.timestamp}] [${data.level}] ${data.message}`, 
            className
        );
    });
    
    logsSource.addEventListener('complete', () => {
        addEvent('logs-output', '[END OF LOGS]', 'warning');
        logsSource.close();
        document.getElementById('logs-status').textContent = 'Complete';
    });
}

function disconnectLogs() {
    if (logsSource) logsSource.close();
    document.getElementById('logs-status').className = 'disconnected';
    document.getElementById('logs-status').textContent = 'Stopped';
}

// Progress Stream Functions
function connectProgress() {
    if (progressSource) progressSource.close();
    document.getElementById('progress-output').innerHTML = '';
    progressSource = new EventSource('/stream/progress');
    document.getElementById('progress-status').textContent = 'Running...';
    
    progressSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        addEvent('progress-output', 
            `Step ${data.step}/${data.total} (${data.percentage}%): ${data.message}`
        );
    });
    
    progressSource.onerror = () => {
        document.getElementById('progress-status').textContent = 'Complete';
        if (progressSource) progressSource.close();
    };
}

function disconnectProgress() {
    if (progressSource) progressSource.close();
    document.getElementById('progress-status').textContent = 'Cancelled';
}

// Multi-Event Stream Functions
function connectMulti() {
    if (multiSource) multiSource.close();
    document.getElementById('multi-output').innerHTML = '';
    multiSource = new EventSource('/stream/multi');
    document.getElementById('multi-status').className = 'connected';
    document.getElementById('multi-status').textContent = 'Connected';
    
    multiSource.addEventListener('connected', (e) => {
        addEvent('multi-output', '[CONNECTED] ' + e.data, 'warning');
    });
    
    multiSource.addEventListener('status', (e) => {
        const data = JSON.parse(e.data);
        addEvent('multi-output', `[STATUS] ${data.status}, uptime: ${data.uptime}s`);
    });
    
    multiSource.addEventListener('metrics', (e) => {
        const data = JSON.parse(e.data);
        addEvent('multi-output', 
            `[METRICS] CPU: ${data.cpu.toFixed(1)}%, Memory: ${data.memory.toFixed(1)}%, Requests: ${data.requests}`
        );
    });
    
    multiSource.addEventListener('update', (e) => {
        const data = JSON.parse(e.data);
        addEvent('multi-output', `[UPDATE] ${data.message}`);
    });
    
    multiSource.addEventListener('warning', (e) => {
        const data = JSON.parse(e.data);
        addEvent('multi-output', `[WARNING] ${data.message}`, 'warning');
    });
    
    multiSource.addEventListener('complete', () => {
        addEvent('multi-output', '[COMPLETE] Stream ended', 'warning');
        multiSource.close();
    });
}

function disconnectMulti() {
    if (multiSource) multiSource.close();
    document.getElementById('multi-status').className = 'disconnected';
    document.getElementById('multi-status').textContent = 'Disconnected';
}

// Chat Stream Functions
function connectChat() {
    const message = document.getElementById('chat-input').value || 'Hello!';
    if (chatSource) chatSource.close();
    document.getElementById('chat-output').innerHTML = '';
    
    chatSource = new EventSource(`/stream/chat?message=${encodeURIComponent(message)}`);
    
    let fullResponse = '';
    chatSource.addEventListener('chunk', (e) => {
        const data = JSON.parse(e.data);
        fullResponse += data.chunk;
        document.getElementById('chat-output').textContent = fullResponse;
    });
    
    chatSource.addEventListener('done', (e) => {
        const data = JSON.parse(e.data);
        addEvent('chat-output', `\n\n[Completed: ${data.tokens} tokens]`, 'warning');
        chatSource.close();
    });
}

function disconnectChat() {
    if (chatSource) chatSource.close();
}

// Utility function to add events to output divs
function addEvent(outputId, text, className = '') {
    const output = document.getElementById(outputId);
    const div = document.createElement('div');
    div.className = 'event ' + className;
    div.textContent = text;
    output.appendChild(div);
    output.scrollTop = output.scrollHeight;
}

// Allow Enter key to send chat messages
document.addEventListener('DOMContentLoaded', () => {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                connectChat();
            }
        });
    }
});