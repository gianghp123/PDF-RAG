"use client";
import { SquarePen, PanelRightOpen } from "lucide-react";
import { useState } from "react";
import { motion } from "motion/react";
import HistoryCard from "./HistoryCard";
import { usePathname, useRouter } from "next/navigation";

export default function HistorySideBar({file_id, session_data}) {
  const [isOpen, setIsOpen] = useState(true);
  const router = useRouter()
  const pathname = usePathname()
    const handleNewSession = async () => {
        try {
            const response = await fetch(`api/create_session/${file_id}`, {
                method: "POST"
            })
            const data = await response.json();
            if (!response.ok) {
                alert(data.detail);
            }
            else {
                const params = new URLSearchParams();
                params.set('session_id', data.session_id);
                router.push(pathname + '?' + params.toString());
            }
        } catch (error) {
            console.error(error);
        }
        finally {
            setIsOpen(true);
        }
    }
  return (
    <motion.div
      className="relative top-0 left-0 h-screen flex flex-col items-center p-4 text-white gap-[50px]"
      animate={{
        width: isOpen ? "220px" : "50px",
        backgroundColor: isOpen ? "#09090b" : "#18181b",
      }}
    >
      <motion.div
        className="flex items-center gap-2"
        animate={{
          position: isOpen ? "relative" : "absolute",
          width: isOpen ? "220px" : "50px",
          justifyContent: "space-between",
          paddingLeft: '16px',
          paddingRight: '16px'
        }}
      >
        <button onClick={() => setIsOpen(!isOpen)} className="p-1 hover:bg-zinc-600 rounded-lg">
          <PanelRightOpen size={24} />
        </button>
        <button onClick={handleNewSession} className="p-1 hover:bg-zinc-600 rounded-lg">
          <SquarePen size={24}/>
        </button>
      </motion.div>
      {isOpen && (
        <motion.div
          className="w-full h-full flex flex-col overflow-y-auto gap-1"
          animate={{
            opacity: isOpen ? 1 : 0
          }}
          transition={{
            duration: 0.5,
            ease: "easeInOut"
          }}
        >
          {
            session_data.map(session => <HistoryCard key={session.session_id} session_id={session.session_id} title={session.created_at}/>)
          }
        </motion.div>
      )}
    </motion.div>
  );
}
