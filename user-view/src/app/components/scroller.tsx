"use client"
import { ReactElement, useEffect, useRef, useState } from "react";
import { SocialPost } from "./social_post";
import { Credentials } from "../credentials";
import { CurationSetting } from "../curation_settings";
import { getCuratedPosts, recommend_post } from "../api_call";

var nextLoadTime = 0;

type PostBatchProps = {
  credentials : Credentials, 
  curationSettings : CurationSetting,
  beforeUTC : number,
  setBeforeUTC : (time : number) => void,
}

function SocialPostVote(
  {embedStr, post_id, credentials, curationSettings} : 
  {embedStr : string, post_id : string, credentials : Credentials, curationSettings : CurationSetting}
) {
  return <div className="flex items-start">
    <SocialPost embedStr={embedStr}/>
    <div className="">
      <div onClick={()=>recommend_post(credentials, curationSettings.curationMode.key, post_id, true)} className="h-12 w-12 m-2">
        <svg viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="100" stroke="gray" stroke-width="3" fill="green"/>
        </svg>
      </div>
      <div onClick={()=>recommend_post(credentials, curationSettings.curationMode.key, post_id, false)} className="h-12 w-12 m-2">
        <svg viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="100" stroke="gray" stroke-width="3" fill="red"/>
        </svg>
      </div>
    </div>
  </div>
}

export function PostBatch(
  {credentials, curationSettings, beforeUTC, setBeforeUTC} :
  PostBatchProps
) {
  const [htmlEmbed, setHtmlEmbed] = useState<[string,string][]|null>(null);

  // Get HTML embeds for posts
  useEffect(() => {
    getCuratedPosts(credentials, curationSettings, beforeUTC).then((response) => {
      // Set html embedding and indicate a new earliest post
      const create_utc = response.posts.map((item)=>item.create_utc);
      let earliestPost = beforeUTC;
      for (const i of create_utc)
          if (i < earliestPost) earliestPost = i;

      if (earliestPost != beforeUTC) setBeforeUTC(earliestPost);
      setHtmlEmbed(response.posts.map((v)=>[v.html,v.post_id]));
      nextLoadTime = Date.now()+3000*response.posts.length;
    });
  }, []);
  return <div>
    {htmlEmbed && 
      <>
        {htmlEmbed.length >= 1  && <SocialPostVote embedStr={htmlEmbed[0][0]} post_id={htmlEmbed[0][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 2  && <SocialPostVote embedStr={htmlEmbed[1][0]} post_id={htmlEmbed[1][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 3  && <SocialPostVote embedStr={htmlEmbed[2][0]} post_id={htmlEmbed[2][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 4  && <SocialPostVote embedStr={htmlEmbed[3][0]} post_id={htmlEmbed[3][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 5  && <SocialPostVote embedStr={htmlEmbed[4][0]} post_id={htmlEmbed[4][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 6  && <SocialPostVote embedStr={htmlEmbed[5][0]} post_id={htmlEmbed[5][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 7  && <SocialPostVote embedStr={htmlEmbed[6][0]} post_id={htmlEmbed[6][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 8  && <SocialPostVote embedStr={htmlEmbed[7][0]} post_id={htmlEmbed[7][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 9  && <SocialPostVote embedStr={htmlEmbed[8][0]} post_id={htmlEmbed[8][1]} credentials={credentials} curationSettings={curationSettings}/>}
        {htmlEmbed.length >= 10 && <SocialPostVote embedStr={htmlEmbed[9][0]} post_id={htmlEmbed[9][1]} credentials={credentials} curationSettings={curationSettings}/>}
      </>
    }
  </div>
}

export function PostScroller({
    credentials, curationSettings
} : {credentials : Credentials, curationSettings : CurationSetting}) {
  // the time that the earliest rendered post was created
  const [beforeUTC, setBeforeUTC] = useState<number>(Date.now());
  // scroll y position of the viewer
  const [scrollPos, setScrollPos] = useState<number>(1000);
  // Maximum scroll
  const scrollLimitRef = useRef<number>(0);
  // Children are defined by their beforeUTC prop
  const [beforeUTCList, setBeforeUTCList] = useState<number[]>([Date.now()]);

  function appendNewPostBatch() {
    // Avoid appending a duplicate batch 
    if (beforeUTCList.indexOf(beforeUTC)!=-1) return;
    beforeUTCList.push(beforeUTC);
    setBeforeUTCList(beforeUTCList);
  }

  // Scroll handling
  function handleScroll() { setScrollPos(window.scrollY); }
  useEffect(() => {
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  function checkAddPostsLoop() {
    // Add more posts if the user is reaching the end of their feed, and sm sites are ready to serve another batch.
    if (Date.now() < nextLoadTime) return;
    scrollLimitRef.current = Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight) - window.innerHeight;
    if (scrollLimitRef.current-scrollPos < 500)
      appendNewPostBatch();
    setTimeout(checkAddPostsLoop, 1000);
  }
  checkAddPostsLoop();

  return <div className="">
    {beforeUTCList.map(
      (child) => 
      <div className="flex justify-center" key={child}><PostBatch credentials={credentials} curationSettings={curationSettings} beforeUTC={child} setBeforeUTC={setBeforeUTC}></PostBatch> </div>
    )}
    <div className="text-5xl text-gray-500 w-full flex justify-center h-40">Loading...</div>
  </div>
}