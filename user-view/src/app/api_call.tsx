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
    max_score : number,
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

type GetCurationModesRequestBody = {
  credentials : HTTPCredentials
}

type CreateCurationModeRequestBody = {
  credentials : HTTPCredentials,
  mode_name : string
}

type CreateCurationModeResponseBody = {
  curation_mode : HTTPCurationMode
}

type RecommendPostOptions = {
  positive : boolean
}

type RecommendPostRequestBody = {
  credentials : HTTPCredentials,
  curate_key : string,
  post_id : string,
  options : RecommendPostOptions
}

export async function getCuratedPosts(
  credentials : Credentials, curation_settings : CurationSetting, 
  beforeUTC : number, countMax : number = 10, countMin : number = 1, maxScore : number = 0.5) : Promise<CuratePostsResponseBody> {
  let result : CuratePostsResponseBody = {posts : []};
  const requestBody : CuratePostsRequestBody = {
    credentials : toHTTPCredentials(credentials),
    curation_settings : toHTTPCurationSetting(curation_settings),
    options : {
      before : beforeUTC, 
      count_min : countMin, 
      count_max : countMax,
      max_score : maxScore,
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
  const httpCredentials = toHTTPCredentials(credentials);
  const requestBody : GetCurationModesRequestBody = {
    credentials : httpCredentials,
  }
  let result : CurationMode[] = [];
  await fetch(`${CURATE_API_PATH}/get_curation_modes`,
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
    .then(response => response.json())
    .then(json => { 
      result = json.curation_modes;
    })
    .catch(error => console.log(error));
  
  return result;
}
  
export async function getFilters(credentials : Credentials) : Promise<CurationMode[]> {
  const httpCredentials = toHTTPCredentials(credentials);
  const requestBody : GetCurationModesRequestBody = {
    credentials : httpCredentials,
  }
  let result : CurationMode[] = [];
  await fetch(`${CURATE_API_PATH}/get_curation_modes`,
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
    .then(response => response.json())
    .then(json => { 
      result = json.emerging_topics.map(
        (x : {topic_name: string, topic_key: string})=>{return {key: x.topic_key, name: x.topic_name}}
      );
    })
    .catch(error => console.log(error));
  
  return result;
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

export async function createNewCurateMode(credentials : Credentials, mode_name : string) : Promise<CurationMode> {
  const httpCredentials = toHTTPCredentials(credentials);
  const requestBody : CreateCurationModeRequestBody = {
    credentials : httpCredentials,
    mode_name : mode_name
  }
  let result : CurationMode = {key : "Failed", name : "Failed"};
  await fetch(`${CURATE_API_PATH}/create_curation_mode`,
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
    .then(response => response.json())
    .then(json => { 
      result = json.curation_mode;
    })
  
  return result;
}

export async function recommend_post(credentials : Credentials, curate_key : string, post_id : string, positive : boolean) {
  const httpCredentials = toHTTPCredentials(credentials);
  const requestBody : RecommendPostRequestBody = {
    credentials : httpCredentials,
    curate_key : curate_key,
    post_id : post_id,
    options : {positive : positive}
  }
  fetch(`${CURATE_API_PATH}/recommend_post`,
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    })
    .then(response => response.json())
    .then(json => { 
      
    })
}