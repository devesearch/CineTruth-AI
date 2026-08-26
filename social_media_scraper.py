import requests
import re
import trafilatura
from urllib.parse import urlparse
import streamlit as st

def fetch_social_media_content(url, platform):
    """
    Fetch content from a social media platform based on the URL.
    
    Args:
        url (str): The URL of the social media post
        platform (str): The name of the platform (Twitter, Instagram, Facebook, Reddit)
        
    Returns:
        str: The text content of the post
    """
    if platform == "Twitter":
        return fetch_twitter_content(url)
    elif platform == "Instagram":
        return fetch_instagram_content(url)
    elif platform == "Facebook":
        return fetch_facebook_content(url)
    elif platform == "Reddit":
        return fetch_reddit_content(url)
    else:
        return None

def fetch_twitter_content(url):
    """
    Extract content from a Twitter post.
    Note: This is a simple approach using web scraping.
    
    Args:
        url (str): The URL of the Twitter post
        
    Returns:
        str: The text content of the tweet
    """
    try:
        # Use trafilatura to extract the main content
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            content = trafilatura.extract(downloaded)
            
            # Since Twitter might have limited access due to authentication,
            # we'll extract relevant text from what we can get
            if content:
                # Try to find the tweet text using a simple pattern
                # This is a basic approach and might need refinement
                tweet_pattern = r'(@\w+):\s*(.*?)(?=\n|\Z)'
                matches = re.findall(tweet_pattern, content)
                
                if matches:
                    return "\n".join([f"{username}: {tweet}" for username, tweet in matches])
                
                # If we couldn't extract using the pattern, return the whole content
                return content
            
        st.warning("Limited Twitter content was extracted. For better results, consider using the Twitter API.")
        return "Could not extract complete content from Twitter. Try pasting the tweet text directly."
    
    except Exception as e:
        st.error(f"Error fetching Twitter content: {str(e)}")
        return None

def fetch_instagram_content(url):
    """
    Extract content from an Instagram post.
    Note: This is a simple approach using web scraping.
    
    Args:
        url (str): The URL of the Instagram post
        
    Returns:
        str: The text content of the post
    """
    try:
        # Use trafilatura to extract the main content
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            content = trafilatura.extract(downloaded)
            
            if content:
                # Try to extract the Instagram caption using a simple pattern
                caption_pattern = r'Caption:?\s*(.*?)(?=\n|\Z)'
                match = re.search(caption_pattern, content, re.DOTALL)
                
                if match:
                    return match.group(1).strip()
                
                # If we couldn't extract using the pattern, return the whole content
                return content
        
        st.warning("Limited Instagram content was extracted. For better results, consider using the Instagram API.")
        return "Could not extract complete content from Instagram. Try pasting the post text directly."
    
    except Exception as e:
        st.error(f"Error fetching Instagram content: {str(e)}")
        return None

def fetch_facebook_content(url):
    """
    Extract content from a Facebook post.
    Note: This is a simple approach using web scraping.
    
    Args:
        url (str): The URL of the Facebook post
        
    Returns:
        str: The text content of the post
    """
    try:
        # Use trafilatura to extract the main content
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded:
            content = trafilatura.extract(downloaded)
            
            if content:
                return content
        
        st.warning("Limited Facebook content was extracted. For better results, consider using the Facebook API.")
        return "Could not extract complete content from Facebook. Try pasting the post text directly."
    
    except Exception as e:
        st.error(f"Error fetching Facebook content: {str(e)}")
        return None

def fetch_reddit_content(url):
    """
    Extract content from a Reddit post.
    Keeps the original working flow first (trafilatura), and only uses
    a safer fallback for Reddit share URLs when that first method fails.

    Args:
        url (str): The URL of the Reddit post

    Returns:
        str: The text content of the post
    """
    try:
        # Parse the URL to extract post ID
        parsed_url = urlparse(url)

        # Check if it's a Reddit URL
        if "reddit.com" not in parsed_url.netloc:
            return "Not a valid Reddit URL"

        # ORIGINAL WORKING LOGIC: always try trafilatura first.
        downloaded = trafilatura.fetch_url(url)

        if downloaded:
            content = trafilatura.extract(downloaded)

            if content:
                return content

        # Only if the original method failed, resolve Reddit /s/... share URLs
        # to their canonical /comments/... URL before requesting JSON.
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                          'AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/131.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        resolved_url = url
        try:
            redirect_response = requests.get(
                url,
                headers=headers,
                timeout=12,
                allow_redirects=True,
            )
            if redirect_response.url:
                resolved_url = redirect_response.url
        except requests.RequestException:
            # Keep the original URL if Reddit resets the redirect request.
            pass

        # Remove query params/fragments before adding .json.
        resolved_url = resolved_url.split('#', 1)[0].split('?', 1)[0]
        resolved_url = resolved_url.rstrip('/')
        json_url = f"{resolved_url}.json"

        try:
            response = requests.get(
                json_url,
                headers={**headers, 'Accept': 'application/json,text/plain,*/*'},
                timeout=12,
                allow_redirects=True,
            )

            if response.status_code == 200:
                # Reddit sometimes returns HTML with status 200. Parse JSON only
                # when the response actually looks like JSON.
                raw = response.text.lstrip()
                content_type = response.headers.get('content-type', '').lower()

                if 'json' in content_type or raw.startswith('[') or raw.startswith('{'):
                    try:
                        data = response.json()
                    except ValueError:
                        data = None

                    if isinstance(data, list) and data:
                        children = data[0].get('data', {}).get('children', [])
                        if children:
                            post_data = children[0].get('data', {})
                            title = post_data.get('title', '') or ''
                            selftext = post_data.get('selftext', '') or ''

                            if title or selftext:
                                return f"{title}\n\n{selftext}".strip()
        except requests.RequestException:
            pass

        # Final lightweight fallback: fetch the resolved public page and let
        # the same trafilatura extractor process its HTML.
        try:
            html_response = requests.get(
                resolved_url,
                headers=headers,
                timeout=12,
                allow_redirects=True,
            )
            if html_response.status_code == 200 and html_response.text:
                content = trafilatura.extract(html_response.text)
                if content:
                    return content
        except requests.RequestException:
            pass

        st.warning("Limited Reddit content was extracted. For better results, consider using the Reddit API.")
        return "Could not extract complete content from Reddit. Try pasting the post text directly."

    except Exception as e:
        st.error(f"Error fetching Reddit content: {str(e)}")
        return None

