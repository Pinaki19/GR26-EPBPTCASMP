let name_sent=false;

//The below is a function that detects url change events
(() => {
  const hasNativeEvent = Object.keys(window).includes('onurlchange')
  if (!hasNativeEvent) {
    let oldURL = location.href
    setInterval(() => {
      const newURL = location.href
      if (oldURL === newURL) {
        return
      }
      const urlChangeEvent = new CustomEvent('urlchange', {
        detail: {
          oldURL,
          newURL
        }
      })
      oldURL = newURL
      dispatchEvent(urlChangeEvent)
    }, 25)
    addEventListener('urlchange', event => {
      if (typeof (onurlchange) === 'function') {
        onurlchange(event)
      }
    })
  }
})()

window.onurlchange =event => {
  chrome.runtime.sendMessage({ action: 'Reset'});
  name_sent=false;
  if(!isFacebookProfilePage())
    return;
  waitForH1AndSendName();
  console.log("URL CHANGED");
}


const message_selector_uri = '[data-ad-preview="message"]';
const more_link_selector = 'a[href*="more"]'; // Selector for the "see more" link

const MAX_REQUESTS = 30;
let totalRequest = 0;
async function check_for_image(post) {
  let p1 = post?.parentElement?.parentElement?.parentElement;
  // Proceed to the next lines only if p1 exists
  if (!p1) {
    return Promise.resolve([]);
  }

  let d1 = p1;
  let imagesInDiv = d1.querySelectorAll('img');

  // Create a list containing all img.src
  let imgSrcs = [];
  for (let img of imagesInDiv) {
    imgSrcs.push(img.currentSrc || img.src); // Use currentSrc or fallback to src
  }

  return Promise.resolve(imgSrcs);
}


async function expandPost(post) {
  const moreButton = Array.from(post.querySelectorAll('div[role="button"]'))
    .find(button => button.innerText.includes('See more'));

  if (moreButton) {
    moreButton.click();
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

// function waitForH1AndSendName() {
//   if(!isFacebookProfilePage() ||name_sent)
//     return;
//   const observer = new MutationObserver((mutations, obs) => {
//       const firstH1 = document.querySelector('h1');
//       if (firstH1) {
//           sendName(); // Call your function once the <h1> is found
//           obs.disconnect(); // Stop observing once done
//       }
//   });

//   observer.observe(document.body, { childList: true, subtree: true });
// }

function waitForH1AndSendName() {
  if (!isFacebookProfilePage() || name_sent) return;

  let retries = 0;
  const maxRetries = 5; // Adjust as needed
  const baseDelay = 500; // Initial delay

  const observer = new MutationObserver((mutations, obs) => {
    const firstH1 = document.querySelector('h1');
    if (firstH1) {
      sendName();
      obs.disconnect();
    }
  });

  observer.observe(document.body, { childList: true, subtree: true });

  function retrySendingName() {
    const firstH1 = document.querySelector('h1');
    if (firstH1) {
      sendName();
    } else if (retries < maxRetries) {
      retries++;
      setTimeout(retrySendingName, baseDelay * (2 ** retries)); // Exponential backoff
    } else {
      console.log("Retry limit reached. Attempting fallback...");
      fallbackSendName(); // Fallback approach
    }
  }

  setTimeout(retrySendingName, baseDelay);
}

// Fallback: Extract a name from the URL if h1 isn't found
function fallbackSendName() {
  if (name_sent) return;

  let extractedName = location.pathname.split('/').filter(Boolean).pop();
  if (extractedName) {
    extractedName = extractedName.replace(/\?.*/, ''); // Remove query params if any
    chrome.runtime.sendMessage({ action: 'sendName', Name: extractedName, url: location.href, dp: null });
    name_sent = true;
  } else {
    console.log("Failed to extract a name from the URL.");
  }
}


function getProfilePhotoUrl(name) {
  let svgElement = document.querySelector(`svg[aria-label="${name}"]`);
  
  if (!svgElement) {
      console.log(`No SVG found with aria-label="${name}"`);
      return null;
  }

  // Select the <image> inside the SVG
  let imageElement = svgElement.querySelector('image');
  let imageUrl = imageElement ? imageElement.getAttribute('xlink:href') : null;

  console.log("SVG Element:", svgElement);
  console.log("Image URL:", imageUrl);

  return imageUrl;
}



function isFacebookProfilePage() {
  const url = window.location.href;
  const profileRegex = /^https:\/\/www\.facebook\.com\/[a-zA-Z0-9.]+\/?$/;
  return profileRegex.test(url);
}



async function sendName(){

  const firstH1 = document.querySelector('h1');
  // Check if the h1 element exists
  if (firstH1) {
      // Get the text content of the h1 element
      let h1Text = firstH1.textContent.trim();

      // Define the possible strings to be removed
      const verifiedAccountBengali = "ভেরিফায়েড অ্যাকাউন্ট";
      const verifiedAccountEnglish = "Verified account";

      if (h1Text.endsWith(verifiedAccountBengali)) {
          h1Text = h1Text.slice(0, -verifiedAccountBengali.length).trim();
      } else if (h1Text.endsWith(verifiedAccountEnglish)) {
          h1Text = h1Text.slice(0, -verifiedAccountEnglish.length).trim();
      }
      const name=h1Text;
      const profileUrl=getProfilePhotoUrl(name);
      name_sent=true;
      chrome.runtime.sendMessage({ action: 'sendName', Name: name,url:location.href,dp:profileUrl});
  }
}

async function searchPost() {
  if(!isFacebookProfilePage())
    return;
  let posts = [];
  const allPosts = document.querySelectorAll(message_selector_uri);

  for (let i = 0; i < allPosts.length; i++) {
    const post = allPosts[i];
    if (!post.is_visited) {
      posts.push(post);
    }
  }

  if (totalRequest < MAX_REQUESTS) {
    for (let post of posts) {
      if (!post.is_visited) {
        await expandPost(post);
        const postText = post.innerText;
        let img_links=await check_for_image(post);
        post.is_visited = true;
        if (postText) {
          chrome.runtime.sendMessage({ action: 'sendPost', postText: postText,imgs:img_links,url:location.href});
          totalRequest++;
        }
        if (totalRequest >= MAX_REQUESTS) break;
      }
    }
  }
}

window.addEventListener('scroll', searchPost);
window.addEventListener('load', searchPost);
window.addEventListener('load', waitForH1AndSendName);

