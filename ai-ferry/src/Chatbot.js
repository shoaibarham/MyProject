import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
// Import CSS for styling
import './Chatbot.css';

const API_BASE_URL = "http://127.0.0.1:8000"; 


const Chatbot = () => {
  const [messages, setMessages] = useState(() => {
    const savedMessages = sessionStorage.getItem('chatMessages');
    return savedMessages ? JSON.parse(savedMessages) : [{ role: "assistant", content: "Hello! How can I assist you with ferry bookings?" }];
  });
  const [userQuery, setUserQuery] = useState("");
  const [randomQuestions, setRandomQuestions] = useState([]);
  const [dynamicQuestions, setDynamicQuestions] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [editIndex, setEditIndex] = useState(null);
  const [editContent, setEditContent] = useState("");
  const [isAutoScrollEnabled, setIsAutoScrollEnabled] = useState(true);
  const [showScrollDownIndicator, setShowScrollDownIndicator] = useState(false);
  const chatBoxRef = useRef(null);

  const recommendationQuestions = [
    "How long does it take to travel from Kimolos to Sifnos?",
    "What is the price for a ferry from Athens to Santorini?",
    "Are there any ferries available on July 15th?",
    "Can you provide the schedule for ferries from Mykonos?",
    "What is the cheapest route from Naxos to Paros?"
  ];

  useEffect(() => {
    const shuffledQuestions = recommendationQuestions.sort(() => 0.5 - Math.random());
    setRandomQuestions(shuffledQuestions.slice(0, 3)); 
  }, []);

  useEffect(() => {
    sessionStorage.setItem('chatMessages', JSON.stringify(messages));
    if (isAutoScrollEnabled) {
      scrollToBottom();
    } else {
      checkIfScrollDownIndicatorNeeded();
    }
  }, [messages]);

  

  const sendMessage = async (query, index = null) => {
    if (!query.trim()) return;

    const newMessages = index !== null ? [...messages] : [...messages, { role: "user", content: query }];
    if (index !== null) {
      newMessages[index] = { ...newMessages[index], content: query };
    }
    setMessages(newMessages);
    setUserQuery("");
    setIsTyping(true);

    try {
      const response = await axios.get(`${API_BASE_URL}/chat/`, {
        params: { query },
      });
      

      const chatbotReply = response.data.response || "I couldn't fetch a response.";
      const newDynamicQuestions = response.data.dynamic_questions || [];
      setDynamicQuestions(newDynamicQuestions);

      if (index !== null) {
        newMessages[index + 1] = { role: "assistant", content: chatbotReply };
      } else {
        newMessages.push({ role: "assistant", content: chatbotReply });
      }
      setMessages(newMessages);
    } catch (error) {
      if (index !== null) {
        newMessages[index + 1] = { role: "assistant", content: "Error connecting to AI chat service." };
      } else {
        newMessages.push({ role: "assistant", content: "Error connecting to AI chat service." });
      }
      setMessages(newMessages);
    } finally {
      setIsTyping(false);
      if (index !== null) {
        highlightMessage(index + 1);
      }
    }
  };

  const handleRecommendationClick = (question) => {
    setUserQuery(question);
    setRandomQuestions(randomQuestions.filter(q => q !== question));
  };

  const handleDynamicQuestionClick = (question) => {
    setUserQuery(question);
    setDynamicQuestions(dynamicQuestions.filter(q => q !== question));
  };

  const handleEditClick = (index) => {
    setEditIndex(index);
    setEditContent(messages[index].content);
  };

  const handleEditSubmit = () => {
    sendMessage(editContent, editIndex);
    setEditIndex(null);
    setEditContent("");
  };

  const highlightMessage = (index) => {
    const messageElement = chatBoxRef.current.children[index];
    if (messageElement) {
      messageElement.classList.add("highlight");
      setTimeout(() => {
        messageElement.classList.remove("highlight");
      }, 2000);
    }
  };

  const scrollToBottom = () => {
    chatBoxRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
  };

  const checkIfScrollDownIndicatorNeeded = () => {
    const chatBox = chatBoxRef.current;
    if (chatBox.scrollHeight > chatBox.clientHeight && chatBox.scrollTop + chatBox.clientHeight < chatBox.scrollHeight) {
      setShowScrollDownIndicator(true);
    } else {
      setShowScrollDownIndicator(false);
    }
  };

  const handleScroll = () => {
    const chatBox = chatBoxRef.current;
    if (chatBox.scrollTop + chatBox.clientHeight >= chatBox.scrollHeight) {
      setIsAutoScrollEnabled(true);
      setShowScrollDownIndicator(false);
    } else {
      setIsAutoScrollEnabled(false);
      checkIfScrollDownIndicatorNeeded();
    }
  };

  return (
    <div className="chat-container">
      <h1 className="chat-title">
        {/* <i className="fas fa-ship"></i> Ferry Chatbot */}
      </h1>
      <div className="chat-box" ref={chatBoxRef} onScroll={handleScroll}>
        {messages.map((msg, index) => (
          <div key={index} className={`chat-message ${msg.role === "user" ? "user-message" : "assistant-message"}`}>
            {editIndex === index ? (
              <div className="edit-container">
                <input
                  type="text"
                  value={editContent}
                  onChange={(e) => setEditContent(e.target.value)}
                  className="edit-input"
                />
                <button onClick={handleEditSubmit} className="edit-submit-button">Submit</button>
              </div>
            ) : (
              <>
                {msg.content}
                {msg.role === "user" && (
                  <button onClick={() => handleEditClick(index)} className="edit-button"></button>
                )}
              </>
            )}
          </div>
        ))}
        {isTyping && (
          <div className="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
          </div>
        )}
      </div>
      {showScrollDownIndicator && (
        <div className="scroll-down-indicator" onClick={scrollToBottom}>
          ↓ New Messages
        </div>
      )}
      <div className="chat-input-container">
        <input
          type="text"
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          className="chat-input"
          placeholder="Ask about ferry schedules, pricing, or routes..."
        />
        <button onClick={() => sendMessage(userQuery)} className="chat-button">Send</button>
      </div>
      <div className="recommendations-container">
        <div className="recommendations">
          {randomQuestions.map((question, index) => (
            <button
              key={index}
              className="recommendation-button"
              onClick={() => handleRecommendationClick(question)}
            >
              {question}
            </button>
          ))}
        </div>
        <div className="dynamic-recommendations">
          {dynamicQuestions.map((question, index) => (
            <button
              key={index}
              className="recommendation-button"
              onClick={() => handleDynamicQuestionClick(question)}
            >
              {question}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
