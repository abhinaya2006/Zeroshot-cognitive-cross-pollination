import dynamic from "next/dynamic";

const GamifiedDashboard = dynamic(
  () => import("@/components/GamifiedDashboard"),
  { ssr: false }
);

export default function Home() {
  return (
    <main className="min-height-screen bg-slate-950">
      <GamifiedDashboard />
    </main>
  );
}
