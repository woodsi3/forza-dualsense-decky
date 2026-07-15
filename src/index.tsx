import { ButtonItem, PanelSection, PanelSectionRow, SliderField, TextField, ToggleField, staticClasses } from "@decky/ui";
import { callable, definePlugin } from "@decky/api";
import { useCallback, useEffect, useState } from "react";
import { FaGamepad } from "react-icons/fa";

type RuntimeStatus = {
  running:boolean; enabled:boolean; telemetry:string; controller:string; controller_name:string; controller_transport:string;
  controller_path:string; controller_serial:string; controller_product_id:string; controller_firmware:string;
  controller_battery_percent:number|null; controller_battery_status:string; brake_effect:string; throttle_effect:string;
  active_test:string; settings_revision:number; speed_kmh:number; rpm:number; rpm_ratio:number; gear:number;
  packet_rate_hz:number; packet_age_seconds:number|null; abs_active:boolean; traction_state:string; rear_slip:number;
  surface_state:string; car_ordinal:number; car_class:number; car_performance_index:number; active_profile:string; backend_error?:string;
};
type Curve = "linear"|"progressive"|"aggressive";
type Settings = { enabled:boolean; pedal_enabled:boolean; abs_enabled:boolean; gear_kick_enabled:boolean; rev_limiter_enabled:boolean; pedal_force_intensity:number; abs_intensity:number; gear_kick_intensity:number; rev_limiter_intensity:number; traction_intensity:number; pedal_response_curve:Curve; traction_response_curve:Curve; traction_enabled:boolean; traction_mild_slip:number; traction_heavy_slip:number; automatic_car_profiles:boolean; };
type SettingUpdate={key:keyof Settings;value:boolean|number|string};

const getStatus=callable<[],RuntimeStatus>("get_status");
const getSettings=callable<[],Settings>("get_settings");
const updateSetting=callable<[update:SettingUpdate],Settings>("update_setting");
const restartBackend=callable<[],boolean>("restart_backend");
const listPresets=callable<[],string[]>("list_presets");
const createPreset=callable<[],string>("create_preset");
const loadPreset=callable<[name:string],Settings>("load_preset");
const duplicatePreset=callable<[name:string],string>("duplicate_preset");
const deletePreset=callable<[name:string],boolean>("delete_preset");
const renameProfile=callable<[request:{old_name:string;new_name:string}],string>("rename_profile");
const testEffect=callable<[effect:string],boolean>("test_effect");
const assignCarProfile=callable<[request:{car_ordinal:number;preset:string}],boolean>("assign_current_car_profile");
const removeCarProfile=callable<[car_ordinal:number],boolean>("remove_current_car_profile");

const curves:Curve[]=["linear","progressive","aggressive"];
const nextCurve=(curve:Curve)=>curves[(curves.indexOf(curve)+1)%curves.length];
const emptyStatus:RuntimeStatus={running:false,enabled:true,telemetry:"waiting",controller:"disconnected",controller_name:"",controller_transport:"",controller_path:"",controller_serial:"",controller_product_id:"",controller_firmware:"Unavailable through hidraw",controller_battery_percent:null,controller_battery_status:"Unavailable",brake_effect:"clear",throttle_effect:"clear",active_test:"",settings_revision:0,speed_kmh:0,rpm:0,rpm_ratio:0,gear:0,packet_rate_hz:0,packet_age_seconds:null,abs_active:false,traction_state:"stable",rear_slip:0,surface_state:"unknown",car_ordinal:0,car_class:0,car_performance_index:0,active_profile:"Global",backend_error:""};

