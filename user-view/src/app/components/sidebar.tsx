import { useEffect, useRef, useState } from "react";
import { getFilters, getSocialAppFilters, getUserCurationModes } from "../api_call";
import { Credentials } from "../credentials";
import { cloneCurationSetting, CurationMode, CurationSetting } from "../curation_settings";
import { LoginButton } from "./login_button";

type SidebarProps = {
  credentials : Credentials, 
  setCredentials : (a : Credentials) => void
  curationSettings : CurationSetting, 
  setCurationSettings : (a : CurationSetting) => void,
};

export function Sidebar({
  credentials, curationSettings, setCurationSettings, setCredentials
} : SidebarProps) {

  const [availableCurationModes, setAvailableCurationModes] = useState<CurationMode[]>([]);
  const [availableFilters, setAvailableFilters] = useState<CurationMode[]>([]);
  const [availableSocialSites, setAvailableSocialSites] = useState<CurationMode[]>([]);
  const [shown, setShown] = useState<boolean>(true);
  useEffect(()=>{
    getUserCurationModes(credentials).then((curationModes)=>setAvailableCurationModes(curationModes));
    getSocialAppFilters().then((socialSites)=>setAvailableSocialSites(socialSites));
    getFilters().then((filter)=>setAvailableFilters(filter));
  }, [credentials])


  /****************
   *   CONTROLS   *
   ****************/

  function switchCurationMode(newMode : CurationMode) {
    const newSettings = cloneCurationSetting(curationSettings);
    newSettings.curationMode = newMode;
    setCurationSettings(newSettings);
  }
  function whitelistSite(site : CurationMode) {
    const newSettings = cloneCurationSetting(curationSettings);
    newSettings.socialMediaWhitelist.push(site);
    setCurationSettings(newSettings);
  }
  function unWhitelistSite(site : CurationMode) {
    const newSettings = cloneCurationSetting(curationSettings);
    newSettings.socialMediaWhitelist = curationSettings.socialMediaWhitelist.filter((v)=>v.key!=site.key);
    setCurationSettings(newSettings);
  }

  const ref = useRef<HTMLDivElement>(null);

  function hide() {
    if (!ref.current) return;
    ref.current.style.left = "-255px";
  }
  function show() {
    if (!ref.current) return;
    ref.current.style.left = "0px";
  }

  return <div className="h-screen bg-white w-64 p-4 text-black border-r-2 absolute transition-all" style={{left : "0px"}} ref={ref}>
    <div>
      {!credentials.isSet && <LoginButton credentials={credentials} setCredentials={setCredentials}></LoginButton>}
      <p>Curation Modes</p>
      {availableCurationModes.map((val)=>{
        // CURATION MODES
        const isSelected = val.key==curationSettings.curationMode.key;
        return <div className="w-full h-6" key={val.key}>
          {isSelected  && <input type="radio" name="curation-mode" className="inline-block m-2" checked 
            onChange={(e)=>switchCurationMode(val)}/>}
          {!isSelected && <input type="radio" name="curation-mode" className="inline-block m-2" 
            onChange={(e)=>switchCurationMode(val)}/>}

          <p className="inline-block m-2">{val.name}</p>
        </div>
      })}
    </div>
    <button onClick={()=>{shown ? hide():show(); setShown(!shown);}}>
      <div className="w-8 h-8 absolute top-2" style={{left : "260px"}}>
        <svg viewBox="0 0 110 110">
          <circle cx="53" cy="53" r="50" stroke="gray" stroke-width="3" fill="rgba(0,0,0, 0.1)"/>
          <text x="12" y="68" fill="gray" fontSize="60">{shown ? "<<" : ">>"}</text>
        </svg>
      </div> 
    </button>
    {/*<div className="w-full h-6">
      <p className="inline-block m-2">+</p>
      <p className="inline-block m-2">Create New</p>
    </div>
    <p className="mt-8">Whitelisted Sites</p>
    {/*availableSocialSites.map((val)=>{
      // WHITELIST SITES
      const isWhitelisted = curationSettings.socialMediaWhitelist
        .map((v)=>v.key)
        .indexOf(val.key) 
         >= 0;
      return <div className="w-full h-6" key={val.key}>
        {isWhitelisted  && <input type="checkbox" className="inline-block m-2" checked 
          onChange={(e)=>unWhitelistSite(val)}/>}
        {!isWhitelisted && <input type="checkbox" className="inline-block m-2" 
          onChange={(e)=>whitelistSite(val)}/>}
        <p className="inline-block m-2">{val.name}</p>
      </div>
    })
    <p className="mt-8">Blacklisted Topics</p>
    {/*availableFilters.map((val)=>{
      // BLACKLIST TRENDING TOPICS
      const isBlacklisted = curationSettings.trendingFilters
        .map((v)=>v.key)
        .indexOf(val.key)
         >= 0;
      return <div className="w-full h-6 p-2" key={val.key}>
        {isBlacklisted  && <input type="checkbox" className="inline-block m-2" defaultChecked/>}
        {!isBlacklisted && <input type="checkbox" className="inline-block m-2"/>}
        <p className="inline-block m-2">{val.name}</p>
      </div>
    })*/}
  </div>;
}