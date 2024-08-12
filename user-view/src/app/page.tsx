"use client"
import Image from "next/image";
import { PostScroller } from "./components/scroller";
import { SocialPost } from "./components/social_post";
import { Sidebar } from "./components/sidebar";
import { useState } from "react";
import { Credentials } from "./credentials";
import { CurationSetting } from "./curation_settings";

export default function Home() {
  const [credentials, setCredentials] = useState<Credentials>({token : "public", isSet : false});
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

  // Maybe some auto-login using cookies here

  return (
    <main className="">
      <div className="fixed left-0 top-0">
        <Sidebar credentials={credentials} setCredentials={setCredentials} curationSettings={curationSettings} setCurationSettings={setCurationSettings}/>
      </div>
      <div className="top-0 w-full items-center">
        <PostScroller credentials={credentials} curationSettings={curationSettings}/>
      </div>
    </main>
  );
}
