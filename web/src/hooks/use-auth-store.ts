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
        localStorage.setItem("DrusaBoT_token", token);
        set({ token });
      },
      setGuildId: (guildId) => {
        localStorage.setItem("DrusaBoT_guild", guildId);
        set({ guildId });
      },
      setUserId: (userId) => {
        localStorage.setItem("DrusaBoT_user", userId);
        set({ userId });
      },
    }),
    {
      name: "DrusaBoT-auth",
      partialize: (state) => ({
        token: state.token,
        guildId: state.guildId,
        userId: state.userId,
      }),
    },
  ),
);
