"use client"
import Image from "next/image";
import { PostScroller } from "./components/scroller";
import { SocialPost } from "./components/social_post";
import { Sidebar } from "./components/sidebar";
import { useEffect, useState } from "react";
import { Credentials } from "./credentials";
import { CurationSetting } from "./curation_settings";
import { login } from "./api_call";

function getToken() {
  return "public";
  const cname="token";
  let name = cname + "=";
  let decodedCookie = decodeURIComponent(document.cookie);
  let ca = decodedCookie.split(';');
  for(let i = 0; i <ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) == ' ') {
          c = c.substring(1);
      }
      if (c.indexOf(name) == 0) {
          return c.substring(name.length, c.length);
      }
  }
  return "public";
}

export default function Home() {
  const [credentials, setCredentials] = useState<Credentials>({token : getToken(), isSet : getToken()!="public"});
  const [curationSettings, setCurationSettings] = useState<CurationSetting>({
    curationMode : {key : "all", name : "All"},
    socialMediaWhitelist : 
      [
        {key : "reddit", name : "Reddit"},
        {key : "twitter", name : "Twitter"},
        {key : "instagram", name : "Instagram"},
        {key : "youtube", name : "YouTube"},
        {key : "facebook", name : "Facebook"},
      ],
    trendingFilters : [],
  });
  useEffect(()=>{
    if (credentials.isSet) login(credentials);
  }, [credentials]);

  return (
    <main className="bg-white">
      <div className="fixed left-0 top-0">
        <Sidebar credentials={credentials} setCredentials={setCredentials} curationSettings={curationSettings} setCurationSettings={setCurationSettings}/>
      </div>
      <div className="top-0 w-full items-center">
        <PostScroller credentials={credentials} curationSettings={curationSettings}/>
      </div>
    </main>
  );
}
