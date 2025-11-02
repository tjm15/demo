import { useEffect, useState } from 'react';

export type LocalAuthority = {
  code: string; // e.g., E09000033
  name: string; // e.g., Westminster City Council
};

const STORAGE_KEY = 'tpa_settings_v1';

type AppSettings = {
  localAuthority?: LocalAuthority;
};

function readSettings(): AppSettings {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeSettings(s: AppSettings) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {}
}

export function useAppSettings() {
  const [settings, setSettings] = useState<AppSettings>(() => readSettings());

  useEffect(() => {
    writeSettings(settings);
  }, [settings]);

  const setLocalAuthority = (la?: LocalAuthority) => {
    setSettings((prev) => ({ ...prev, localAuthority: la }));
  };

  return {
    settings,
    setLocalAuthority,
  };
}
