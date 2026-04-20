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
  const [currentAnonymizedText, setCurrentAnonymizedText] = useState('');
  const [currentDocFindings, setCurrentDocFindings] = useState([]);

  // Evaluation State
  const [evalResults, setEvalResults] = useState(null);

  // Persisted Form State for Evaluation Page
  const [piiText, setPiiText] = useState('Jim Halpert lives in Scranton, Pennsylvania. He was born on 2024-05-12 and has Asthma. His email is m.scott@example-paper.com and SSN is 123-45-6789.');
  const [groundTruthJson, setGroundTruthJson] = useState('[\n  {"text": "Jim Halpert", "type": "PERSON"},\n  {"text": "Scranton, Pennsylvania", "type": "LOCATION"},\n  {"text": "2024-05-12", "type": "DATE"},\n  {"text": "Asthma", "type": "CONDITION"},\n  {"text": "m.scott@example-paper.com", "type": "CONTACT"},\n  {"text": "123-45-6789", "type": "SSN"}\n]');
  const [anonResults, setAnonResults] = useState(null);
  const [ragResults, setRagResults] = useState(null);
  const [overallResults, setOverallResults] = useState(null);

  const resetSession = () => {
    setMessages([]);
    setFile(null);
    setIsReady(false);
    setUploadStats(null);
    setCurrentDocText('');
    setCurrentAnonymizedText('');
    setCurrentDocFindings([]);
    setEvalResults(null);
    setPiiText('Jim Halpert lives in Scranton, Pennsylvania. He was born on 2024-05-12 and has Asthma. His email is m.scott@example-paper.com and SSN is 123-45-6789.');
    setGroundTruthJson('[\n  {"text": "Jim Halpert", "type": "PERSON"},\n  {"text": "Scranton, Pennsylvania", "type": "LOCATION"},\n  {"text": "2024-05-12", "type": "DATE"},\n  {"text": "Asthma", "type": "CONDITION"},\n  {"text": "m.scott@example-paper.com", "type": "CONTACT"},\n  {"text": "123-45-6789", "type": "SSN"}\n]');
    setAnonResults(null);
    setRagResults(null);
    setOverallResults(null);
  };

  return (
    <DocSentryContext.Provider value={{
      messages, setMessages,
      file, setFile,
      isReady, setIsReady,
      uploadStats, setUploadStats,
      currentDocText, setCurrentDocText,
      currentAnonymizedText, setCurrentAnonymizedText,
      currentDocFindings, setCurrentDocFindings,
      evalResults, setEvalResults,
      piiText, setPiiText,
      groundTruthJson, setGroundTruthJson,
      anonResults, setAnonResults,
      ragResults, setRagResults,
      overallResults, setOverallResults,
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
