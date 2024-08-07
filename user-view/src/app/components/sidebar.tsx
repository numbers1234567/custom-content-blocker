import { useEffect, useState } from "react";
import { getFilters, getSocialAppFilters, getUserCurationModes } from "../api_call";
import { Credentials } from "../credentials";
import { cloneCurationSetting, CurationMode, CurationSetting } from "../curation_settings";

export function Sidebar({
  credentials, curationSettings, setCurationSettings
} : {credentials : Credentials, curationSettings : CurationSetting, setCurationSettings : (a : CurationSetting) => void}) {

  const [availableCurationModes, setAvailableCurationModes] = useState<CurationMode[]>([]);
  const [availableFilters, setAvailableFilters] = useState<CurationMode[]>([]);
  const [availableSocialSites, setAvailableSocialSites] = useState<CurationMode[]>([]);
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

  return <div className="h-screen bg-white w-64 p-4">
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
    {/*<div className="w-full h-6">
      <p className="inline-block m-2">+</p>
      <p className="inline-block m-2">Create New</p>
    </div>*/}
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
    })*/}
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