import { useState, useEffect } from "react";
import { FolderOpen, Loader2, ArrowLeft } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DocumentCard } from "./DocumentCard";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const LOCAL_MOCK_UPLOADS_KEY = "documents.mockUploads.v1";

interface Document {
  source_id: number;
  doc_type: string;
  title: string;
  file_path: string;
  published_date: string | null;
  extracted_at: string | null;
  created_at: string;
  mock_source?: "seed" | "local_upload";
}

const MOCK_DOCUMENTS: Document[] = [
  {
    source_id: 900001,
    doc_type: "HR Report",
    title: "Q1 Performance Review - Sales Team",
    file_path: "https://example.com/mock/hr-q1-performance.pdf",
    published_date: "2026-03-28",
    extracted_at: "2026-03-28T08:30:00Z",
    created_at: "2026-03-28T08:00:00Z",
    mock_source: "seed",
  },
  {
    source_id: 900002,
    doc_type: "Sales Log",
    title: "Enterprise Pipeline Snapshot",
    file_path: "https://example.com/mock/sales-pipeline-apr.docx",
    published_date: "2026-04-10",
    extracted_at: "2026-04-10T03:10:00Z",
    created_at: "2026-04-10T03:00:00Z",
    mock_source: "seed",
  },
  {
    source_id: 900003,
    doc_type: "Supply Chain Log",
    title: "Supplier Lead Time Variance",
    file_path: "https://example.com/mock/supply-variance.md",
    published_date: "2026-04-16",
    extracted_at: "2026-04-16T10:05:00Z",
    created_at: "2026-04-16T10:00:00Z",
    mock_source: "seed",
  },
  {
    source_id: 900004,
    doc_type: "Legal Policy",
    title: "Termination and PIP Policy 2026",
    file_path: "https://example.com/mock/legal-pip-policy.pdf",
    published_date: "2026-01-12",
    extracted_at: "2026-01-12T09:15:00Z",
    created_at: "2026-01-12T09:00:00Z",
    mock_source: "seed",
  },
  {
    source_id: 900005,
    doc_type: "Finance Report",
    title: "Severance Cost Impact Model",
    file_path: "https://example.com/mock/finance-severance-cost.xlsx",
    published_date: "2026-02-04",
    extracted_at: "2026-02-04T07:45:00Z",
    created_at: "2026-02-04T07:30:00Z",
    mock_source: "seed",
  },
];

interface DocumentListProps {
  refreshTrigger?: number;
}

