"""Research system for Pal - learn from URLs, searches, and text."""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from anthropic import Anthropic
from dotenv import load_dotenv

from memory import store_memory
from topics import load_topics, save_topics, create_topic, add_memory_to_topic, add_unresolved_question, discuss_topic

load_dotenv()

client = Anthropic()
MODEL = "claude-sonnet-4-20250514"

# User agent for web requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Request timeout
REQUEST_TIMEOUT = 15


def extract_text_from_html(html: str, url: str = "") -> str:
    """
    Extract main text content from HTML, removing navigation, ads, etc.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove unwanted elements
    for element in soup.find_all([
        "script", "style", "nav", "header", "footer", "aside",
        "form", "iframe", "noscript", "svg", "button"
    ]):
        element.decompose()

    # Remove elements with common ad/nav classes
    ad_patterns = ["ad", "advertisement", "sidebar", "nav", "menu", "footer", "header", "comment"]
    for pattern in ad_patterns:
        for element in soup.find_all(class_=re.compile(pattern, re.I)):
            element.decompose()
        for element in soup.find_all(id=re.compile(pattern, re.I)):
            element.decompose()

    # Try to find main content
    main_content = None

    # Look for article or main tags first
    for tag in ["article", "main", "[role='main']"]:
        main_content = soup.select_one(tag)
        if main_content:
            break

    # Fall back to common content div classes
    if not main_content:
        content_patterns = ["content", "post", "entry", "article", "body"]
        for pattern in content_patterns:
            main_content = soup.find(class_=re.compile(f"^{pattern}|{pattern}$", re.I))
            if main_content:
                break

    # Use body if nothing else found
    if not main_content:
        main_content = soup.body or soup

    # Extract text
    text = main_content.get_text(separator="\n", strip=True)

    # Clean up whitespace
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    text = "\n".join(lines)

    # Limit text length (Claude context)
    max_chars = 15000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Content truncated...]"

    return text


def fetch_url(url: str) -> tuple[str, str | None]:
    """
    Fetch content from a URL.

    Returns:
        Tuple of (content text, error message or None)
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not parsed.scheme:
            url = "https://" + url
            parsed = urlparse(url)

        if parsed.scheme not in ["http", "https"]:
            return "", "I can only read http/https URLs."

        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "").lower()

        if "text/html" in content_type:
            text = extract_text_from_html(response.text, url)
        elif "text/plain" in content_type:
            text = response.text[:15000]
        elif "application/json" in content_type:
            text = response.text[:15000]
        else:
            return "", f"I can't read this type of content ({content_type})."

        if not text or len(text) < 50:
            return "", "I couldn't extract any useful content from that page."

        return text, None

    except requests.exceptions.Timeout:
        return "", "The page took too long to load."
    except requests.exceptions.ConnectionError:
        return "", "I couldn't connect to that URL."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return "", "That page doesn't exist (404)."
        elif e.response.status_code == 403:
            return "", "I'm not allowed to access that page (403)."
        else:
            return "", f"The page returned an error ({e.response.status_code})."
    except Exception as e:
        return "", f"Something went wrong fetching that URL."


def search_web(query: str, num_results: int = 3) -> tuple[list[dict], str | None]:
    """
    Search the web using DuckDuckGo.

    Returns:
        Tuple of (list of results, error message or None)
        Each result: {"title": str, "url": str, "snippet": str}
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results))

        if not results:
            return [], "I couldn't find anything about that."

        formatted = []
        for r in results:
            formatted.append({
                "title": r.get("title", ""),
                "url": r.get("href", r.get("link", "")),
                "snippet": r.get("body", r.get("snippet", "")),
            })

        return formatted, None

    except ImportError:
        return [], "Web search is not available (missing ddgs package)."
    except Exception as e:
        return [], f"Search failed: {str(e)}"


def process_with_claude(
    content: str,
    source: str,
    content_type: str = "article",
) -> dict:
    """
    Process content with Claude to extract facts and generate summary.

    Args:
        content: The text content to process
        source: Source of the content (URL or "user provided")
        content_type: Type of content ("article", "search_results", "text")

    Returns:
        {
            "summary": str,
            "facts": list[str],
            "topic": str,
            "questions": list[str],
        }
    """
    if content_type == "search_results":
        prompt = f"""I searched the web and found these results. Help me understand them.

