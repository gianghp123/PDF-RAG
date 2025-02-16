import { revalidatePath } from "next/cache";

export async function POST(request, { params }) {
    const file_id = (await params).file_id;
    const { signal } = request;
    const data = await request.json();
    console.log(data)
    try {
        const response = await fetch(`http://localhost:8000/question/${file_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question: data.question, session_id: data.session_id }),
            signal: signal
        });
        const result = await response.json();
        revalidatePath('/workspace/[file_id]', 'page');
        if (response.ok) {
            return Response.json(result);
        }
        else {
            return Response.json({ detail: result.detail }, { status: response.status })
        }
    }
    catch (error) {
        console.log(error)
        return Response.json({ detail: 'User cancelled the request.' }, { status: 499 });
    }
}