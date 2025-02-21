import FileCards from "../components/FileCards";

export const revalidate = 60

export default async function Home() {
  const res = await fetch("http://localhost:8000/");
  const files = await res.json();

  return (
    <div className="h-screen flex flex-col items-center pt-[100px] gap-10 bg-zinc-900">
      <div className="text-white text-4xl font-bold">CHOOSE YOUR PDF</div>
      <FileCards initialFiles={files} />
    </div>
  );
}
