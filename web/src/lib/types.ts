export interface HealthResponse {
  ok: boolean;
  ready: boolean;
}

export interface LavalinkHealthResponse {
  healthy: boolean;
  reason?: string;
  connected?: boolean;
  uri?: string;
  players?: number;
}

export interface StatusResponse {
  bot_name: string;
  bot_id: number | null;
  latency_ms: number | null;
  guild_count: number;
  uptime: string | null;
  uptime_seconds: number | null;
  connected_voice_channels: number;
}

export interface LavalinkStatusResponse {
  connected: boolean;
  uri?: string;
  latency_ms?: number | null;
  players?: number;
  playing_players?: number;
}

export interface Guild {
  id: number;
  name: string;
  member_count: number | null;
  icon_url: string | null;
}

export interface GuildsResponse {
  guilds: Guild[];
}

export interface NowPlayingResponse {
  playing: boolean;
  title?: string;
  author?: string;
  uri?: string;
  length?: number;
  position?: number;
  paused?: boolean;
  volume?: number;
  artwork_url?: string | null;
  autoplay?: boolean;
  loop?: string | null;
  queue_length?: number;
}

export interface QueueTrack {
  title: string | null;
  author: string | null;
  uri: string | null;
  length: number | null;
  requester_id: number | null;
}

export interface QueueResponse {
  guild_id: number;
  queue_length: number;
  tracks: QueueTrack[];
}

export interface GuildSettings {
  guild_id: string;
  volume: number;
  autoplay: boolean;
  announce_songs: boolean;
  default_source: string;
}

export interface SettingsUpdate {
  volume?: number;
  autoplay?: boolean;
  announce_songs?: boolean;
  default_source?: string;
}

export interface TopTrack {
  title: string;
  author: string;
  play_count: number;
}

export interface StatsResponse {
  total_plays: number;
  unique_tracks: number;
  top_tracks: TopTrack[];
}

export interface HistoryTrack {
  title: string;
  author: string;
  uri: string;
  length: number;
  played_at?: string;
}

export interface HistoryResponse {
  guild_id: string;
  limit: number;
  tracks: HistoryTrack[];
}

export interface OverviewResponse {
  status: StatusResponse;
  guild: Guild;
  queue_length: number;
  settings: GuildSettings;
  stats: StatsResponse;
  recent: HistoryTrack[];
}

export interface Favorite {
  title: string;
  author: string;
  uri: string;
  identifier?: string;
  length: number;
}

export interface FavoritesResponse {
  user_id: string;
  page: number;
  total: number;
  favorites: Favorite[];
}

export interface PlaylistTrack {
  position: number;
  title: string;
  author: string;
  uri: string;
  identifier: string;
  length: number;
  artwork_url?: string | null;
  added_by: string;
}

export interface Playlist {
  playlist_id: string;
  name: string;
  description: string;
  track_count: number;
  created_at?: string;
}

export interface PlaylistDetail {
  playlist_id: string;
  user_id: string;
  guild_id: string;
  name: string;
  description: string;
  track_count: number;
  tracks: PlaylistTrack[];
  created_at?: string;
  updated_at?: string;
}

export interface PlaylistsResponse {
  user_id: string;
  playlists: Playlist[];
}

export type ControlAction =
  | "pause"
  | "resume"
  | "play_pause"
  | "skip"
  | "stop"
  | "shuffle"
  | "volume";

export interface ControlResponse {
  success: boolean;
  message: string;
  volume?: number;
}

export interface ApiError {
  detail: string;
}