Search results:
{content}

Respond in this exact JSON format:
{{
    "summary": "2-3 sentence summary of what I learned",
    "facts": ["fact 1", "fact 2", "fact 3"],
    "topic": "main topic name (2-5 words)",
    "questions": ["question I still have about this"]
}}

Keep facts simple and memorable. Questions should be things I don't fully understand yet."""

    elif content_type == "article":
        prompt = f"""I'm reading this content from {source}. Help me understand and remember it.

Content:
{content}

Respond in this exact JSON format:
{{
    "summary": "2-3 sentence summary of what this is about",
    "facts": ["key fact 1", "key fact 2", "key fact 3", "key fact 4", "key fact 5"],
    "topic": "main topic name (2-5 words)",
    "questions": ["thing I'm confused about", "thing I want to know more about"]
}}

Extract the most important facts I should remember. Questions are things that weren't fully explained or that I'm curious about."""

    else:  # direct text
        prompt = f"""Someone shared this information with me. Help me understand and remember it.

Text:
{content}

Respond in this exact JSON format:
{{
    "summary": "2-3 sentence summary of what this is about",
    "facts": ["key fact 1", "key fact 2", "key fact 3"],
    "topic": "main topic name (2-5 words)",
    "questions": ["question I have about this"]
}}

Extract the key facts I should remember. Questions are things I'm curious about or want to understand better."""

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()

        # Extract JSON from response
        import json

        # Try to find JSON in the response
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            data = json.loads(json_match.group())
            return {
                "summary": data.get("summary", "I read it but I'm not sure what to make of it."),
                "facts": data.get("facts", [])[:10],  # Limit facts
                "topic": data.get("topic", "general"),
                "questions": data.get("questions", [])[:3],  # Limit questions
            }

    except Exception as e:
        print(f"[DEBUG] Claude processing error: {e}")

    # Fallback
    return {
        "summary": "I read it but had trouble understanding it all.",
        "facts": [],
        "topic": "general",
        "questions": [],
    }


def store_research_results(
    result: dict,
    source: str,
    topics: dict,
) -> tuple[dict, list[str]]:
    """
    Store research results as memories and update topic card.

    Args:
        result: Output from process_with_claude
        source: Source of the content
        topics: Current topics dict

    Returns:
        Tuple of (updated topics, list of memory IDs)
    """
    topic_name = result.get("topic", "general")
    facts = result.get("facts", [])
    questions = result.get("questions", [])

    memory_ids = []

    # Store each fact as a memory
    for fact in facts:
        if fact and len(fact) > 10:  # Skip very short facts
            memory_id = store_memory(
                content=fact,
                memory_type="learned",
                source=source,
            )
            memory_ids.append(memory_id)

            # Link to topic
            topics = add_memory_to_topic(topics, topic_name, memory_id)

    # Update topic discussion count
    topics = discuss_topic(topics, topic_name)

    # Add unresolved questions
    for question in questions:
        if question and len(question) > 5:
            topics = add_unresolved_question(topics, topic_name, question)

    save_topics(topics)
    return topics, memory_ids


def research_url(url: str) -> dict:
    """
    Research a URL - fetch, process, and store.

    Returns:
        {
            "success": bool,
            "summary": str,
            "topic": str,
            "facts_stored": int,
            "questions": list[str],
            "error": str | None,
        }
    """
    # Fetch content
    content, error = fetch_url(url)
    if error:
        return {
            "success": False,
            "summary": "",
            "topic": "",
            "facts_stored": 0,
            "questions": [],
            "error": error,
        }

    # Process with Claude
    result = process_with_claude(content, url, "article")

    # Store results
    topics = load_topics()
    topics, memory_ids = store_research_results(result, url, topics)

    return {
        "success": True,
        "summary": result["summary"],
        "topic": result["topic"],
        "facts_stored": len(memory_ids),
        "questions": result["questions"],
        "error": None,
    }


