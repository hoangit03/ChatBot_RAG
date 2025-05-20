import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useNavigate } from 'react-router-dom';

import ChatbotWidget from './components/ChatbotWidget';

function Redirector() {
  const navigate = useNavigate();

  useEffect(() => {
    // Chuyển hướng người dùng đến /wata/ai ngay khi ứng dụng khởi động
    navigate('/wata/ai');
  }, [navigate]);

  return null;  // Không cần hiển thị gì ở đây
}

function App() {
  return (
    <Router>
      <Redirector /> {/* Component điều hướng ngay khi khởi động */}
      <Routes>
        <Route path="/wata/ai" element={<ChatbotWidget />} />
      </Routes>
    </Router>
  );
}

export default App;
