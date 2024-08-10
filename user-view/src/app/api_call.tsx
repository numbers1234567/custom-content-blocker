/*
 * Formats for API messages.
 * This should be a 1-1 mapping of the endpoints available in the public API
 */

import { CURATE_API_PATH } from "./config";
import { Credentials } from "./credentials";
import { CurationMode, CurationSetting } from "./curation_settings";

export type CuratePostsRequestBody = {
  credentials : {
    token : string
  }
  curation_settings : CurationSetting
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

export async function getCuratedPosts(
  credentials : Credentials, curation_settings : CurationSetting, 
  beforeUTC : number, count_max : number = 10, count_min : number = 5, min_score : number = 0.5) : Promise<CuratePostsResponseBody> {
  let result : CuratePostsResponseBody = {posts : []};
  const requestBody : CuratePostsRequestBody = {
    credentials : credentials,
    curation_settings : curation_settings,
    options : {
      before : beforeUTC, 
      count_min : count_min, 
      count_max : count_max,
      min_score : min_score,
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