def research_search(query: str) -> dict:
    """
    Research via web search - search, fetch top results, process, and store.

    Returns:
        {
            "success": bool,
            "summary": str,
            "topic": str,
            "facts_stored": int,
            "questions": list[str],
            "sources": list[str],
            "error": str | None,
        }
    """
    # Search the web
    results, error = search_web(query, num_results=3)
    if error:
        return {
            "success": False,
            "summary": "",
            "topic": "",
            "facts_stored": 0,
            "questions": [],
            "sources": [],
            "error": error,
        }

    # Combine search result snippets for initial processing
    combined = ""
    sources = []
    for r in results:
        combined += f"\n\n## {r['title']}\n{r['snippet']}\n"
        if r["url"]:
            sources.append(r["url"])

    # Process the combined snippets
    result = process_with_claude(combined, "web search", "search_results")

    # Store results
    topics = load_topics()
    source_str = f"search: {query}"
    topics, memory_ids = store_research_results(result, source_str, topics)

    return {
        "success": True,
        "summary": result["summary"],
        "topic": result["topic"],
        "facts_stored": len(memory_ids),
        "questions": result["questions"],
        "sources": sources,
        "error": None,
    }


def research_text(text: str) -> dict:
    """
    Research provided text - process and store.

    Returns:
        {
            "success": bool,
            "summary": str,
            "topic": str,
            "facts_stored": int,
            "questions": list[str],
            "error": str | None,
        }
    """
    if not text or len(text) < 20:
        return {
            "success": False,
            "summary": "",
            "topic": "",
            "facts_stored": 0,
            "questions": [],
            "error": "That's too short for me to learn from.",
        }

    # Limit text length
    if len(text) > 15000:
        text = text[:15000] + "\n\n[Content truncated...]"

    # Process with Claude
    result = process_with_claude(text, "provided by user", "text")

    # Store results
    topics = load_topics()
    topics, memory_ids = store_research_results(result, "user provided", topics)

    return {
        "success": True,
        "summary": result["summary"],
        "topic": result["topic"],
        "facts_stored": len(memory_ids),
        "questions": result["questions"],
        "error": None,
    }


def detect_research_intent(message: str) -> tuple[str | None, str]:
    """
    Detect if a message is a research request.

    Returns:
        Tuple of (intent type, extracted content)
        Intent types: "url", "search", "text", None
    """
    message_lower = message.lower().strip()

    # Check for URL
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    url_match = re.search(url_pattern, message)
    if url_match:
        # Check for trigger phrases
        url_triggers = ["read this", "look at this", "check this", "learn from", "read about"]
        if any(trigger in message_lower for trigger in url_triggers) or url_match:
            return "url", url_match.group()

    # Check for search intent
    search_triggers = [
        (r"(?:look up|search for|search|find out about|learn about|research)\s+(.+)", 1),
        (r"what (?:is|are|does|do)\s+(.+)\??", 1),
    ]
    for pattern, group in search_triggers:
        match = re.search(pattern, message_lower)
        if match:
            query = match.group(group).strip().rstrip("?")
            if len(query) > 2:
                return "search", query

    # Check for direct text learning
    text_triggers = [
        r"learn this[:\s]+(.+)",
        r"remember this[:\s]+(.+)",
        r"here'?s? (?:some )?(?:info|information)[:\s]+(.+)",
    ]
    for pattern in text_triggers:
        match = re.search(pattern, message_lower, re.DOTALL)
        if match:
            text = match.group(1).strip()
            if len(text) > 20:
                return "text", text

    return None, ""
