import { useState, useCallback } from "react";
import { Upload, File, Check, X, Loader2, Sparkles } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { Card } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface DocumentUploadProps {
  onUploadSuccess?: () => void;
}

export const DocumentUpload = ({ onUploadSuccess }: DocumentUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
  const [customExtraction, setCustomExtraction] = useState("");
  const { toast } = useToast();

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const uploadFile = async (file: File) => {
    setUploading(true);
    setProgress(0);
    setUploadStatus("idle");

    try {
      const formData = new FormData();
      formData.append("file", file);
      
      // Add custom extraction if provided
      if (customExtraction.trim()) {
        formData.append("custom_extraction", customExtraction.trim());
      }

      // Simulate progress
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 200);

      const response = await fetch("http://localhost:8000/api/documents/upload", {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);
      setProgress(100);

      const result = await response.json();

      if (response.ok && result.success) {
        setUploadStatus("success");
        toast({
          title: "Upload successful!",
          description: `${file.name} has been processed and data extracted.`,
        });
        onUploadSuccess?.();
        
        // Reset after 3 seconds
        setTimeout(() => {
          setUploading(false);
          setProgress(0);
          setUploadStatus("idle");
          setCustomExtraction(""); // Clear custom extraction field
        }, 3000);
      } else {
        throw new Error(result.error || "Upload failed");
      }
    } catch (error) {
      setUploadStatus("error");
      toast({
        title: "Upload failed",
        description: error instanceof Error ? error.message : "An error occurred during upload",
        variant: "destructive",
      });
      setTimeout(() => {
        setUploading(false);
        setProgress(0);
        setUploadStatus("idle");
      }, 3000);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      uploadFile(files[0]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      uploadFile(files[0]);
    }
  }, []);

  return (
    <Card className="border-2 border-orange-200 bg-gradient-to-br from-orange-50 to-white shadow-lg">
      <div className="p-6">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-lg bg-orange-400 flex items-center justify-center">
            <Upload className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Upload Documents</h2>
            <p className="text-sm text-gray-600">
              Upload business documents for AI extraction and analysis
            </p>
          </div>
        </div>

        {/* Custom Extraction Field */}
        <div className="space-y-2 mb-4">
          <Label htmlFor="custom-extraction" className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Sparkles className="w-4 h-4 text-orange-600" />
            What specific data do you want to extract? (Optional)
          </Label>
          <Input
            id="custom-extraction"
            type="text"
            placeholder="e.g., team morale score, customer satisfaction rating, budget approval status..."
            value={customExtraction}
            onChange={(e) => setCustomExtraction(e.target.value)}
            disabled={uploading}
            className="border-orange-200 focus:border-orange-400 focus:ring-orange-400"
          />
          <p className="text-xs text-gray-500">
            If this data doesn't match a standard column, the AI will save it in the justification field for reference.
          </p>
        </div>

        {/* Drag and Drop Area */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-xl p-12 text-center transition-all
            ${isDragging ? "border-orange-500 bg-orange-100" : "border-orange-300 bg-white/50"}
            ${uploading ? "pointer-events-none" : "cursor-pointer hover:border-orange-400 hover:bg-orange-50"}
          `}
        >
          <input
            type="file"
            id="file-upload"
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt,.md,.png,.jpg,.jpeg,.xlsx,.csv"
            disabled={uploading}
          />

          {!uploading && uploadStatus === "idle" && (
            <label htmlFor="file-upload" className="cursor-pointer">
              <div className="w-16 h-16 mx-auto rounded-2xl bg-orange-100 flex items-center justify-center mb-4">
                <File className="w-8 h-8 text-orange-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900 mb-2">
                Drop files here or click to browse
              </p>
              <p className="text-sm text-gray-600">
                Supports PDF, Word, Excel, Images (Max 10MB)
              </p>
            </label>
          )}

          {uploading && uploadStatus === "idle" && (
            <div className="space-y-4">
              <Loader2 className="w-12 h-12 mx-auto text-orange-600 animate-spin" />
              <p className="text-lg font-semibold text-gray-900">Processing document...</p>
              <p className="text-sm text-gray-600">Extracting data with AI</p>
              <div className="max-w-md mx-auto">
                <Progress value={progress} className="h-2" />
              </div>
            </div>
          )}

          {uploadStatus === "success" && (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center">
                <Check className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900">Upload successful!</p>
              <p className="text-sm text-gray-600">Document processed and data extracted</p>
            </div>
          )}

          {uploadStatus === "error" && (
            <div className="space-y-4">
              <div className="w-16 h-16 mx-auto rounded-full bg-red-100 flex items-center justify-center">
                <X className="w-8 h-8 text-red-600" />
              </div>
              <p className="text-lg font-semibold text-gray-900">Upload failed</p>
              <p className="text-sm text-gray-600">Please try again</p>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
