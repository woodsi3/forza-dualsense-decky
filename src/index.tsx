import {
  ButtonItem,
  PanelSection,
  PanelSectionRow,
  SliderField,
  ToggleField,
  staticClasses,
} from "@decky/ui";
import { callable, definePlugin } from "@decky/api";
import { useCallback, useEffect, useRef, useState } from "react";
import { FaGamepad } from "react-icons/fa";

type RuntimeStatus = {
  running: boolean;
  enabled: boolean;
  telemetry: string;
  controller: string;
  controller_name: string;
  controller_transport: string;
  controller_path: string;
  controller_serial: string;
  controller_product_id: string;
  controller_firmware: string;
  controller_battery_percent: number | null;
  controller_battery_status: string;
  brake_effect: string;
  throttle_effect: string;
  active_test: string;
  settings_revision: number;
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
const updateSetting = callable<[key: string, value: boolean | number], Settings>("update_setting");
const restartBackend = callable<[], boolean>("restart_backend");
const listPresets = callable<[], string[]>("list_presets");
const createPreset = callable<[], string>("create_preset");
const loadPreset = callable<[name: string], Settings>("load_preset");
const duplicatePreset = callable<[name: string], string>("duplicate_preset");
const deletePreset = callable<[name: string], boolean>("delete_preset");
const testEffect = callable<[effect: string], boolean>("test_effect");

const emptyStatus: RuntimeStatus = {
  running: false,
  enabled: true,
  telemetry: "waiting",
  controller: "disconnected",
  controller_name: "",
  controller_transport: "",
  controller_path: "",
  controller_serial: "",
  controller_product_id: "",
  controller_firmware: "Unavailable through hidraw",
  controller_battery_percent: null,
  controller_battery_status: "Unavailable",
  brake_effect: "clear",
  throttle_effect: "clear",
  active_test: "",
  settings_revision: 0,
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
        <span style={{ fontWeight: 600 }}><span style={{ marginRight: 6 }}>{ok ? "●" : "○"}</span>{value}</span>
      </div>
    </PanelSectionRow>
  );
}

