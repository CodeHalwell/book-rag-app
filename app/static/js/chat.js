document.addEventListener('DOMContentLoaded', () => {
    const chatContainer = document.getElementById('chat-container');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    // Auto-resize textarea
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 150) + 'px';
    });

    // Handle Enter key to submit
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event('submit'));
        }
    });

    function appendMessage(content, isUser) {
        const wrapperDiv = document.createElement('div');
        wrapperDiv.className = `flex ${isUser ? 'justify-end' : 'justify-start'} message-appear`;
        
        const innerHTML = isUser ? `
            <div class="flex flex-col space-y-1 max-w-[80%] items-end">
                <div class="flex items-center space-x-2 flex-row-reverse space-x-reverse">
                    <div class="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                    </div>
                    <div class="chat-bubble-user p-3 text-white">
                        <p class="text-sm whitespace-pre-wrap">${escapeHtml(content)}</p>
                    </div>
                </div>
            </div>
        ` : `
            <div class="flex flex-col space-y-1 max-w-[80%]">
                <div class="flex items-center space-x-2">
                    <div class="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0">
                        <span class="text-xs font-bold">AI</span>
                    </div>
                    <div class="chat-bubble-ai p-3">
                        <div class="text-sm text-gray-200 whitespace-pre-wrap">${content}</div> <!-- Note: AI content might contain HTML/Markdown later -->
                    </div>
                </div>
            </div>
        `;

        wrapperDiv.innerHTML = innerHTML;
        chatContainer.appendChild(wrapperDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
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
        appendMessage(message, true);
        userInput.value = '';
        userInput.style.height = 'auto';
        sendBtn.disabled = true;

        // 2. Add Loader
        const loaderId = appendLoader();

        try {
            // 3. Send to Backend
            const response = await fetch('/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: message })
            });

            const data = await response.json();

            // 4. Remove Loader & Add AI Response
            document.getElementById(loaderId).remove();
            
            if (data.error) {
                appendMessage(`Error: ${data.error}`, false);
            } else {
                // You can process markdown here if needed
                appendMessage(data.answer, false);
            }

        } catch (error) {
            const loader = document.getElementById(loaderId);
            if (loader) loader.remove();
            appendMessage("Sorry, I couldn't connect to the server. Please try again.", false);
            console.error(error);
        } finally {
            sendBtn.disabled = false;
            userInput.focus();
        }
    });
});

