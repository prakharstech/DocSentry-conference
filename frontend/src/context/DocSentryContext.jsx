import React, { createContext, useContext, useState } from 'react';

const DocSentryContext = createContext();

export const DocSentryProvider = ({ children }) => {
  // Chat State
  const [messages, setMessages] = useState([]);
  const [file, setFile] = useState(null);
  const [isReady, setIsReady] = useState(false);
  const [uploadStats, setUploadStats] = useState(null);
  
  // Document Cache (for evaluation)
  const [currentDocText, setCurrentDocText] = useState('');
  const [currentDocFindings, setCurrentDocFindings] = useState([]);

  // Evaluation State
  const [evalResults, setEvalResults] = useState(null);

  const resetSession = () => {
    setMessages([]);
    setFile(null);
    setIsReady(false);
    setUploadStats(null);
    setCurrentDocText('');
    setCurrentDocFindings([]);
    setEvalResults(null);
  };

  return (
    <DocSentryContext.Provider value={{
      messages, setMessages,
      file, setFile,
      isReady, setIsReady,
      uploadStats, setUploadStats,
      currentDocText, setCurrentDocText,
      currentDocFindings, setCurrentDocFindings,
      evalResults, setEvalResults,
      resetSession
    }}>
      {children}
    </DocSentryContext.Provider>
  );
};

export const useDocSentry = () => {
  const context = useContext(DocSentryContext);
  if (!context) {
    throw new Error('useDocSentry must be used within a DocSentryProvider');
  }
  return context;
};