export const DocumentList = ({ refreshTrigger }: DocumentListProps) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [usingMockData, setUsingMockData] = useState(false);
  const [localMockUploads, setLocalMockUploads] = useState<Document[]>([]);

  const loadLocalMockUploads = () => {
    try {
      const raw = localStorage.getItem(LOCAL_MOCK_UPLOADS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      const safe = Array.isArray(parsed) ? parsed : [];
      setLocalMockUploads(safe);
      return safe;
    } catch (error) {
      console.error("Failed to load local mock uploads:", error);
      setLocalMockUploads([]);
      return [];
    }
  };

  const removeLocalMockUpload = (sourceId: number) => {
    try {
      const raw = localStorage.getItem(LOCAL_MOCK_UPLOADS_KEY);
      const parsed = raw ? JSON.parse(raw) : [];
      const safe = Array.isArray(parsed) ? parsed : [];
      const next = safe.filter((doc: Document) => doc.source_id !== sourceId);
      localStorage.setItem(LOCAL_MOCK_UPLOADS_KEY, JSON.stringify(next));
      setLocalMockUploads(next);
      setDocuments((prev) => prev.filter((doc) => doc.source_id !== sourceId));
    } catch (error) {
      console.error("Failed to remove local mock upload:", error);
    }
  };

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/api/documents`);
      if (!response.ok) {
        throw new Error(`Failed to fetch documents: ${response.status}`);
      }
      const data = await response.json();
      const localUploads = loadLocalMockUploads();
      setDocuments([...(data.documents || []), ...localUploads]);
      setUsingMockData(false);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
      const localUploads = loadLocalMockUploads();
      setDocuments([...localUploads, ...MOCK_DOCUMENTS]);
      setUsingMockData(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadLocalMockUploads();
    fetchDocuments();
  }, [refreshTrigger]);

  // Group documents by type
  const documentsByType = documents.reduce((acc, doc) => {
    const type = doc.doc_type || "Unknown";
    if (!acc[type]) {
      acc[type] = [];
    }
    acc[type].push(doc);
    return acc;
  }, {} as Record<string, Document[]>);

  // Folder configuration
  const folders = [
    { name: "HR Report" },
    { name: "Sales Log" },
    { name: "Finance Report" },
    { name: "Marketing Report" },
    { name: "Supply Chain Log" },
    { name: "Legal Policy" },
    { name: "Legal Contract" },
    { name: "Legal Case" },
    { name: "Employee" },
  ];

  const getDocumentCount = (type: string) => {
    return documentsByType[type]?.length || 0;
  };

  const getFilteredDocuments = (type: string) => {
    return documentsByType[type] || [];
  };

  return (
    <Card className="border border-gray-200/40 bg-white/70 backdrop-blur-sm shadow-lg shadow-gray-900/5 h-full rounded-2xl transition-all duration-300 hover:shadow-xl hover:shadow-gray-900/10">
      <div className="p-6">
        {/* Header with back button when folder is open */}
        <div className="flex items-center gap-3 mb-6">
          {selectedFolder && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedFolder(null)}
              className="text-gray-600 hover:text-gray-800 hover:bg-gray-100/50 rounded-full transition-all duration-200"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-br from-orange-400/90 to-orange-500/90 flex items-center justify-center shadow-md shadow-orange-500/20">
            <FolderOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-800 tracking-tight">
              {selectedFolder || "My Documents"}
            </h2>
            <p className="text-sm text-gray-500 font-light">
              {selectedFolder 
                ? `${getDocumentCount(selectedFolder)} document${getDocumentCount(selectedFolder) !== 1 ? 's' : ''} in this folder`
                : "Browse and manage uploaded documents by category"
              }
            </p>
            {usingMockData && (
              <p className="text-xs text-amber-700 font-medium mt-1">
                Backend unavailable, showing mock documents.
              </p>
            )}
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-orange-500 animate-spin" />
          </div>
        ) : selectedFolder ? (
          // Show documents in selected folder
          <div className="space-y-4">
            {getFilteredDocuments(selectedFolder).length === 0 ? (
              <div className="text-center py-16">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-orange-100/80 to-amber-100/60 flex items-center justify-center mb-4 shadow-sm">
                  <FolderOpen className="w-8 h-8 text-orange-500" />
                </div>
                <p className="text-base font-medium text-gray-700 mb-2">
                  No documents yet
                </p>
                <p className="text-sm text-gray-500 font-light">
                  Upload documents to see them here
                </p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {getFilteredDocuments(selectedFolder).map(doc => (
                  <DocumentCard
                    key={doc.source_id}
                    document={doc}
                    onDelete={fetchDocuments}
                    onDeleteLocal={removeLocalMockUpload}
                  />
                ))}
              </div>
            )}
          </div>
        ) : (
          // Show folder grid - Google Drive style
          <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
            {folders.map((folder) => {
              const count = getDocumentCount(folder.name);
              return (
                <div
                  key={folder.name}
                  className="cursor-pointer hover:bg-gradient-to-br hover:from-orange-50/30 hover:to-amber-50/20 rounded-2xl p-4 transition-all duration-300 group border border-gray-200/30 hover:border-orange-200/60 hover:shadow-md hover:shadow-gray-900/5 hover:scale-[1.02]"
                  onClick={() => setSelectedFolder(folder.name)}
                >
                  {/* Folder Icon */}
                  <div className="mb-3">
                    <svg
                      className="w-full h-auto"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M10 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20H20C21.1046 20 22 19.1046 22 18V8C22 6.89543 21.1046 6 20 6H12L10 4Z"
                        fill="#9CA3AF"
                        className="group-hover:fill-orange-400 transition-colors duration-300"
                      />
                    </svg>
                  </div>
                  
                  {/* Folder Info */}
                  <div>
                    <h3 className="font-medium text-gray-700 text-sm truncate mb-1 group-hover:text-gray-800 transition-colors">
                      {folder.name}
                    </h3>
                    <p className="text-xs text-gray-400 font-light">
                      {count} file{count !== 1 ? 's' : ''}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
};
