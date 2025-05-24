chrome.runtime.onInstalled.addListener(() => {
  console.log('Facebook Post Scraper extension installed');
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  async function handleRequest() {
    try {
      if (request.action === 'sendPost') {
        const response = await fetch('http://localhost:8090/api', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: request.url, text: request.postText, imgs: request.imgs })
        });
        const data = await response.json();
        sendResponse({ success: true, data });
      } else if (request.action === 'sendName') {
        const response = await fetch('http://localhost:8090/send_name', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: request.url, name: request.Name, dp: request.dp })
        });
        const data = await response.json();
        sendResponse({ success: true, data });
      } else if (request.action === 'Reset') {
        await fetch('http://localhost:8090/reset');
        sendResponse({ success: true });
      } else {
        sendResponse({ success: false, error: 'Unknown action' });
      }
    } catch (error) {
      console.error('Fetch error:', error);
      sendResponse({ success: false, error: error.message });
    }
  }
  handleRequest();
  return true; // keep the message channel open for async sendResponse
});