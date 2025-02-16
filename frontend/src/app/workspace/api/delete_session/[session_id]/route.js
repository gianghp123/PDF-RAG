import { revalidatePath } from "next/cache";

export async function DELETE(request, { params }) {
    const session_id = (await params).session_id;
    const response = await fetch(`http://localhost:8000/delete_session/${session_id}`, {
        method: "DELETE",
    });
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