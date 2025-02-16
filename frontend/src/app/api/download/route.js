import { revalidatePath } from "next/cache";

export async function POST(request) {
  const data = await request.json();
  const response = await fetch("http://localhost:8000/download/", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url: data.url }),
  });
  const result = await response.json();

  if (response.ok) {
    revalidatePath("/");
    return Response.json(result);
  }
  return Response.json({ detail: result.detail }, { status: response.status });
}
