# Data organization

main.csv contains the IDs, text, 1 if political and 0 if nonpolitical, and the data split ("train" or "test").

media.csv contains, for each media, the ID of the post that the media came from. It also includes a path to the media. Both csvs hold data about train and test splits jointly.

# Sources 

I will start by taking a list of political/nonpolitical subreddits. The subreddits will be split into training/validation and test sets.

https://www.reddit.com/r/redditlists/comments/josdr/list_of_political_subreddits/

I will provide a zip file of all posts. Due to the nature of online content, I must also download the images rather than just providing links.

One potential challenge is that nonpolitical subreddits may also have political content, so this may introduce noise to the data.

I will curate the test set myself to ensure accuracy, though I'm concerned about data leakage (reposts). Not sure how to resolve this.

Training:
 * https://www.reddit.com/r/Republican/
 * https://www.reddit.com/r/democrats/
 * https://www.reddit.com/r/TheRightCantMeme/
 * https://www.reddit.com/r/TheLeftCantMeme/
 * https://www.reddit.com/r/UkraineWarVideoReport/
 * https://www.reddit.com/r/interestingasfuck/
 * https://www.reddit.com/r/funny/
 * https://www.reddit.com/r/Damnthatsinteresting/

Testing:
 * https://www.reddit.com/r/Israel/
 * https://www.reddit.com/r/pakistan/
 * https://www.reddit.com/r/Palestine/
 * https://www.reddit.com/r/memes/

Posts are collected by starting the server with data_collection.py and then going to the websites with the browser (with the extension active and using data_collection.py as the API)