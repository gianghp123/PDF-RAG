import HistorySideBar from "../../../components/HistorySideBar";
import WorkspaceUI from "../../../components/WorkspaceUi";

export default async function WorkspacePage({ params, searchParams }) {
    const file_id = (await params).file_id
    const response = await fetch(`http://localhost:8000/get_all_sessions/${file_id}`).then(res => res.json());
    const session_data = response.session_data
    if (session_data.length > 0){
        session_data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
    const session_id = (await searchParams).session_id;
    const response2 = await fetch(`http://localhost:8000/get_all_question_answer/${session_id}`).then(res => res.json());
    const QAList = response2.data
    if (QAList.length > 0){
        QAList.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    }
    return (
        <div className="h-screen flex gap-10 bg-zinc-900">
            <HistorySideBar file_id={file_id} session_data={session_data}/>
            <WorkspaceUI key={session_id} file_id={file_id} session_id={session_id} QAList={QAList}/>
        </div>
    );
}