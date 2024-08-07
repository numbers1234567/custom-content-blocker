/*
 * Formats for API messages.
 * This should be a 1-1 mapping of the endpoints available in the public API
 */

import { CURATE_API_PATH } from "./config";
import { Credentials } from "./credentials";
import { CurationMode } from "./curation_settings";

export type CuratePostsRequestBody = {
  username : string,
  password : string,
  before : number,
  count_max : number,
  count_min : number,
  min_score : number,
  curation_key : string,
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

export async function getCuratedPosts(request : CuratePostsRequestBody) : Promise<CuratePostsResponseBody> {
  let result : CuratePostsResponseBody = {posts : []};
  await fetch(`${CURATE_API_PATH}/get_curated_posts`, 
    {method: "POST",
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request)
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