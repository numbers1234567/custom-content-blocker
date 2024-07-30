"use client"
import { ReactElement, useEffect, useRef, useState } from "react";
import { SocialPost } from "./social_post";
import { CURATE_API_PATH } from "../config";

export function PostBatch(
    {beforeUTC, setBeforeUTC} :
    {beforeUTC : number, setBeforeUTC : (time : number) => void}
) {
    const [htmlEmbed, setHtmlEmbed] = useState<string[]|null>(null);
    // Get HTML embeds for posts
    useEffect(() => {
        let html = [];
        console.log("Fetched! " + beforeUTC)
        fetch(`${CURATE_API_PATH}/get_curated_posts`, 
            {method: "POST",
             headers: {
                 'Content-Type': 'application/json',
             },
             body: JSON.stringify({username : "angelo", password : "pimienta", before : beforeUTC, curation_key : "half", count_min : 5, count_max : 10})
            })
            .then(response => response.json())
            .then(json => {
                html = json.posts.map((item : {html : string, create_utc : number})=>item.html);
                let create_utc = json.posts.map((item : {html : string, create_utc : number})=>item.create_utc);
                // new earliest post
                let earliest = create_utc[0];
                for (const i of create_utc)  
                    if (i < earliest) earliest = i;

                setBeforeUTC(earliest);
                // Data ready
                setHtmlEmbed(html);
            })
            .catch(error => console.log(error));
    }, [beforeUTC]);
    return <div>
        {htmlEmbed && 
            <>
                {htmlEmbed.length >= 1  && <SocialPost embedStr={htmlEmbed[0]}/>}
                {htmlEmbed.length >= 2  && <SocialPost embedStr={htmlEmbed[1]}/>}
                {htmlEmbed.length >= 3  && <SocialPost embedStr={htmlEmbed[2]}/>}
                {htmlEmbed.length >= 4  && <SocialPost embedStr={htmlEmbed[3]}/>}
                {htmlEmbed.length >= 5  && <SocialPost embedStr={htmlEmbed[4]}/>}
                {htmlEmbed.length >= 6  && <SocialPost embedStr={htmlEmbed[5]}/>}
                {htmlEmbed.length >= 7  && <SocialPost embedStr={htmlEmbed[6]}/>}
                {htmlEmbed.length >= 8  && <SocialPost embedStr={htmlEmbed[7]}/>}
                {htmlEmbed.length >= 9  && <SocialPost embedStr={htmlEmbed[8]}/>}
                {htmlEmbed.length >= 10 && <SocialPost embedStr={htmlEmbed[9]}/>}
            </>
        }
    </div>
}

export function PostScroller() {
    // the time that the earliest rendered post was created
    const [beforeUTC, setBeforeUTC] = useState<number>(Date.now());
    // scroll y position of the viewer
    const [scrollPos, setScrollPos] = useState<number>(1000);
    // Maximum scroll
    const scrollLimitRef = useRef<number>(0);
    // Children are defined by their beforeUTC prop
    const [beforeUTCList, setBeforeUTCList] = useState<number[]>([Date.now()]);

    function appendNewPostBatch() {
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
    useEffect(() => {
        // Add more posts if the user is reaching the end of their feed.
        scrollLimitRef.current = Math.max( document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight) - window.innerHeight;
        if (scrollLimitRef.current-scrollPos < 500)
            appendNewPostBatch();
    }, [scrollPos])

    return <div>
        {beforeUTCList.map((child) => <PostBatch beforeUTC={child} setBeforeUTC={setBeforeUTC} key={child}></PostBatch> )}
    </div>
}