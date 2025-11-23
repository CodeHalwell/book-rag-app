document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const newChatBtn = document.getElementById('new-chat-btn');

    // Generate or retrieve session ID
    let currentSessionId = localStorage.getItem('bookrag_session_id');
    if (!currentSessionId) {
        currentSessionId = crypto.randomUUID();
        localStorage.setItem('bookrag_session_id', currentSessionId);
    }

    // New Chat Button Logic
    newChatBtn.addEventListener('click', () => {
        // 1. Generate new Session ID
        currentSessionId = crypto.randomUUID();
        localStorage.setItem('bookrag_session_id', currentSessionId);

        // 2. Clear Chat Interface
        chatContainer.innerHTML = `
        <div class="flex justify-start message-appear">
            <div class="flex flex-col space-y-1 max-w-[80%]">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span class="text-xs font-bold">AI</span>
                    </div>
                    <div class="bg-gray-800 p-3 rounded-2xl rounded-tl-none border border-gray-700 shadow-sm">
                        <p class="text-sm text-gray-200">Hello! I'm BookRAG. Ask me any question about your document collection.</p>
                    </div>
                </div>
            </div>
        </div>
        `;
        
        // 3. Focus Input
        userInput.focus();
    });

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = '56px';
        this.style.height = Math.min(Math.max(this.scrollHeight, 56), 150) + 'px';
    });

    // Handle Enter key to submit
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    function createMessageBubble(isUser) {
        const wrapperDiv = document.createElement('div');
        wrapperDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} message-appear`;
        
        const contentDivId = `msg-content-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        
        const innerHTML = isUser ? `
            <div class="flex flex-col space-y-1 max-w-[80%] items-end">
                <div class="flex items-center space-x-2 flex-row-reverse space-x-reverse">
                    <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>
                    <div class="chat-bubble-user p-3 text-white">
                        <div id="${contentDivId}" class="text-sm whitespace-pre-wrap"></div>
                    </div>
                </div>
            </div>
        ` : `
            <div class="flex flex-col space-y-1 max-w-[80%]">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span class="text-xs font-bold">AI</span>
                    </div>
                    <div class="chat-bubble-ai p-3 overflow-hidden">
                        <div id="${contentDivId}" class="text-sm text-gray-200 prose prose-invert max-w-none"></div>
                    </div>
                </div>
            </div>
        `;

        wrapperDiv.innerHTML = innerHTML;
        chatContainer.appendChild(wrapperDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        
        return document.getElementById(contentDivId);
    }

    function appendLoader() {
        const loaderId = 'loader-' + Date.now();
        const wrapperDiv = document.createElement('div');
        wrapperDiv.id = loaderId;
        wrapperDiv.className = 'flex justify-start message-appear';
        
        wrapperDiv.innerHTML = `
            <div class="flex flex-col space-y-1 max-w-[80%]">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span class="text-xs font-bold">AI</span>
                    </div>
                    <div class="chat-bubble-ai p-4 flex space-x-1">
                        <div class="typing-dot" style="animation-delay: 0s"></div>
                        <div class="typing-dot" style="animation-delay: 0.2s"></div>
                        <div class="typing-dot" style="animation-delay: 0.4s"></div>
                    </div>
                </div>
            </div>
        `;
        chatContainer.appendChild(wrapperDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
        return loaderId;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // 1. Add User Message
        const userMsgDiv = createMessageBubble(true);
        userMsgDiv.textContent = message; // User message is just text
        
        userInput.value = '';
        userInput.style.height = '56px';
        sendBtn.disabled = true;

        // 2. Add Loader
        const loaderId = appendLoader();

        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

        try {
            // 3. Send to Backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ 
                    query: message,
                    session_id: currentSessionId
                })
            });

            // 4. Remove Loader
            document.getElementById(loaderId).remove();

            // 5. Create AI Message Bubble
            const aiMsgDiv = createMessageBubble(false);
            let fullAnswer = "";

            // 6. Handle Streaming Response
            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            // Configure marked options
            marked.setOptions({
                highlight: function(code, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        return hljs.highlight(code, { language: lang }).value;
                    }
                    return hljs.highlightAuto(code).value;
                },
                breaks: true
            });

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const data = JSON.parse(line);
                        if (data.error) {
                            fullAnswer += `\n\n*Error: ${data.error}*`;
                        } else if (data.answer) {
                            fullAnswer += data.answer;
                        }
                    } catch (e) {
                        console.warn("Failed to parse JSON chunk:", line);
                    }
                }
                
                // Update UI with markdown parsed content
                aiMsgDiv.innerHTML = marked.parse(fullAnswer);
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }

        } catch (error) {
            const loader = document.getElementById(loaderId);
            if (loader) loader.remove();
            
            const aiMsgDiv = createMessageBubble(false);
            aiMsgDiv.textContent = "Sorry, I couldn't connect to the server. Please try again.";
            console.error(error);
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
});
