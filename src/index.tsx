import {
  PanelSection,
  PanelSectionRow,
  SliderField,
  ToggleField,
  staticClasses,
} from "@decky/ui";
import { callable, definePlugin } from "@decky/api";
import { useCallback, useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";

type RuntimeStatus = {
  running: boolean;
  enabled: boolean;
  telemetry: string;
  controller: string;
  controller_name: string;
  controller_transport: string;
  brake_effect: string;
  throttle_effect: string;
  speed_kmh: number;
  rpm: number;
  rpm_ratio: number;
  gear: number;
  backend_error?: string;
};

type Settings = {
  enabled: boolean;
  pedal_force_intensity: number;
  abs_intensity: number;
  gear_kick_intensity: number;
  rev_limiter_intensity: number;
};

const getStatus = callable<[], RuntimeStatus>("get_status");
const getSettings = callable<[], Settings>("get_settings");
const updateSetting = callable<[key: string, value: boolean | number], Settings>(
  "update_setting",
);
const restartBackend = callable<[], boolean>("restart_backend");

const emptyStatus: RuntimeStatus = {
  running: false,
  enabled: true,
  telemetry: "waiting",
  controller: "disconnected",
  controller_name: "",
  controller_transport: "",
  brake_effect: "clear",
  throttle_effect: "clear",
  speed_kmh: 0,
  rpm: 0,
  rpm_ratio: 0,
  gear: 0,
  backend_error: "",
};

function StatusRow({ label, ok, value }: { label: string; ok: boolean; value: string }) {
  return (
    <PanelSectionRow>
      <div style={{ display: "flex", width: "100%", justifyContent: "space-between" }}>
        <span>{label}</span>
        <span style={{ fontWeight: 600 }}>
          <span style={{ marginRight: 6 }}>{ok ? "●" : "○"}</span>
          {value}
        </span>
      </div>
    </PanelSectionRow>
  );
}

function Content() {
  const [status, setStatus] = useState<RuntimeStatus>(emptyStatus);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setStatus(await getStatus());
    } catch (error) {
      console.error("Failed to read Forza DualSense status", error);
    }
  }, []);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch((error) => {
        console.error(error);
        setLoadError(String(error));
      });
    refresh();
    const timer = window.setInterval(refresh, 750);
    return () => window.clearInterval(timer);
  }, [refresh]);

  const save = async (key: keyof Settings, value: boolean | number) => {
    setBusy(true);
    try {
      const updated = await updateSetting(key, value);
      setSettings(updated);
      await refresh();
    } finally {
      setBusy(false);
    }
  };

  if (!settings) {
    return (
      <PanelSection title="Forza DualSense">
        <PanelSectionRow>
          <div>
            {loadError ? `Backend RPC error: ${loadError}` : "Loading backend…"}
          </div>
        </PanelSectionRow>
      </PanelSection>
    );
  }

  return (
    <>
      <PanelSection title="Status">
        <StatusRow label="Engine" ok={status.running} value={status.running ? "Running" : "Stopped"} />
        <StatusRow
          label="Telemetry"
          ok={status.telemetry === "receiving"}
          value={status.telemetry === "receiving" ? "Receiving" : "Waiting"}
        />
        <StatusRow
          label="DualSense"
          ok={status.controller === "connected"}
          value={
            status.controller === "connected"
              ? `${status.controller_transport || "Connected"}`
              : "Disconnected"
          }
        />
        {status.backend_error && (
          <PanelSectionRow>
            <div style={{ fontSize: 12 }}>
              Engine error: {status.backend_error}
            </div>
          </PanelSectionRow>
        )}
        <PanelSectionRow>
          <div style={{ fontSize: 13, opacity: 0.85 }}>
            L2: {status.brake_effect}<br />
            R2: {status.throttle_effect}<br />
            {status.speed_kmh.toFixed(0)} km/h · Gear {status.gear} · RPM {status.rpm.toFixed(0)}
          </div>
        </PanelSectionRow>
      </PanelSection>

      <PanelSection title="Controls">
        <PanelSectionRow>
          <ToggleField
            label="Enable haptics"
            checked={settings.enabled}
            disabled={busy}
            onChange={(value) => save("enabled", value)}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label="Pedal resistance"
            value={settings.pedal_force_intensity}
            min={0}
            max={2}
            step={0.05}
            showValue
            disabled={busy}
            onChange={(value) =>
              setSettings({ ...settings, pedal_force_intensity: value })
            }
            onChangeEnd={(value) => save("pedal_force_intensity", value)}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label="ABS vibration"
            value={settings.abs_intensity}
            min={0}
            max={2}
            step={0.05}
            showValue
            disabled={busy}
            onChange={(value) => setSettings({ ...settings, abs_intensity: value })}
            onChangeEnd={(value) => save("abs_intensity", value)}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label="Gear kick"
            value={settings.gear_kick_intensity}
            min={0}
            max={2}
            step={0.05}
            showValue
            disabled={busy}
            onChange={(value) =>
              setSettings({ ...settings, gear_kick_intensity: value })
            }
            onChangeEnd={(value) => save("gear_kick_intensity", value)}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <SliderField
            label="Rev limiter"
            value={settings.rev_limiter_intensity}
            min={0}
            max={2}
            step={0.05}
            showValue
            disabled={busy}
            onChange={(value) =>
              setSettings({ ...settings, rev_limiter_intensity: value })
            }
            onChangeEnd={(value) => save("rev_limiter_intensity", value)}
          />
        </PanelSectionRow>

        <PanelSectionRow>
          <button
            disabled={busy}
            onClick={async () => {
              setBusy(true);
              try {
                await restartBackend();
                await refresh();
              } finally {
                setBusy(false);
              }
            }}
            style={{ width: "100%", padding: 10 }}
          >
            Restart engine
          </button>
        </PanelSectionRow>
      </PanelSection>
    </>
  );
}

export default definePlugin(() => ({
  name: "Forza DualSense Haptics",
  titleView: <div className={staticClasses.Title}>Forza DualSense</div>,
  content: <Content />,
  icon: <FaGamepad />,
  onDismount() {
    console.log("Forza DualSense frontend unloaded");
  },
}));
