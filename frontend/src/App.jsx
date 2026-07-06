import { useState, useEffect, useRef } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Suggestions for empty state
  const suggestions = [
    { text: "How do I create a new mentor?", label: "Create Mentor" },
    { text: "What is the confidence score threshold?", label: "Threshold Info" },
    { text: "Can you help me submit a support ticket?", label: "Support Ticket" },
    { text: "How does the RAG search pipeline work?", label: "Pipeline Details" }
  ];

  // Auto-scroll to the bottom of the chat
  useEffect(() => {
    console.log("[Chat] Auto-scrolling to bottom. Message count:", messages.length);
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Check connection to backend on load
  useEffect(() => {
    console.log("[Connection] Checking backend connection status on load...");
    const checkConnection = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/health");
        if (res.ok) {
          console.log("[Connection] Backend is online and responding.");
          setIsConnected(true);
        } else {
          console.warn("[Connection] Backend returned non-OK status:", res.status);
          setIsConnected(false);
        }
      } catch (err) {
        console.error("[Connection] Failed to connect to backend:", err);
        setIsConnected(false);
      }
    };
    checkConnection();
  }, []);

  // Handle textarea autosize
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || message;
    if (!text.trim()) {
      console.warn("[Chat] Attempted to send empty message. Aborting.");
      return;
    }
    if (loading) {
      console.warn("[Chat] System is currently loading another response. Aborting.");
      return;
    }

    console.log("[Chat] Preparing to send message:", text);

    // Add user message to history
    const userMsg = {
      id: Date.now(),
      text: text,
      isUser: true,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    console.log("[Chat] Appending user message to chat UI:", userMsg);
    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setMessage("");
    setLoading(true);

    try {
      const payload = {
        user_id: "test_user",
        message: text,
      };
      console.log("[Chat] Dispatching API request to http://127.0.0.1:8000/chat with payload:", payload);

      const response = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        console.error("[Chat] API request failed with status:", response.status, response.statusText);
        throw new Error("Server error");
      }

      const data = await response.json();
      console.log("[Chat] API response successfully received:", data);

      const botMsg = {
        id: Date.now() + 1,
        text: data.answer,
        isUser: false,
        confidence: data.confidence,
        escalated: data.escalated,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      console.log("[Chat] Appending assistant response to chat UI:", botMsg);
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      console.error("[Chat] Error occurred during message processing:", err);
      const errorMsg = {
        id: Date.now() + 1,
        text: "Unable to connect to the backend server. Please make sure the backend is running.",
        isUser: false,
        isError: true,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      console.log("[Chat] Enter key pressed. Submitting message.");
      handleSendMessage();
    }
  };

  const clearChat = () => {
    console.log("[Chat] Requesting clear chat history.");
    if (window.confirm("Are you sure you want to clear your chat history?")) {
      console.log("[Chat] Chat history cleared.");
      setMessages([]);
    } else {
      console.log("[Chat] Clear chat cancelled by user.");
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="header-title-area">
          <div className="bot-avatar-main">🤖</div>
          <div className="header-text">
            <h1>TEF AI Assistant</h1>
            <div className="status-badge">
              <span className="status-dot" style={{ backgroundColor: isConnected ? "#2ec4b6" : "#e71d36" }} />
              {isConnected ? "Server Online" : "Server Offline"}
            </div>
          </div>
        </div>
        {messages.length > 0 && (
          <button className="clear-btn" onClick={clearChat} title="Clear history">
            <span>🗑️</span> Clear Chat
          </button>
        )}
      </header>

      {/* Main Chat Area */}
      <main className="chat-area">
        {messages.length === 0 ? (
          <div className="welcome-container">
            <div className="welcome-logo">🤖</div>
            <h2>Welcome to TEF Support</h2>
            <p className="welcome-desc">
              Ask any question about mentor creation, support ticket processing, or configuration settings.
              Our RAG-powered agent is here to help!
            </p>
            <div className="suggestions-title">Suggested questions:</div>
            <div className="suggestions-grid">
              {suggestions.map((s, index) => (
                <button
                  key={index}
                  className="suggestion-card"
                  onClick={() => handleSendMessage(s.text)}
                >
                  <span>{s.label}</span>
                  <p style={{ color: "var(--text-muted)", fontSize: "13px", marginTop: "4px" }}>
                    {s.text}
                  </p>
                  <span className="suggestion-arrow">→</span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg) => (
            <div key={msg.id} className={`message-row ${msg.isUser ? "user-row" : "bot-row"}`}>
              <div className={`avatar ${msg.isUser ? "user-avatar" : "bot-avatar"}`}>
                {msg.isUser ? "👤" : "🤖"}
              </div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <div className={`message-bubble ${msg.isUser ? "user-bubble" : "bot-bubble"}`} style={msg.isError ? { borderLeft: "4px solid #e71d36" } : {}}>
                  {msg.text}

                  {/* Escalation warning */}
                  {!msg.isUser && msg.escalated && (
                    <div className="escalation-notice">
                      <span className="escalation-icon">⚠️</span>
                      <div>
                        <div className="escalation-title">Escalated to Support Ticket</div>
                        This answer has lower confidence. A support ticket has been created automatically for human review.
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Message Meta (time & confidence) */}
                <div className="message-meta">
                  <span>{msg.time}</span>
                  {!msg.isUser && msg.confidence !== undefined && (
                    <span className={`confidence-pill ${msg.confidence < 0.6 ? "low" : ""}`}>
                      Confidence: {Math.round(msg.confidence * 100)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {/* Loading Indicator */}
        {loading && (
          <div className="message-row bot-row">
            <div className="avatar bot-avatar">🤖</div>
            <div className="message-bubble bot-bubble">
              <div className="typing-container">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </main>

      {/* Footer / Input Area */}
      <footer className="app-footer">
        <div className="input-container">
          <textarea
            ref={textareaRef}
            className="chat-input"
            rows="1"
            placeholder="Type your message here..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={() => handleSendMessage()}
            disabled={loading || !message.trim()}
          >
            <span className="send-icon">▲</span>
          </button>
        </div>
        <div className="footer-info">
          TEF Chatbot answers queries using local FAQs and Knowledge Base documents.
        </div>
      </footer>
    </div>
  );
}

export default App;