function Content() {
  const [status, setStatus] = useState<RuntimeStatus>(emptyStatus);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [presets, setPresets] = useState<string[]>([]);
  const [presetIndex, setPresetIndex] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState("");
  const saveTimer = useRef<number | undefined>(undefined);

  const refresh = useCallback(async () => {
    try { setStatus(await getStatus()); } catch (error) { console.error(error); }
  }, []);

  const refreshPresets = useCallback(async () => {
    const names = await listPresets();
    setPresets(names);
    setPresetIndex((current) => names.length ? Math.min(current, names.length - 1) : 0);
  }, []);

  useEffect(() => {
    getSettings().then(setSettings).catch((error) => setLoadError(String(error)));
    void refreshPresets();
    void refresh();
    const timer = window.setInterval(refresh, 750);
    return () => {
      window.clearInterval(timer);
      if (saveTimer.current !== undefined) window.clearTimeout(saveTimer.current);
    };
  }, [refresh, refreshPresets]);

  const save = async (key: keyof Settings, value: boolean | number) => {
    const updated = await updateSetting(key, value);
    setSettings(updated);
  };

  const queueSave = (key: keyof Settings, value: number) => {
    if (saveTimer.current !== undefined) window.clearTimeout(saveTimer.current);
    saveTimer.current = window.setTimeout(() => {
      saveTimer.current = undefined;
      void save(key, value);
    }, 400);
  };

  const selectedPreset = presets[presetIndex] ?? "No presets";

  if (!settings) {
    return <PanelSection title="Forza DualSense"><PanelSectionRow>{loadError || "Loading backend…"}</PanelSectionRow></PanelSection>;
  }

  return (
    <>
      <PanelSection title="Status">
        <StatusRow label="Engine" ok={status.running} value={status.running ? "Running" : "Stopped"} />
        <StatusRow label="Telemetry" ok={status.telemetry === "receiving"} value={status.telemetry === "receiving" ? "Receiving" : "Waiting"} />
        <StatusRow label="DualSense" ok={status.controller === "connected"} value={status.controller === "connected" ? status.controller_transport : "Disconnected"} />
        <PanelSectionRow>
          <div style={{ fontSize: 13, opacity: 0.85 }}>
            L2: {status.brake_effect}<br />R2: {status.throttle_effect}<br />
            {status.speed_kmh.toFixed(0)} km/h · Gear {status.gear} · RPM {status.rpm.toFixed(0)}
          </div>
        </PanelSectionRow>
        {status.backend_error && <PanelSectionRow><div style={{ fontSize: 12 }}>Engine error: {status.backend_error}</div></PanelSectionRow>}
      </PanelSection>

      <PanelSection title="Live controls">
        <PanelSectionRow><ToggleField label="Enable haptics" checked={settings.enabled} onChange={(value) => void save("enabled", value)} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Pedal resistance" value={settings.pedal_force_intensity} min={0} max={2} step={0.05} showValue onChange={(value) => { setSettings({ ...settings, pedal_force_intensity: value }); queueSave("pedal_force_intensity", value); }} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="ABS vibration" value={settings.abs_intensity} min={0} max={2} step={0.05} showValue onChange={(value) => { setSettings({ ...settings, abs_intensity: value }); queueSave("abs_intensity", value); }} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Gear kick" value={settings.gear_kick_intensity} min={0} max={2} step={0.05} showValue onChange={(value) => { setSettings({ ...settings, gear_kick_intensity: value }); queueSave("gear_kick_intensity", value); }} /></PanelSectionRow>
        <PanelSectionRow><SliderField label="Rev limiter" value={settings.rev_limiter_intensity} min={0} max={2} step={0.05} showValue onChange={(value) => { setSettings({ ...settings, rev_limiter_intensity: value }); queueSave("rev_limiter_intensity", value); }} /></PanelSectionRow>
      </PanelSection>

      <PanelSection title="Presets">
        <PanelSectionRow><ButtonItem layout="below" onClick={() => presets.length && setPresetIndex((presetIndex + 1) % presets.length)}>Selected: {selectedPreset}</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length || busy} onClick={async () => { setBusy(true); try { setSettings(await loadPreset(selectedPreset)); } finally { setBusy(false); } }}>Load selected</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={busy} onClick={async () => { setBusy(true); try { const name = await createPreset(); await refreshPresets(); const names = await listPresets(); setPresetIndex(Math.max(0, names.indexOf(name))); } finally { setBusy(false); } }}>Save current as new preset</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length || busy} onClick={async () => { setBusy(true); try { const name = await duplicatePreset(selectedPreset); await refreshPresets(); const names = await listPresets(); setPresetIndex(Math.max(0, names.indexOf(name))); } finally { setBusy(false); } }}>Duplicate selected</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length || busy} onClick={async () => { setBusy(true); try { await deletePreset(selectedPreset); await refreshPresets(); } finally { setBusy(false); } }}>Delete selected</ButtonItem></PanelSectionRow>
      </PanelSection>

      <PanelSection title="Test haptics">
        <PanelSectionRow><ButtonItem layout="below" onClick={() => void testEffect("pedal")}>Test pedal resistance</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => void testEffect("abs")}>Test ABS pulse</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => void testEffect("gear")}>Test gear kick</ButtonItem></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" onClick={() => void testEffect("rev")}>Test rev limiter</ButtonItem></PanelSectionRow>
      </PanelSection>

      <PanelSection title="Controller diagnostics">
        <PanelSectionRow><div style={{ fontSize: 13 }}>
          Model: {status.controller_name || "Not detected"}<br />
          Transport: {status.controller_transport || "—"}<br />
          Battery: {status.controller_battery_percent === null ? status.controller_battery_status : `${status.controller_battery_percent}% (${status.controller_battery_status})`}<br />
          Product: {status.controller_product_id || "—"}<br />
          Serial: {status.controller_serial || "Unavailable"}<br />
          HID: {status.controller_path || "—"}<br />
          Firmware: {status.controller_firmware}
        </div></PanelSectionRow>
        <PanelSectionRow><ButtonItem layout="below" disabled={busy} onClick={async () => { setBusy(true); try { await restartBackend(); await refresh(); } finally { setBusy(false); } }}>Restart engine</ButtonItem></PanelSectionRow>
      </PanelSection>
    </>
  );
}

export default definePlugin(() => ({
  name: "Forza DualSense Haptics",
  titleView: <div className={staticClasses.Title}>Forza DualSense</div>,
  content: <Content />,
  icon: <FaGamepad />,
  onDismount() { console.log("Forza DualSense frontend unloaded"); },
}));
