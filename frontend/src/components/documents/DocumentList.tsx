import { useState, useEffect } from "react";
import { FolderOpen, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  const [activeTab, setActiveTab] = useState<string>("all");

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

  const documentTypes = ["All", "HR Report", "Sales Log", "Finance Report", "Marketing Report", "Supply Chain Log", "Legal Policy", "Employee"];
  
  const getFilteredDocuments = (type: string) => {
    if (type === "All") return documents;
    return documentsByType[type] || [];
  };

  const getDocumentCount = (type: string) => {
    if (type === "All") return documents.length;
    return documentsByType[type]?.length || 0;
  };

  return (
    <Card className="border-2 border-orange-200 bg-white shadow-lg">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-lg bg-orange-400 flex items-center justify-center">
            <FolderOpen className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">My Documents</h2>
            <p className="text-sm text-gray-600">
              Browse and manage uploaded documents by category
            </p>
          </div>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-orange-600 animate-spin" />
          </div>
        ) : (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="w-full flex-wrap h-auto bg-orange-50 border border-orange-200">
              {documentTypes.map(type => {
                const count = getDocumentCount(type);
                return (
                  <TabsTrigger
                    key={type}
                    value={type}
                    className="data-[state=active]:bg-orange-400 data-[state=active]:text-white text-gray-700"
                  >
                    {type} ({count})
                  </TabsTrigger>
                );
              })}
            </TabsList>

            {documentTypes.map(type => {
              const filteredDocs = getFilteredDocuments(type);
              return (
                <TabsContent key={type} value={type} className="mt-6">
                  {filteredDocs.length === 0 ? (
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
                      {filteredDocs.map(doc => (
                        <DocumentCard key={doc.source_id} document={doc} onDelete={fetchDocuments} />
                      ))}
                    </div>
                  )}
                </TabsContent>
              );
            })}
          </Tabs>
        )}
      </div>
    </Card>
  );
};
