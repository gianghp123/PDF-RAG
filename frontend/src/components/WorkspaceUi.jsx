"use client";
import { ArrowUp, Plus, Square } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";
import { useState} from "react";
import { motion } from "motion/react";
import QuestionMessage from "./QuestionMessage";
import AnswerMessage from "./AnswerMessage";

export default function WorkspaceUi({ file_id, session_id, QAList = [] }) {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [currentMessages, setCurrentMessages] = useState([]);
  const router = useRouter();
  const pathname = usePathname();
  const [isStarted, setIsStarted] = useState(QAList.length > 0);
  const [controller, setController] = useState(null);

  const handleNewSession = async () => {
    try {
      const response = await fetch(`api/create_session/${file_id}`, {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        alert(data.detail);
      } else {
        const params = new URLSearchParams();
        params.set("session_id", data.session_id);
        session_id = data.session_id;
        router.push(pathname + "?" + params.toString());
      }
    } catch (error) {
      console.error(error);
    }
  };
  const handleSubmit = async () => {
    if (!question){
      setCurrentMessages((currentMessages) => [
        ...currentMessages,
        { question, answer: "What question do you want to ask? Please enter a question."},
      ]);
      return
    }
    if (controller) controller.abort();
    const newController = new AbortController();
    const id = new Date().getTime()
    setController(newController);
    setIsLoading(true);
    setIsStarted(true);
    setCurrentMessages((currentMessages) => [
      ...currentMessages,
      { question, answer: "", id: id},
    ]);
    const body = {
      question: question,
      session_id: session_id,
    };
    try {
      const response = await fetch(`api/question/${file_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
        signal: newController.signal,
      });
      const data = await response.json();
      console.log(data)
      if (!response.ok) {
        if (typeof data.detail === "string") {
          if (response.status == 499 || response.status == 429) {
            setCurrentMessages((currentMessages) =>
              currentMessages.map((item) =>
                item.id === id ? { ...item, answer: data.detail } : item
              )
            );
          }
          else if (response.status == 404) {
            alert(data.detail)
            router.push('/')
          }
          else {
            alert(data.detail);
            router.push(pathname)
          }
        }
        else {
          console.log(data)
        }
      } else {
        console.log(data.answer);
        setQuestion("");
        setCurrentMessages((currentMessages) =>
          currentMessages.map((item) =>
            item.id === id ? { ...item, answer: data.answer } : item
          )
        );
      }
    } catch (error) {
      setCurrentMessages((currentMessages) =>
        currentMessages.map((item) =>
          item.id === id ? { ...item, answer: error } : item
        )
      );
    }
    setIsLoading(false);
  };

  const stopRequest = () => {
    controller.abort('User cancelled the request!');
  };

  return (
    <div
      className="w-full flex flex-col items-center justify-center bg-zinc-900 text-white space-y-0"
      style={{
        justifyContent: QAList.length === 0 && "center",
        paddingTop: "50px",
        paddingBottom: "30px",
      }}
    >
      {!isStarted ? (
        <div className="text-3xl font-bold pb-[30px]">
          Ask me anything about your PDF
        </div>
      ) : (
        <div
          className="w-full flex flex-col items-center gap-8 overflow-y-scroll pb-[50px] pl-[18px]"
          style={{ height: isStarted && "500px" }}
        >
          {QAList.map((item, index) => (
            <div
              key={index}
              className="w-[700px] text-white/90 flex flex-col gap-2"
            >
              <QuestionMessage question={item.question} />
              <AnswerMessage answer={item.answer} />
            </div>
          ))}
          {currentMessages.map((item, index) => (
            <div
              key={index}
              className="w-[700px] text-white/90 flex flex-col gap-2"
            >
              <QuestionMessage question={item.question} />
              <AnswerMessage answer={item.answer} />
            </div>
          ))}
        </div>
      )}
      {session_id ? (
        <motion.div className="w-[700px] flex flex-col bg-zinc-700 rounded-xl p-2" initial={{ scale: 0 }} animate={{ scale: 1 }}>
          <textarea
            value={question}
            className="bg-zinc-700 w-full h-full resize-none overflow-hidden border-0 shadow-none focus:outline-none"
            placeholder="Type your question here"
            onChange={(e) => setQuestion(e.target.value)}
          />
          <button className="p-[6px] rounded-full bg-white self-end text-black hover:bg-white/50">
            {isLoading ? (
              <Square size={20} strokeWidth={3} fill="currentColor" onClick={stopRequest}/>
            ) : (
              <ArrowUp size={20} strokeWidth={3} onClick={handleSubmit} />
            )}
          </button>
        </motion.div>
      ) : (
        <button
          onClick={handleNewSession}
          className="p-[8px] rounded-3xl bg-white text-black hover:bg-white/50 flex items-center justify-center gap-2"
        >
          <div>Create new session </div><Plus size={20} strokeWidth={3} />
        </button>
      )}
    </div>
  );
}
