export function LoadingState({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="status-card loading-card">
      <div className="loading-orb" />
      <p>{label}</p>
    </div>
  );
}
