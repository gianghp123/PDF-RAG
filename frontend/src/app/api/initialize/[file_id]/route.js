export async function POST(request, { params }) {
  const file_id = (await params).file_id;
  const response = await fetch(`http://localhost:8000/initialize/${file_id}`, {
    method: "POST"
  });
  const result = await response.json();
  console.log(result)
  if (response.ok) {
    return Response.json(result);
  }
  return Response.json({ detail: result.detail }, { status: response.status });
}
