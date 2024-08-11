/*
 * Formats for API messages.
 * This should be a 1-1 mapping of the endpoints available in the public API
 */

import { CURATE_API_PATH } from "./config";
import { Credentials } from "./credentials";
import { CurationMode, CurationSetting } from "./curation_settings";

// Some conversion for transfer

type HTTPCredentials = {
  token : string,
}

function toHTTPCredentials(credentials : Credentials) : HTTPCredentials {
  return {token : credentials.token};
}

type HTTPCurationMode = {
  key : string,
  name : string,
}

function toHTTPCurationMode(curationMode : CurationMode) : HTTPCurationMode {
  return {key : curationMode.key, name : curationMode.name};
}

type HTTPCurationSetting = {
  curation_mode : HTTPCurationMode,
  social_media_whitelist : CurationMode[],
  trending_filters : CurationMode[],
}

function toHTTPCurationSetting(curationSettings : CurationSetting) : HTTPCurationSetting {
  return {
    curation_mode : toHTTPCurationMode(curationSettings.curationMode),
    social_media_whitelist : curationSettings.socialMediaWhitelist.map((val)=>toHTTPCurationMode(val)),
    trending_filters : curationSettings.trendingFilters.map((val)=>toHTTPCurationMode(val)),
  }
}

type CuratePostsRequestBody = {
  credentials : HTTPCredentials
  curation_settings : HTTPCurationSetting
  options : {
    before : number,
    count_max : number,
    count_min : number,
    min_score : number,
  }
}

type CuratedPost = {
  post_id : string,
  create_utc : number,
  html : string,
  curate_score : number,
}

type CuratePostsResponseBody = {
  posts : CuratedPost[],
}

type LoginRequestBody = {
  credentials : HTTPCredentials,
}

type LoginResponseBody = {
  success : boolean,
}

export async function getCuratedPosts(
  credentials : Credentials, curation_settings : CurationSetting, 
  beforeUTC : number, countMax : number = 10, countMin : number = 5, minScore : number = 0.5) : Promise<CuratePostsResponseBody> {
  let result : CuratePostsResponseBody = {posts : []};
  const requestBody : CuratePostsRequestBody = {
    credentials : toHTTPCredentials(credentials),
    curation_settings : toHTTPCurationSetting(curation_settings),
    options : {
      before : beforeUTC, 
      count_min : countMin, 
      count_max : countMax,
      min_score : minScore,
    }
  }
  await fetch(`${CURATE_API_PATH}/get_curated_posts`, 
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody)
    })
    .then(response => response.json())
    .then(json => { result = {...json}; })
    .catch(error => console.log(error))
  return result;
}

export async function login(credentials : Credentials) : Promise<boolean> {
  const httpCredentials = toHTTPCredentials(credentials);
  const requestBody : LoginRequestBody = {
    credentials : httpCredentials,
  }
  let result = false;
  await fetch(`${CURATE_API_PATH}/login`,
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
    .then(response => response.json())
    .then(json => { result = json.success; })
    .catch(error => console.log(error));
    
  return result;
}

export async function getUserCurationModes(credentials : Credentials) : Promise<CurationMode[]> {
  return [
    {key : "all", name : "All"},
    //{key : "half", name : "Half"},
    {key : "no_politics", name : "No Politics"}
  ]
}
  
export async function getFilters() : Promise<CurationMode[]> {
  return [
    {key : "trump_shooting", name : "Trump Shooting"}
  ]
}

export async function getSocialAppFilters() : Promise<CurationMode[]> {
  return [
    {key : "reddit", name : "Reddit"},
    {key : "twitter", name : "Twitter"},
    {key : "instagram", name : "Instagram"},
    {key : "youtube", name : "YouTube"},
    {key : "facebook", name : "Facebook"},
  ]
}

export async function createNewCurateMode(credentials : Credential) {

}