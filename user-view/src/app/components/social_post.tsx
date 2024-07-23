import { memo, useLayoutEffect, useRef } from "react"


export const SocialPost = memo(function SocialPost({embedStr} : {embedStr : string}) {
    // https://macarthur.me/posts/script-tags-in-react/
    const elRef = useRef<HTMLDivElement>(null);

	useLayoutEffect(() => {
        if (!elRef.current) return;
		const range = document.createRange();
		range.selectNode(elRef.current);
		const documentFragment = range.createContextualFragment(embedStr);
        
		elRef.current.innerHTML = '';
		elRef.current.append(documentFragment);
	}, []);

	return (
		<div 
			ref={elRef} 
			dangerouslySetInnerHTML={{ __html: embedStr }}>
		</div>
    )
})