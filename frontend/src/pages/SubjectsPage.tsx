import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, Clock, Trash2, Sparkles, Network, ArrowRight } from 'lucide-react';
import { apiClient } from '../api/client';
import { useStudyStore } from '../store/useStudyStore';

export const SubjectsPage: React.FC = () => {
  const navigate = useNavigate();
  const { startSession } = useStudyStore();

  const [documents, setDocuments] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const fetchDocuments = async () => {
    setIsLoading(true);
    try {
      const res = await apiClient.get('/documents/');
      setDocuments(res.data);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Could not load your document library.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    setIsUploading(true);
    setUploadSuccess('');
    setErrorMessage('');

    try {
      const res = await apiClient.post('/documents/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setUploadSuccess(`"${file.name}" was uploaded and queued for indexing.`);
      fetchDocuments();
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Document ingestion failed.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm('Are you sure you want to delete this study document?')) return;
    try {
      await apiClient.delete(`/documents/${docId}`);
      fetchDocuments();
    } catch (err: any) {
      setErrorMessage(err.response?.data?.error?.message || 'Document deletion failed.');
    }
  };

  const handleStartStudy = (concept: string) => {
    const sessionId = crypto.randomUUID();
    startSession(sessionId, concept);
    navigate('/study');
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white tracking-tight">Subject Knowledge Base</h2>
          <p className="text-xs text-[#9CA3AF] mt-1">
            Upload notes, lecture slides, assignments, and past papers. Your AI Study Companion parses and learns your material automatically.
          </p>
        </div>

        <button
          onClick={() => handleStartStudy('Binary Search Tree')}
          className="px-4 py-2.5 rounded-xl bg-[#6366F1] hover:bg-[#6366F1]/90 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-[#6366F1]/25 transition-all whitespace-nowrap self-start sm:self-auto"
        >
          <Sparkles className="w-4 h-4" />
          <span>Launch Study Companion</span>
        </button>
      </div>

      {errorMessage && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-xs text-red-400">
          {errorMessage}
        </div>
      )}

      {/* File Upload Dropzone */}
      <div className="glass-card p-8 rounded-2xl border-2 border-dashed border-[#232D3F] hover:border-[#6366F1]/50 transition-colors text-center relative">
        <input
          type="file"
          accept=".pdf,.docx,.pptx,.txt,.md,.html"
          onChange={handleFileUpload}
          disabled={isUploading}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
        />

        <div className="w-14 h-14 rounded-2xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center text-[#6366F1] mx-auto mb-4">
          <Upload className="w-7 h-7" />
        </div>

        <h3 className="text-sm font-bold text-white">
          {isUploading ? 'Ingesting Document & Building Vector Index...' : 'Drag & drop study materials here'}
        </h3>
        <p className="text-xs text-[#9CA3AF] mt-1">
          Supports PDF, DOCX, PPTX, TXT, Markdown (Max 50MB per file)
        </p>

        {uploadSuccess && (
          <div className="mt-4 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#10B981]/10 border border-[#10B981]/20 text-[#10B981] text-xs font-medium">
            <CheckCircle className="w-4 h-4" /> {uploadSuccess}
          </div>
        )}
      </div>

      {/* Ingested Document Library Table */}
      <div className="glass-card rounded-2xl border border-[#232D3F] overflow-hidden">
        <div className="px-6 py-4 border-b border-[#232D3F] flex items-center justify-between">
          <h3 className="font-bold text-sm text-white">Ingested Document Library</h3>
          <span className="text-xs text-[#9CA3AF]">{documents.length} Files Ingested</span>
        </div>

        {isLoading ? (
          <div className="p-8 text-center text-xs text-[#9CA3AF] animate-pulse">
            Loading document library...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-12 text-center">
            <FileText className="w-10 h-10 text-[#9CA3AF]/40 mx-auto mb-3" />
            <h4 className="text-sm font-semibold text-white">No documents uploaded yet</h4>
            <p className="text-xs text-[#9CA3AF] mt-1">Upload your first PDF or lecture slides to build your AI knowledge base.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-[#0B0F17] text-[#9CA3AF] uppercase text-[10px] tracking-wider border-b border-[#232D3F]">
                <tr>
                  <th className="px-6 py-3">Document Title</th>
                  <th className="px-6 py-3">Status</th>
                  <th className="px-6 py-3">Vector Chunks</th>
                  <th className="px-6 py-3">Uploaded</th>
                  <th className="px-6 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#232D3F]">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-[#232D3F]/30 transition-colors">
                    <td className="px-6 py-4 font-medium text-white flex items-center gap-3">
                      <FileText className="w-4 h-4 text-[#6366F1] shrink-0" />
                      <span className="truncate max-w-xs">{doc.title || doc.filename}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-[#10B981]/10 text-[#10B981] border border-[#10B981]/20 flex items-center gap-1.5 w-fit">
                        <CheckCircle className="w-3 h-3" /> {doc.status || 'READY'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-[#9CA3AF]">{doc.chunk_count} Chunks</td>
                    <td className="px-6 py-4 text-[#9CA3AF]">{new Date(doc.created_at).toLocaleDateString()}</td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDeleteDoc(doc.id)}
                        className="p-1.5 text-[#9CA3AF] hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Auto-Generated DAG Concept Graph Map */}
      <div className="glass-card p-6 rounded-2xl border border-[#232D3F]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-[#8B5CF6]" />
            <h3 className="font-bold text-sm text-white">Auto-Extracted Concept Knowledge Map</h3>
          </div>
          <span className="text-xs text-[#9CA3AF]">DAG Dependency Traversal</span>
        </div>

        <div className="p-4 rounded-xl bg-[#0B0F17] border border-[#232D3F] flex flex-wrap items-center justify-center gap-4 text-xs">
          {[
            { name: 'Binary Trees', type: 'Prerequisite', color: 'border-blue-500/30 text-blue-400' },
            { name: 'Binary Search Tree', type: 'Active Focus', color: 'border-[#6366F1] text-[#6366F1] font-bold' },
            { name: 'AVL Tree', type: 'Next Unlocked', color: 'border-[#10B981]/30 text-[#10B981]' },
            { name: 'Red-Black Tree', type: 'Advanced', color: 'border-[#8B5CF6]/30 text-[#8B5CF6]' },
          ].map((node, idx) => (
            <React.Fragment key={node.name}>
              <div
                onClick={() => handleStartStudy(node.name)}
                className={`px-4 py-2.5 rounded-xl bg-[#161B26] border ${node.color} cursor-pointer hover:scale-105 transition-transform flex items-center gap-2 shadow-md`}
              >
                <span>{node.name}</span>
              </div>
              {idx < 3 && <ArrowRight className="w-4 h-4 text-[#9CA3AF]/40 shrink-0" />}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
};
