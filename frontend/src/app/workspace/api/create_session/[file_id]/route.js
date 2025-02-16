import { revalidatePath } from "next/cache";

export async function POST(request, { params }) {
    const file_id = (await params).file_id;
    const response = await fetch(`http://localhost:8000/new_session/${file_id}`, {
        method: "POST",
    })
    const result = await response.json();
    console.log(result);
    if (response.ok) {
        revalidatePath('/workspace/[file_id]', 'page');
        return Response.json(result);
    }
    else {
        return Response.json({ detail: result.detail }, { status: response.status })
    }
}