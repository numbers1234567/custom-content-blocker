import { memo, useEffect, useLayoutEffect, useRef, useState } from "react"

const SocialPostInner = memo(function SocialPostInner({embedStr} : {embedStr : string}) {
  // https://macarthur.me/posts/script-tags-in-react/

  // The following HTML should come from a trusted source.
  const elRef = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    if (!elRef.current) return;
		const range = document.createRange();
		range.selectNode(elRef.current);
		const documentFragment = range.createContextualFragment(embedStr);
        
    // Inject the markup, triggering a re-run! 
    elRef.current.innerHTML = '';
    elRef.current.append(documentFragment);
	});
  return <div 
    ref={elRef} 
    dangerouslySetInnerHTML={{ __html: embedStr }}>
  </div>
})

export const SocialPost = function SocialPost({embedStr} : {embedStr : string}) {
  const elRef = useRef<HTMLDivElement>(null);

  const [scrollPos, setScrollPos] = useState<number>(1000);
  const [visible, setVisible] = useState<boolean>(true);
  const [maxHeight, setMaxHeight] = useState<number>(10);


  function handleScroll() { setScrollPos(window.scrollY); }
  useEffect(() => {
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);
  
  if (elRef.current) {
    if (maxHeight < elRef.current.clientHeight) {
      setMaxHeight(elRef.current.clientHeight);
    }
    var rect = elRef.current.getBoundingClientRect();
    if (visible && (rect.bottom < -500 || rect.top > 1500)) setVisible(false);
    if (!visible && (rect.bottom > -500 && rect.top < 1500)) setVisible(true);
  }
  

	return (
    <div style={{"width" : "100%", "height" : maxHeight + "px", backgroundColor : "red"}}>
      <div ref={elRef}>
        {visible && <SocialPostInner embedStr={embedStr}/>}
      </div>
    </div>
    )
}