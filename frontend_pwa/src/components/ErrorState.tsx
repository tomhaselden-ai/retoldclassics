export function ErrorState({
  title = "Something went off course",
  message,
}: {
  title?: string;
  message: string;
}) {
  return (
    <div className="status-card error-card">
      <h3>{title}</h3>
      <p>{message}</p>
    </div>
  );
}
