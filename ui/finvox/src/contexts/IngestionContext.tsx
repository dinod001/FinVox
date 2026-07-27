import React, { createContext, useContext, useState } from 'react';
import { ingestApi } from '../api/ingest';
import type { IngestionResponse } from '../api/ingest';

interface IngestionContextType {
  isUploading: boolean;
  uploadError: string | null;
  response: IngestionResponse | null;
  startUpload: (file: File, userId: string, description: string) => Promise<void>;
  resetState: () => void;
}

const IngestionContext = createContext<IngestionContextType | undefined>(undefined);

export const IngestionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [response, setResponse] = useState<IngestionResponse | null>(null);

  const startUpload = async (file: File, userId: string, description: string) => {
    if (isUploading) return;
    
    setIsUploading(true);
    setUploadError(null);
    setResponse(null);
    
    try {
      const res = await ingestApi.uploadFile(file, userId, description);
      setResponse(res);
    } catch (err: any) {
      setUploadError(err.message || 'Failed to upload file');
    } finally {
      setIsUploading(false);
    }
  };

  const resetState = () => {
    setUploadError(null);
    setResponse(null);
    setIsUploading(false);
  };

  return (
    <IngestionContext.Provider value={{ isUploading, uploadError, response, startUpload, resetState }}>
      {children}
    </IngestionContext.Provider>
  );
};

export const useIngestion = () => {
  const context = useContext(IngestionContext);
  if (context === undefined) {
    throw new Error('useIngestion must be used within an IngestionProvider');
  }
  return context;
};
