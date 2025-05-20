import { useChatbotLogic } from "../scripts/useChatbotLogic";
import { X, Send, Mic } from "lucide-react";
import styles from '../styles/ChatbotWidget.module.css';

const ChatbotWidget = () => {
  const {
    isOpen,
    setIsOpen,
    messages,
    input,
    setInput,
    isBotResponding,
    error,
    suggestions,
    formatTime,
    sendMessage,
    handleMicClick,
    bottomRef,
    messagesContainerRef,
    dismissNotice,
    clearNotice,
    isTyping,
  } = useChatbotLogic();

return (
    <div className={styles.chatbotContainer}>
      {!isOpen ? (
        <div className={styles.closedState}>
          <div className={styles.promoBanner}>
            Nhắn cho chúng tôi <span className={styles.waveAnimation}>👋</span>
          </div>
          <img
            onClick={() => setIsOpen(true)}
            src="/chat-bot.png"
            alt="Chat Icon"
            className={styles.chatIcon}
          />
        </div>
      ) : (
        <div className={styles.openState}>
          {/* Header */}
          <div className={styles.header}>
            <span className={styles.headerTitle}>Xin chào 👋</span>

            <button
              onClick={() => setIsOpen(false)}
              className={styles.closeButton}
            >
              <X size={20} />
            </button>
          </div>

          {/* Messages */}
          <div className={styles.messagesContainer} ref={messagesContainerRef}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`${styles.messageWrapper} ${
                  msg.from === "bot" ? styles.messageWrapperBot : styles.messageWrapperUser
                }`}
              >
                {msg.from === "bot" && (
                  <img src="/chat-bot.png" alt="Bot Avatar" className={styles.avatar} />
                )}

                <span className={`${styles.messageBubble} ${
                  msg.from === "bot" ? styles.messageBubbleBot : styles.messageBubbleUser
                }`}>
                  {msg.text}
                </span>
                  {/* Source */}
                <div className={styles.timestamp}>
                  <span>{formatTime(msg.timestamp)}</span>
                  {msg.from === "bot" && msg.sources && msg.sources.length > 0 && (
                    <>
                      <span>📎 Source:</span>
                      <a
                        href={msg.sources[0].url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={styles.sourceLink}
                      >
                        here
                      </a>
                    </>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className={styles.typingIndicator}>
                <span className={styles.typingBubble}>
                  <span className={styles.typingText}>Đang nhập...</span>
                </span>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
          
          {/* Inactive Notice */}
          {clearNotice && (
            <div className={styles.clearNotice}>
              <span>{clearNotice.text}</span>
              <button 
                onClick={() => dismissNotice(clearNotice.id)}
                className={styles.dismissButton}
              >
                ×
              </button>
            </div>
          )}

          {/* Suggestions */}
       
          <div className={styles.suggestionsContainer}>
            {suggestions.map((text, idx) => (
              <button
                key={idx}
                onClick={() => sendMessage(text)}
                className={styles.suggestionButton}
              >
                {text}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div className={styles.inputArea}>
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && sendMessage()}
              className={styles.inputField}
              placeholder="Enter your message..."
            />
            {/* Void and Send Button */}
            <div className={styles.voiceButtonContainer}>
              <button
                onClick={handleMicClick}
                aria-label="Voice input"
                className={`${styles.voiceButton} ${
                  input.trim() ? `${styles.voiceButtonHidden} ${styles.micButtonHidden}` : styles.voiceButtonVisible
                }`}
                disabled={isBotResponding}
              >
                <Mic size={24} />
              </button>
              <button
                onClick={() => sendMessage()}
                aria-label="Send input"
                className={`${styles.voiceButton} ${
                  input.trim() ? `${styles.voiceButtonVisible} ${styles.sendButtonBounce}` : styles.voiceButtonHidden
                }`}
                disabled={isBotResponding}
              >
                <Send size={24} />
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className={styles.errorMessage}>
              <span>{error}</span>
            </div>
          )}
          {/* Footer Text */}
          <div className={styles.footerText}>
            <span>Powered by <a href="https://watatek.com" target="_blank" rel="noopener noreferrer">watatek.com</a></span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotWidget;
