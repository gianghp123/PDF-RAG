import { revalidatePath } from "next/cache";

export async function DELETE(request, { params }) {
    const file_id = ( await params ).file_id;
    const response = await fetch(`http://localhost:8000/delete/${file_id}`, {
        method: "DELETE",
    });
    const result = await response.json();
    if (response.ok) {
        revalidatePath('/');
        return Response.json(result);
    }
    return Response.json({ detail: result.detail }, { status: response.status });
}