function StatusRow({label,value}:{label:string;value:string}){return <PanelSectionRow><div style={{display:"flex",width:"100%",justifyContent:"space-between"}}><span>{label}</span><span style={{fontWeight:600}}>{value}</span></div></PanelSectionRow>}
function Content(){
 const[status,setStatus]=useState(emptyStatus); const[settings,setSettings]=useState<Settings|null>(null); const[presets,setPresets]=useState<string[]>([]); const[presetIndex,setPresetIndex]=useState(0); const[busy,setBusy]=useState(false); const[error,setError]=useState(""); const[advanced,setAdvanced]=useState(""); const[profileName,setProfileName]=useState("");
 const refresh=useCallback(async()=>{try{setStatus(await getStatus())}catch(e){setError(String(e))}},[]);
 const refreshPresets=useCallback(async()=>{const names=await listPresets();setPresets(names);setPresetIndex(i=>names.length?Math.min(i,names.length-1):0)},[]);
 useEffect(()=>{getSettings().then(setSettings).catch(e=>setError(String(e)));void refreshPresets();void refresh();const timer=window.setInterval(refresh,750);return()=>window.clearInterval(timer)},[refresh,refreshPresets]);
 const save=async(key:keyof Settings,value:boolean|number|string)=>{try{const updated=await updateSetting({key,value});setSettings(updated);setError("")}catch(e){setError(`Could not save ${key}: ${String(e)}`);setSettings(await getSettings())}};
 const selectedPreset=presets[presetIndex]??"No presets";
 if(!settings)return <PanelSection title="Forza DualSense"><PanelSectionRow>{error||"Loading backend…"}</PanelSectionRow></PanelSection>;
 const slider=(label:string,key:keyof Settings,value:number)=><PanelSectionRow><SliderField label={label} value={value} min={0} max={2} step={0.05} showValue onChange={(v)=>{setSettings({...settings,[key]:v});void save(key,v)}}/></PanelSectionRow>;
 return <>
  <PanelSection title="Status">
   <StatusRow label="Engine" value={status.running?"Running":"Stopped"}/><StatusRow label="Telemetry" value={status.telemetry==="receiving"?`${status.packet_rate_hz.toFixed(0)} Hz · ${Math.round((status.packet_age_seconds??0)*1000)} ms`:"Waiting"}/><StatusRow label="DualSense" value={status.controller==="connected"?status.controller_transport:"Disconnected"}/>
   <PanelSectionRow><div style={{fontSize:13,opacity:.9}}>RPM {status.rpm.toFixed(0)} · Gear {status.gear} · {status.speed_kmh.toFixed(0)} km/h<br/>ABS: {status.abs_active?"Active":"Inactive"} · Traction: {status.traction_state}<br/>Surface: {status.surface_state} · Rear slip: {status.rear_slip.toFixed(2)}<br/>Car ID {status.car_ordinal||"—"} · Class {status.car_class} · PI {status.car_performance_index}<br/>Profile: {status.active_profile||"Global"}</div></PanelSectionRow>
   {error&&<PanelSectionRow><div style={{fontSize:12}}>Error: {error}</div></PanelSectionRow>}
  </PanelSection>
  <PanelSection title="Live controls">
   <PanelSectionRow><ToggleField label="Enable haptics" checked={settings.enabled} onChange={v=>void save("enabled",v)}/></PanelSectionRow>

   <PanelSectionRow><ToggleField label="Pedal resistance" checked={settings.pedal_enabled} onChange={v=>void save("pedal_enabled",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>setAdvanced(advanced==="pedal"?"":"pedal")}>Pedal advanced</ButtonItem></PanelSectionRow>
   {advanced==="pedal"&&<>
    {slider("Pedal response","pedal_force_intensity",settings.pedal_force_intensity)}
    <PanelSectionRow><ButtonItem layout="below" onClick={()=>void save("pedal_response_curve",nextCurve(settings.pedal_response_curve))}>Response curve: {settings.pedal_response_curve}</ButtonItem></PanelSectionRow>
   </>}

   <PanelSectionRow><ToggleField label="ABS vibration" checked={settings.abs_enabled} onChange={v=>void save("abs_enabled",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>setAdvanced(advanced==="abs"?"":"abs")}>ABS advanced</ButtonItem></PanelSectionRow>
   {advanced==="abs"&&<>
    {slider("ABS vibration","abs_intensity",settings.abs_intensity)}
   </>}

   <PanelSectionRow><ToggleField label="Gear kick" checked={settings.gear_kick_enabled} onChange={v=>void save("gear_kick_enabled",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>setAdvanced(advanced==="gear"?"":"gear")}>Gear kick advanced</ButtonItem></PanelSectionRow>
   {advanced==="gear"&&<>
    {slider("Gear kick","gear_kick_intensity",settings.gear_kick_intensity)}
   </>}

   <PanelSectionRow><ToggleField label="Rev limiter" checked={settings.rev_limiter_enabled} onChange={v=>void save("rev_limiter_enabled",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>setAdvanced(advanced==="rev"?"":"rev")}>Rev limiter advanced</ButtonItem></PanelSectionRow>
   {advanced==="rev"&&<>
    {slider("Rev limiter vibration","rev_limiter_intensity",settings.rev_limiter_intensity)}
   </>}

   <PanelSectionRow><ToggleField label="Dynamic traction feedback" checked={settings.traction_enabled} onChange={v=>void save("traction_enabled",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>setAdvanced(advanced==="traction"?"":"traction")}>Traction feedback advanced</ButtonItem></PanelSectionRow>
   {advanced==="traction"&&<>
    {slider("Traction feedback","traction_intensity",settings.traction_intensity)}
    <PanelSectionRow><ButtonItem layout="below" onClick={()=>void save("traction_response_curve",nextCurve(settings.traction_response_curve))}>Response curve: {settings.traction_response_curve}</ButtonItem></PanelSectionRow>
   </>}
  </PanelSection>
  <PanelSection title="Profiles and cars">
   <PanelSectionRow><ButtonItem layout="below" onClick={()=>{if(presets.length){const next=(presetIndex+1)%presets.length;setPresetIndex(next);setProfileName(presets[next]??"")}}}>Selected profile: {selectedPreset}</ButtonItem></PanelSectionRow>
   <PanelSectionRow><TextField label="Profile name" value={profileName} onChange={e=>setProfileName(e.target.value)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length||!profileName.trim()||busy} onClick={async()=>{setBusy(true);try{const renamed=await renameProfile({old_name:selectedPreset,new_name:profileName.trim()});await refreshPresets();const names=await listPresets();setPresetIndex(Math.max(0,names.indexOf(renamed)));setProfileName(renamed);setError("")}catch(e){setError(`Could not rename profile: ${String(e)}`)}finally{setBusy(false)}}}>Rename selected profile</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length||busy} onClick={async()=>{setBusy(true);try{setSettings(await loadPreset(selectedPreset))}finally{setBusy(false)}}}>Load selected profile</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={busy} onClick={async()=>{setBusy(true);try{const name=await createPreset();await refreshPresets();const names=await listPresets();setPresetIndex(Math.max(0,names.indexOf(name)))}finally{setBusy(false)}}}>Save current as new profile</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length||busy} onClick={async()=>{setBusy(true);try{const name=await duplicatePreset(selectedPreset);await refreshPresets();const names=await listPresets();setPresetIndex(Math.max(0,names.indexOf(name)))}finally{setBusy(false)}}}>Duplicate selected profile</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!presets.length||busy} onClick={async()=>{setBusy(true);try{await deletePreset(selectedPreset);await refreshPresets()}finally{setBusy(false)}}}>Delete selected profile</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ToggleField label="Automatic per-car profiles" checked={settings.automatic_car_profiles} onChange={v=>void save("automatic_car_profiles",v)}/></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!status.car_ordinal||!presets.length} onClick={()=>void assignCarProfile({car_ordinal:status.car_ordinal,preset:selectedPreset})}>Assign profile to current car</ButtonItem></PanelSectionRow>
   <PanelSectionRow><ButtonItem layout="below" disabled={!status.car_ordinal} onClick={()=>void removeCarProfile(status.car_ordinal)}>Remove current-car assignment</ButtonItem></PanelSectionRow>
  </PanelSection>
  <PanelSection title="Test haptics"><PanelSectionRow><ButtonItem layout="below" onClick={()=>void testEffect("pedal")}>Test pedal resistance</ButtonItem></PanelSectionRow><PanelSectionRow><ButtonItem layout="below" onClick={()=>void testEffect("abs")}>Test ABS pulse</ButtonItem></PanelSectionRow><PanelSectionRow><ButtonItem layout="below" onClick={()=>void testEffect("gear")}>Test gear kick</ButtonItem></PanelSectionRow><PanelSectionRow><ButtonItem layout="below" onClick={()=>void testEffect("rev")}>Test rev limiter</ButtonItem></PanelSectionRow></PanelSection>
  <PanelSection title="Controller diagnostics"><PanelSectionRow><div style={{fontSize:13}}>Model: {status.controller_name||"Not detected"}<br/>Transport: {status.controller_transport||"—"}<br/>Battery: {status.controller_battery_percent===null?status.controller_battery_status:`${status.controller_battery_percent}% (${status.controller_battery_status})`}<br/>Product: {status.controller_product_id||"—"}<br/>Serial: {status.controller_serial||"Unavailable"}<br/>HID: {status.controller_path||"—"}</div></PanelSectionRow><PanelSectionRow><ButtonItem layout="below" disabled={busy} onClick={async()=>{setBusy(true);try{await restartBackend();await refresh()}finally{setBusy(false)}}}>Restart engine</ButtonItem></PanelSectionRow></PanelSection>
 </>
}
export default definePlugin(()=>({name:"Forza DualSense Haptics",titleView:<div className={staticClasses.Title}>Forza DualSense</div>,content:<Content/>,icon:<FaGamepad/>,onDismount(){console.log("Forza DualSense frontend unloaded")}}));
