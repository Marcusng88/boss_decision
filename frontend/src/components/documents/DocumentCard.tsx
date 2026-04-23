import { useState } from "react";
import { FileText, ExternalLink, Trash2, Calendar, File } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { useToast } from "@/hooks/use-toast";
import { format } from "date-fns";

interface Document {
  source_id: number;
  doc_type: string;
  title: string;
  file_path: string;
  published_date: string | null;
  extracted_at: string | null;
  created_at: string;
}

interface DocumentCardProps {
  document: Document;
  onDelete?: () => void;
}

export const DocumentCard = ({ document, onDelete }: DocumentCardProps) => {
  const { toast } = useToast();
  const [imageError, setImageError] = useState(false);

  const handleDelete = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/documents/${document.source_id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        toast({
          title: "Document deleted",
          description: "The document has been successfully deleted.",
        });
        onDelete?.();
      } else {
        throw new Error("Failed to delete document");
      }
    } catch (error) {
      toast({
        title: "Delete failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    }
  };

  const getDocTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      "HR Report": "bg-blue-100 text-blue-700 border-blue-300",
      "Sales Log": "bg-green-100 text-green-700 border-green-300",
      "Finance Report": "bg-purple-100 text-purple-700 border-purple-300",
      "Marketing Report": "bg-pink-100 text-pink-700 border-pink-300",
      "Supply Chain Log": "bg-yellow-100 text-yellow-700 border-yellow-300",
      "Legal Policy": "bg-gray-100 text-gray-700 border-gray-300",
      "Employee": "bg-indigo-100 text-indigo-700 border-indigo-300",
    };
    return colors[type] || "bg-orange-100 text-orange-700 border-orange-300";
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return "N/A";
    try {
      return format(new Date(dateString), "MMM dd, yyyy");
    } catch {
      return "N/A";
    }
  };

  // Generate Cloudinary preview URL for any file type
  const getCloudinaryPreview = (url: string): string | null => {
    if (!url.includes('cloudinary.com')) return null;
    
    // Extract file extension
    const ext = url.split('.').pop()?.toLowerCase();
    
    // For images, return as-is (Cloudinary serves them directly)
    const imageExts = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'];
    if (imageExts.includes(ext || '')) {
      // Add transformation for consistent preview size
      return url.replace('/upload/', '/upload/w_800,h_600,c_fit/');
    }
    
    // For PDFs, generate image preview of first page
    if (ext === 'pdf') {
      return url.replace('/upload/', '/upload/w_800,h_600,c_fit,pg_1,f_jpg/').replace('.pdf', '.jpg');
    }
    
    // For documents (doc, docx, etc.), Cloudinary can generate previews
    const docExts = ['doc', 'docx', 'ppt', 'pptx'];
    if (docExts.includes(ext || '')) {
      return url.replace('/upload/', '/upload/w_800,h_600,c_fit,pg_1,f_jpg/').replace(`.${ext}`, '.jpg');
    }
    
    return null;
  };

  // Check file types for fallback icons
  const getFileType = (path: string): string => {
    const ext = path.split('.').pop()?.toLowerCase() || '';
    
    if (['png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'svg'].includes(ext)) return 'image';
    if (ext === 'pdf') return 'pdf';
    if (['doc', 'docx', 'txt', 'md', 'rtf'].includes(ext)) return 'document';
    if (['xlsx', 'xls', 'csv'].includes(ext)) return 'spreadsheet';
    
    return 'unknown';
  };

  const previewUrl = getCloudinaryPreview(document.file_path);
  const fileType = getFileType(document.file_path);

  return (
    <Card className="border-2 border-orange-100 hover:border-orange-300 hover:shadow-lg transition-all bg-white overflow-hidden">
      {/* Cloudinary Preview (works for images, PDFs, and documents) */}
      {previewUrl && !imageError ? (
        <div 
          className="w-full h-48 bg-gray-100 overflow-hidden cursor-pointer group"
          onClick={() => window.open(document.file_path, "_blank")}
        >
          <img 
            src={previewUrl} 
            alt={document.title}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform"
            onError={() => setImageError(true)}
          />
        </div>
      ) : (
        // Fallback for non-Cloudinary files or unsupported types
        <div 
          className="w-full h-48 bg-gradient-to-br from-gray-50 to-gray-100 overflow-hidden cursor-pointer hover:from-gray-100 hover:to-gray-200 transition-colors flex items-center justify-center"
          onClick={() => window.open(document.file_path, "_blank")}
        >
          <div className="text-center">
            {fileType === 'pdf' && (
              <>
                <FileText className="w-16 h-16 text-red-600 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">PDF Document</p>
              </>
            )}
            {fileType === 'document' && (
              <>
                <File className="w-16 h-16 text-blue-600 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">Document</p>
              </>
            )}
            {fileType === 'spreadsheet' && (
              <>
                <FileText className="w-16 h-16 text-green-600 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">Spreadsheet</p>
              </>
            )}
            {fileType === 'unknown' && (
              <>
                <File className="w-16 h-16 text-gray-600 mx-auto mb-2" />
                <p className="text-sm font-medium text-gray-700">File</p>
              </>
            )}
            <p className="text-xs text-gray-500 mt-1">Click to view</p>
          </div>
        </div>
      )}
      
      <div className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-orange-100 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-orange-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate" title={document.title}>
              {document.title}
            </h3>
            <Badge className={`mt-1 text-xs border ${getDocTypeColor(document.doc_type)}`}>
              {document.doc_type}
            </Badge>
          </div>
        </div>

        {/* Metadata */}
        <div className="space-y-1 text-sm text-gray-600">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4" />
            <span>Uploaded: {formatDate(document.created_at)}</span>
          </div>
          {document.extracted_at && (
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-green-500" />
              <span className="text-xs">Processed & extracted</span>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-orange-700 border-orange-300 hover:bg-orange-50 hover:text-orange-800"
            onClick={() => window.open(document.file_path, "_blank")}
          >
            <ExternalLink className="w-4 h-4 mr-2" />
            View
          </Button>
          
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="outline"
                size="sm"
                className="text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete document?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete "{document.title}" and all related data.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={handleDelete}
                  className="bg-red-600 hover:bg-red-700"
                >
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>
    </Card>
  );
};
