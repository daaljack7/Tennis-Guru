// Generate a unique session ID for this chat
let sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

const chatMessages = document.getElementById('chat-messages');
const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newChatBtn = document.getElementById('new-chat-btn');

// Guru avatar URL
const guruAvatarUrl = '/static/FloatingGuru.png';

// Add a message to the chat
function addMessage(content, isUser) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;

    // Add guru avatar for bot messages
    if (!isUser) {
        const avatar = document.createElement('img');
        avatar.src = guruAvatarUrl;
        avatar.alt = 'Guru';
        avatar.className = 'guru-avatar';
        messageDiv.appendChild(avatar);
    }

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.textContent = content;

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    // Scroll to show the beginning of the new message
    if (isUser) {
        // For user messages, scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        // For bot messages, scroll to show the top of the message
        messageDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// Show typing indicator
function showTyping() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'typing-indicator';
    typingDiv.id = 'typing-indicator';

    // Add guru avatar
    const avatar = document.createElement('img');
    avatar.src = guruAvatarUrl;
    avatar.alt = 'Guru';
    avatar.className = 'guru-avatar';
    typingDiv.appendChild(avatar);

    const dotsDiv = document.createElement('div');
    dotsDiv.className = 'typing-dots';
    dotsDiv.innerHTML = '<span></span><span></span><span></span>';

    typingDiv.appendChild(dotsDiv);
    chatMessages.appendChild(typingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) {
        typing.remove();
    }
}

// Send message to the server
async function sendMessage(message) {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const data = await response.json();
        return data.response;
    } catch (error) {
        console.error('Error:', error);
        return "Sorry, I'm having trouble connecting right now. Please try again.";
    }
}

// Handle form submission
chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, true);

    // Clear input and disable
    userInput.value = '';
    sendBtn.disabled = true;
    userInput.disabled = true;

    // Show typing indicator
    showTyping();

    // Get bot response
    const response = await sendMessage(message);

    // Hide typing and show response
    hideTyping();
    addMessage(response, false);

    // Re-enable input
    sendBtn.disabled = false;
    userInput.disabled = false;
    userInput.focus();
});

// Handle new chat
newChatBtn.addEventListener('click', async () => {
    // Clear server-side conversation
    await fetch('/new-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId
        }),
    });

    // Generate new session ID
    sessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

    // Clear chat messages except the greeting (with guru avatar)
    chatMessages.innerHTML = `
        <div class="message bot-message">
            <img src="${guruAvatarUrl}" alt="Guru" class="guru-avatar">
            <div class="message-content">
                Greetings! I am your Tennis Guru. I specialize in helping you improve your mental game on the court. How can I help you today?
            </div>
        </div>
    `;

    userInput.focus();
});

// Focus input on load
userInput.focus();
