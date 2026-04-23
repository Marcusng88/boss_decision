import { useState, useEffect } from "react";
import { FolderOpen, Loader2, ArrowLeft, Folder } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { DocumentCard } from "./DocumentCard";

interface Document {
  source_id: number;
  doc_type: string;
  title: string;
  file_path: string;
  published_date: string | null;
  extracted_at: string | null;
  created_at: string;
}

interface DocumentListProps {
  refreshTrigger?: number;
}

export const DocumentList = ({ refreshTrigger }: DocumentListProps) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/documents");
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Failed to fetch documents:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
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
    { name: "Employee" },
  ];

  const getDocumentCount = (type: string) => {
    return documentsByType[type]?.length || 0;
  };

  const getFilteredDocuments = (type: string) => {
    return documentsByType[type] || [];
  };

  return (
    <Card className="border-2 border-orange-200 bg-white shadow-lg h-full">
      <div className="p-6">
        {/* Header with back button when folder is open */}
        <div className="flex items-center gap-3 mb-6">
          {selectedFolder && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedFolder(null)}
              className="text-orange-700 hover:text-orange-900 hover:bg-orange-100"
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
          )}
          <div className="w-10 h-10 rounded-lg bg-orange-400 flex items-center justify-center">
            <FolderOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {selectedFolder || "My Documents"}
            </h2>
            <p className="text-sm text-gray-600">
              {selectedFolder 
                ? `${getDocumentCount(selectedFolder)} document${getDocumentCount(selectedFolder) !== 1 ? 's' : ''} in this folder`
                : "Browse and manage uploaded documents by category"
              }
            </p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-orange-600 animate-spin" />
          </div>
        ) : selectedFolder ? (
          // Show documents in selected folder
          <div className="space-y-4">
            {getFilteredDocuments(selectedFolder).length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 mx-auto rounded-2xl bg-orange-100 flex items-center justify-center mb-4">
                  <FolderOpen className="w-8 h-8 text-orange-600" />
                </div>
                <p className="text-lg font-semibold text-gray-900 mb-2">
                  No documents yet
                </p>
                <p className="text-sm text-gray-600">
                  Upload documents to see them here
                </p>
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {getFilteredDocuments(selectedFolder).map(doc => (
                  <DocumentCard key={doc.source_id} document={doc} onDelete={fetchDocuments} />
                ))}
              </div>
            )}
          </div>
        ) : (
          // Show folder grid - Google Drive style
          <div className="grid gap-3 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-5">
            {folders.map((folder) => {
              const count = getDocumentCount(folder.name);
              return (
                <div
                  key={folder.name}
                  className="cursor-pointer hover:bg-gray-50 rounded-lg p-3 transition-all group border border-transparent hover:border-gray-200"
                  onClick={() => setSelectedFolder(folder.name)}
                >
                  {/* Folder Icon */}
                  <div className="mb-2">
                    <svg
                      className="w-full h-auto"
                      viewBox="0 0 24 24"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M10 4H4C2.89543 4 2 4.89543 2 6V18C2 19.1046 2.89543 20 4 20H20C21.1046 20 22 19.1046 22 18V8C22 6.89543 21.1046 6 20 6H12L10 4Z"
                        fill="#5F6368"
                        className="group-hover:fill-[#4285F4] transition-colors"
                      />
                    </svg>
                  </div>
                  
                  {/* Folder Info */}
                  <div>
                    <h3 className="font-medium text-gray-900 text-sm truncate mb-0.5">
                      {folder.name}
                    </h3>
                    <p className="text-xs text-gray-500">
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
