import { useAuthStore } from "../../hooks/use-auth-store";
import { useGuilds } from "../../hooks/use-guilds";
import Select from "../ui/Select";

export default function GuildSelector() {
  const { guildId, setGuildId } = useAuthStore();
  const { data } = useGuilds();

  const options =
    data?.guilds.map((g) => ({
      value: String(g.id),
      label: g.name,
    })) ?? [];

  return (
    <Select
      label="Guild"
      options={[{ value: "", label: "Select guild..." }, ...options]}
      value={guildId}
      onChange={(e) => setGuildId(e.target.value)}
    />
  );
}
