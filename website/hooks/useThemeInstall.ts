
import React from "react";
import { theme } from '../constants';

export function useThemeInstall() {
  React.useEffect(() => {
    const r = document.documentElement;
    (Object.entries(theme) as [string,string][]).forEach(([k,v]) => r.style.setProperty(`--${k}`, v));
    r.style.setProperty("--ring", "0 0 0 3px rgba(50,156,133,0.25)");
  }, []);
}
