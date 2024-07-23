"use client"
import Image from "next/image";
import { PostScroller } from "./components/scroller";
import { SocialPost } from "./components/social_post";

function createTestMarkup() {
  return {__html: `
    <blockquote class="reddit-embed-bq" style="height:500px" ><a href="https://www.reddit.com/r/MadeMeSmile/comments/1e7ybrv/the_explosion_of_excitement_could_not_be_contained/">The explosion of excitement could not be contained </a><br> by<a href="https://www.reddit.com/user/Sufficient-Bug-9112/">u/Sufficient-Bug-9112</a> in<a href="https://www.reddit.com/r/MadeMeSmile/">MadeMeSmile</a></blockquote><script async src="https://embed.reddit.com/widgets.js" charset="UTF-8"></script>
    `}
}

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <PostScroller/>
    </main>
  );
}
