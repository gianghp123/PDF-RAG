import { revalidatePath } from "next/cache";

export async function POST(request) {
  const formData = await request.formData();
  const response = await fetch("http://localhost:8000/upload/", {
    method: "POST",
    body: formData,
  });
  
  const result = await response.json();
  if (response.ok) {
    revalidatePath('/');
    return Response.json(result);
  }
  return Response.json({ detail: result.detail }, { status: response.status });
}
