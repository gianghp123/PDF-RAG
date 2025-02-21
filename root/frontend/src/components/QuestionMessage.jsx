'use client'
import { motion } from "motion/react";

export default function QuestionMessage({ question }) {
    return (
        <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} className="p-3 bg-zinc-700 rounded-full self-end font-thin">{question}</motion.div>
    );
}