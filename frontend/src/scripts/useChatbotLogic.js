import { useState, useRef, useEffect, useCallback } from "react";
import { suggestions } from '../data/suggestions.ts';

export const useChatbotLogic = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState(() => {
    // Lấy lịch sử trò chuyện từ localStorage (nếu có)
    const savedMessages = localStorage.getItem("chatHistory");
    return savedMessages ? JSON.parse(savedMessages) : [
      { from: "bot", text: "Xin chào, tôi có thể giúp gì cho bạn? 😊", timestamp: new Date() },
    ];
  });
  const [input, setInput] = useState("");
  const [isBotResponding, setIsBotResponding] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);
  const recognitionRef = useRef(null);
  const messagesContainerRef = useRef(null); 
  const timeoutRef = useRef(null); // Thêm ref để lưu timeout
  const [clearNotice, setClearNotice] = useState(null);
  const availableModels = [
    { name: "LLaMA 4", value: process.env.REACT_APP_MODELS }
  ];
  const apiUrl = process.env.REACT_APP_API_URL;
  const [selectedModel, setSelectedModel] = useState(availableModels[0].value);

  const formatTime = (date) =>
    new Date(date).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    });
  
  //Dismiss Notice
  const dismissNotice = (id) => {
    setClearNotice(prev => prev?.id === id ? null : prev);
  };
  
  //Chat History
  const clearChatHistory = useCallback(() => {
    const currentMessages = JSON.parse(localStorage.getItem("chatHistory") || "[]");
    const hasUserMessages = currentMessages.some(msg => msg.from === "user");
  
    if (hasUserMessages) {
      localStorage.removeItem("chatHistory");
      setMessages([{ from: "bot", text: "Xin chào, tôi có thể giúp gì cho bạn? 😊", timestamp: new Date() }]);
      
      // Hiển thị thông báo có thể tắt
      setClearNotice({
        id: Date.now(),
        text: "Lịch sử trò chuyện bị xóa do không hoạt động."
      });
    }
  },[setMessages]);

  const resetAutoClearTimer = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
  
    const hasUserMessages = messages.some(msg => msg.from === "user");
    if (hasUserMessages) {
      timeoutRef.current = setTimeout(() => {
        clearChatHistory();
      }, 10 * 60 * 1000);
    }
  }, [messages, clearChatHistory]); // Include all dependencies used inside

  useEffect(() => {
    // Thiết lập bộ đếm thời gian khi component mount
    resetAutoClearTimer();

    // Xóa timeout khi component unmount
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [resetAutoClearTimer]);

  useEffect(() => {
    localStorage.setItem("chatIsOpen", JSON.stringify(isOpen));
  }, [isOpen]);

  //Message
  const addMessage = (msg) => {
    setMessages((prev) => {
      const updatedMessages = [...prev, { ...msg, timestamp: new Date() }];
      localStorage.setItem("chatHistory", JSON.stringify(updatedMessages));
      
      // Chỉ reset timer nếu là tin nhắn từ user
      if (msg.from === "user") {
        resetAutoClearTimer();
      }
      
      return updatedMessages;
    });
  };

  const sendMessage = async (text = input) => {
    if (!text.trim() || isBotResponding) return;

    // Thêm message của user
    addMessage({ from: "user", text });
    setInput("");
    setIsBotResponding(true);
    setIsTyping(true)
    setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 50);

    try {
      const res = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, model: selectedModel }),
      });
  
      const data = await res.json();
  
      // Sử dụng streamBotResponse để hiển thị từ từ
      streamBotResponse(data.reply, data.sources || []);
  
    } catch (err) {
      console.error(err);
      setError("Bot is currently unavailable. Please try again.");
      
      // Fallback response khi có lỗi
      streamBotResponse("Sorry, I'm having trouble connecting. Please try again later.", []);
      
    } finally {
      setIsTyping(false);
    }
  };

  //Streaming Text
  const streamBotResponse = (fullText, sources) => {
    console.log(sources);
    setError("");
    let index = 0;

    setMessages((prev) => [
      ...prev,
      { from: "bot", text: "Typing...", streaming: true, timestamp: new Date() },
    ]);

    const interval = setInterval(() => {
      index += 1;
      const currentText = fullText.slice(0, index);

      setMessages((prev) => {
        const last = prev[prev.length - 1];
        if (last.from === "bot" && last.streaming) {
          const updated = [...prev];
          updated[updated.length - 1] = {
            ...last,
            text: currentText,
            timestamp: new Date(),
            sources,
          };
          localStorage.setItem("chatHistory", JSON.stringify(updated));
          return updated;
        } else {
          return [
            ...prev,
            {
              from: "bot",
              text: currentText,
              streaming: true,
              timestamp: new Date(),
              sources,
            },
          ];
        }
      });

      if (index >= fullText.length) {
        clearInterval(interval);
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 ? { ...m, text: fullText, streaming: false, sources: m.sources } : m
          )
        );
        setIsBotResponding(false);
      }
    }, 30);
  };

  //Scroll Bar
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
  
    const isAtBottom =
      container.scrollHeight - container.scrollTop <= container.clientHeight + 30;
  
    if (isAtBottom) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  //Mic
  const handleMicClick = () => {
    if (!("webkitSpeechRecognition" in window)) {
      alert("Your browser does not support speech recognition.");
      return;
    }

    if (!recognitionRef.current) {
      const recognition = new window.webkitSpeechRecognition();
      recognition.lang = "en-US";
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        sendMessage(transcript);
      };

      recognition.onerror = (e) => {
        alert("Speech recognition error: " + e.error);
      };

      recognitionRef.current = recognition;
    }

    recognitionRef.current.start();
  };

  return {
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
    selectedModel,
    setSelectedModel,
    availableModels,
    dismissNotice,
    clearNotice,
    isTyping
  };
};