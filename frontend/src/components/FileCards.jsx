import UploadButton from "./UploadButton";
import Card from "./Card";

export default function FileCards({ initialFiles }) {
  return (
    <div className="grid grid-cols-4 gap-4">
      {Array.isArray(initialFiles) &&
        initialFiles.map((file) => (
          <Card
            key={file.file_id}
            id={file.file_id}
            name={file.source}
            created_at={file.created_at}
          />
        ))}

      <UploadButton />
    </div>
  );
}
