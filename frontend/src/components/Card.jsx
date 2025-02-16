"use client";
import React, { useState } from "react";
import { MessageSquareWarning } from "lucide-react";
import { useRouter } from "next/navigation";
import { LoaderCircle } from "lucide-react";
import { motion } from "motion/react";

export default function Card({ id, name, created_at }) {
  const [isOpen, setIsOpen] = useState(false);
  const [baseName, extension] = name.split(/\.(?=[^\.]+$)/);
  const [isHovered, setIsHovered] = useState(false);
  const router = useRouter();
  const [isWaitingInitialize, setIsWaitingInitialize] = useState(false);
  const handleDelete = async () => {
    try {
      const res = await fetch(`api/delete/${id}`, {
        method: "DELETE",
      });
      const result = await res.json();
      if (res.ok) {
        setIsOpen(false);
        router.refresh();
      }
      alert(result.detail);
    } catch (error) {
      console.error(`Error deleting file ${name}:`, error);
      alert("An error occurred while deleting the file.");
    }
  };

  const handleInitialize = async () => {
    try {
      setIsWaitingInitialize(true);
      const res = await fetch(`api/initialize/${id}`, {
        method: "POST",
      });
      const result = await res.json();
      if (res.ok) {
        console.log(result.detail);
        router.push(`/workspace/${id}`);
      }
    } catch (error) {
      console.error(`Error initializing file ${name}:`, error);
      alert("An error occurred while initializing the file.");
    } finally {
      setIsWaitingInitialize(false);
    }
  };

  return (
    <div>
      {isWaitingInitialize && (
        <div className="fixed inset-0 bg-black/50 flex flex-col items-center justify-center z-50 gap-2 text-white">
          <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}>
            <LoaderCircle size={40} />
          </motion.div>
          <div className="text-3xl">The file is being initialized</div>
          <div className="text-xl">
            The first initialization may take a few minutes
          </div>
        </div>
      )}
      <div
        className="relative flex flex-col justify-start bg-black text-white h-[180px] w-[220px] border-[0.5px] border-white/25 rounded-lg p-4 shadow-md hover:shadow-white/25"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <button
          className="absolute top-1 right-2 text-white/50 text-2xl z-50 hover:text-red-600"
          onClick={() => setIsOpen(true)}
        >
          &times;
        </button>
        {isHovered && (
          <div className="absolute inset-0 bg-white/50 border-[0.5px] border-white/25 rounded-lg p-4 flex items-center justify-center z-10">
            <button
              className="bg-black text-white px-6 py-2 border-[0.5px] border-white/70 rounded hover:outline-none hover:ring-2 hover:ring-white transition"
              onClick={handleInitialize}
            >
              Start
            </button>
          </div>
        )}
        {isOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="border-[0.5px] border-white/25 bg-black rounded-lg shadow-lg max-w-md relative">
              <button
                onClick={() => setIsOpen(false)}
                className="absolute top-1 right-2 text-gray-500 hover:text-gray-800 transition text-xl"
              >
                &times;
              </button>
              <div className="p-8 flex flex-col justify-center place-items-end gap-4">
                <div className="flex gap-4 items-center justify-center">
                  <MessageSquareWarning className="self-start" size={70} />
                  <div className="text-xl font-medium">
                    Are your sure you want to delete this file?
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    className="bg-black text-white px-4 py-2 border-[0.5px] border-white/50 rounded hover:outline-none hover:ring-2 hover:ring-white/50 transition"
                    onClick={handleDelete}
                  >
                    Delete
                  </button>
                  <button
                    className="bg-white text-black px-4 py-2 border-[0.5px] border-white/50 rounded hover:outline-none hover:ring-2 hover:ring-white/50 transition"
                    onClick={() => setIsOpen(false)}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
        <div className="text-lg">{baseName}</div>
        <div className="text-sm text-white/80">
          Type: {extension.toUpperCase()}
        </div>
        <div className="text-sm text-white/80">Created at: {created_at}</div>
      </div>
    </div>
  );
}
