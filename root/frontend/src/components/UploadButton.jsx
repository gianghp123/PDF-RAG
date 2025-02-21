"use client";
import { Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useState, useRef } from "react";


export default function UploadButton() {
  const inputRef = useRef(null); 
  const [selectedFile, setSelectedFile] = useState(null);
  const [isOpen, setIsOpen] = useState(false);
  const [method, setMethod] = useState("upload");
  const [downloadLink, setDownloadLink] = useState("");
  const router = useRouter();
  const [isDownloading, setIsDownloading] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelectedFile(file);
      handleUpload(file);
    }
  };

  const handleDownload = async () => {
    if (!downloadLink) {
      alert("Please enter a download link.");
      return;
    }
    setIsDownloading(true);
    try {
      const response = await fetch("api/download", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: downloadLink }),
      });
      const data = await response.json();
      if (response.ok) {
        setIsOpen(false);
        setDownloadLink("");
        router.refresh()
      }
      alert(data.detail);
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred while downloading the file.");
    }
    finally {
      setIsDownloading(false);
    }
  };


  const handleUpload = async (file) => {
    if (file.type !== "application/pdf") {
      alert("Please select a PDF file.");
      return;
    }
  
    const formData = new FormData();
    formData.append("file", file);
  
    try {
      const response = await fetch("api/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setIsOpen(false);
        router.refresh()
      }
      alert(data.detail);
    } catch (error) {
      console.error(error);
      alert("An error occurred while uploading the file.");
    }
  };

  return (
    <div>
      <input
        type="file"
        ref={inputRef}
        onChange={handleFileChange}
        className="hidden"
      />
      <div
        className="flex flex-col items-center justify-center bg-black text-white h-[180px] w-[220px] border-[0.5px] border-white/25 rounded-lg p-4 shadow-md hover:shadow-white/25 cursor-pointer"
        onClick={() => setIsOpen(true)}
      >
        <Plus size={70} strokeWidth={2} />
      </div>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="border-[0.5px] border-white/25 bg-black rounded-lg shadow-lg w-[90%] max-w-md relative">
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-0 right-2 text-gray-500 hover:text-gray-800 transition"
            >
              &times;
            </button>
            <div className="flex w-full justify-evenly">
              <button
                className="w-full border-r-[0.05px] border-r-white/25 py-2 text-center"
                style={{
                  borderBottomWidth: method === "upload" ? "0.5px" : "0",
                  borderBottomColor:
                    method === "upload" ? "white" : "transparent",
                }}
                onClick={() => setMethod("upload")}
              >
                Upload Local File
              </button>
              <button
                className="w-full border-l-[0.05px] border-white/25 py-2 text-center"
                style={{
                  borderBottomWidth: method === "download" ? "0.5px" : "0",
                  borderBottomColor:
                    method === "download" ? "white" : "transparent",
                }}
                onClick={() => setMethod("download")}
              >
                Download File
              </button>
            </div>
            <div className="h-[300px] bg-zinc-900 flex items-center justify-center">
              {method === "upload" ? (
                <button className="bg-black text-white px-4 py-2 rounded hover:outline-none hover:ring-2 hover:ring-white/50 transition" onClick={() => inputRef.current.click()}>
                  Choose your file
                </button>
              ) : (
                <div className="flex flex-col gap-4">
                  <input
                    type="text"
                    value={downloadLink}
                    onChange={(e) => setDownloadLink(e.target.value)}
                    placeholder="Enter the file URL"
                    className="bg-black text-white w-full px-4 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-white/25"
                  />
                  <button
                    onClick={handleDownload}
                    className="bg-black text-white px-4 py-2 rounded hover:outline-none hover:ring-2 hover:ring-white/50 transition"
                    disabled={!downloadLink}
                  >
                    {isDownloading ? "Downloading..." : "Download"}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
