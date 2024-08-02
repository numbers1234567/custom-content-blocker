export type CurationMode = {
  key : string,
  name : string,
}


export type CurationSetting = {
  curationMode : CurationMode,
  socialMediaWhitelist : CurationMode[],
  trendingFilters : CurationMode[],
}

export function cloneCurationSetting(settings : CurationSetting) : CurationSetting {
  const newSettings = {
    curationMode : settings.curationMode, 
    socialMediaWhitelist : [...settings.socialMediaWhitelist],
    trendingFilters : [...settings.trendingFilters],
  }

  return newSettings;
}