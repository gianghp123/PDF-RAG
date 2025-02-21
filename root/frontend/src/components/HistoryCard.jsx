"use client";
import { LoaderCircle } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";

export default function HistoryCard({ session_id, title }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const isActive = searchParams.get("session_id") === session_id;
  const [isOpen, setIsOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const handleClick = () => {
    const params = new URLSearchParams();
    params.set("session_id", session_id);
    router.push(pathname + "?" + params.toString());
  };
  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const res = await fetch(`api/delete_session/${session_id}`, {
        method: "DELETE",
      });
      const result = await res.json();
      if (res.ok) {
        if (isActive) {
          router.push(pathname);
        } else {
          router.refresh();
        }
      }
    } catch (error) {
      console.error(`Error deleting session:`, error);
      alert("An error occurred while deleting the session.");
    } finally {
      setIsDeleting(false);
      setIsOpen(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        key={1}
        className="w-full p-2 flex items-center rounded-lg hover:bg-zinc-900"
        style={{ backgroundColor: isActive && "#27272a" }}
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ duration: 0.2 }}
      >
        <button className="w-full text-sm text-start" onClick={handleClick}>
          {title.length > 20 ? title.slice(0, 20) + "..." : title}
        </button>
        <button
          className="text-zinc-500 text-end hover:text-red-600"
          onClick={() => setIsOpen(true)}
        >
          &times;
        </button>
      </motion.div>
      {isOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" key={2}>
          <motion.div
            className="bg-zinc-800 p-[30px] rounded-lg flex flex-col gap-4 ring-1 ring-zinc-600"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            <div >Are you sure you want to continue?<br></br>This action will delete the session created at {title}</div>
            <div className="flex items-center self-end gap-4">
              <button className="w-[80px] h-[40px] bg-red-600 text-white rounded-lg hover:bg-red-800" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? <motion.div className="flex items-center justify-center" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: "linear" }}><LoaderCircle /></motion.div> : "Delete"}
              </button>
              <button className="w-[80px] h-[40px] bg-white/80 text-black hover:bg-white/50 rounded-lg" onClick={() => setIsOpen(false)} disabled={isDeleting}>Cancel</button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
