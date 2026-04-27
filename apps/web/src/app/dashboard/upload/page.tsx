"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";

export default function UploadPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [contentType, setContentType] = useState("image");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      if (!title) {
        setTitle(selected.name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const handleUpload = async () => {
    if (!file || !title) {
      setError("Please select a file and provide a title");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("title", title);
      formData.append("content_type", contentType);
      formData.append("territories", JSON.stringify(["global"]));

      const res = await api.assets.upload(formData);
      setTaskId(res.data.task_id);

      pollTaskStatus(res.data.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
      setLoading(false);
    }
  };

  const pollTaskStatus = async (taskId: string) => {
    const poll = async () => {
      try {
        const res = await api.tasks.getStatus(taskId);
        setTaskStatus(res.data.status);

        if (res.data.status === "success" || res.data.status === "failure") {
          setLoading(false);
          if (res.data.status === "success") {
            router.push("/dashboard/assets");
          }
        } else {
          setTimeout(poll, 2000);
        }
      } catch {
        setTimeout(poll, 2000);
      }
    };
    poll();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Upload Asset</h1>
        <p className="text-gray-600">Protect your content with GUARDIAN</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Asset Details</CardTitle>
          <CardDescription>Upload images, videos, or audio files</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error && (
            <div className="rounded bg-red-50 p-3 text-sm text-red-600">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label>File</Label>
            <Input
              ref={fileInputRef}
              type="file"
              accept="image/*,video/*,audio/*"
              onChange={handleFileChange}
            />
            {file && (
              <p className="text-sm text-gray-500">
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="title">Title</Label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter asset title"
            />
          </div>

          <div className="space-y-2">
            <Label>Content Type</Label>
            <div className="flex gap-4">
              {["image", "video", "audio"].map((type) => (
                <label key={type} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="content_type"
                    value={type}
                    checked={contentType === type}
                    onChange={(e) => setContentType(e.target.value)}
                  />
                  <span className="capitalize">{type}</span>
                </label>
              ))}
            </div>
          </div>

          {taskId && (
            <div className="rounded bg-blue-50 p-3">
              <p className="text-sm">
                Status: <span className="font-medium">{taskStatus}</span>
              </p>
            </div>
          )}

          <Button onClick={handleUpload} disabled={loading || !file || !title}>
            {loading ? "Uploading..." : "Upload & Protect"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}