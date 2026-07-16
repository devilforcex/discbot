import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string;
  guildId: string;
  userId: string;
  setToken: (token: string) => void;
  setGuildId: (guildId: string) => void;
  setUserId: (userId: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: "",
      guildId: "",
      userId: "",
      setToken: (token) => {
        localStorage.setItem("discbot_token", token);
        set({ token });
      },
      setGuildId: (guildId) => {
        localStorage.setItem("discbot_guild", guildId);
        set({ guildId });
      },
      setUserId: (userId) => {
        localStorage.setItem("discbot_user", userId);
        set({ userId });
      },
    }),
    {
      name: "discbot-auth",
      partialize: (state) => ({
        token: state.token,
        guildId: state.guildId,
        userId: state.userId,
      }),
    },
  ),
);
