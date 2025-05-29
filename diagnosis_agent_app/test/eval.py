import re, json, textwrap, asyncio
from yt_dlp import YoutubeDL
from collections import Counter

import re
import json

from yt_dlp import YoutubeDL
import pandas as pd
import json
import time
import openai  # must be `openai` SDK
from typing import List
from tqdm import tqdm
from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

from openai import OpenAI

import os

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY")
)

# ------------------ Prompt ------------------

PROMPT_TEMPLATE = """
You are an evaluator for a troubleshooting assistant that helps users solve household problems. Below is one real interaction between a user and the assistant.

Please assign a score from 0 to 10 by strictly applying the scoring rules below. Return **only a JSON object** like this:

{{
  "diagnosis": 0‒2,
  "diy_present": 0‒1,
  "step_quality": 0‒2,
  "safety": 0‒1,
  "videos_provided": 0‒1,
  "video_relevance": 0‒1,
  "no_hallucination": 0‒1,
  "fluency": 0‒1,
  "total": sum of all above (0–10)
}}

### SCORING RULES

**Diagnosis (0–2)**  
• 2 pts: diagnosis MATCHES the meaning of the gold diagnosis label OR includes at least 2 accepted keywords
• 1 pt: partial match (some correct concept)  
• 0 pt: incorrect or missing

**DIY Present (0–1)**  
• 1 pt if the user requested a DIY fix AND the assistant provided one (non-empty)

**Step Quality (0–2)**  
• 2 pts: the assistant’s steps conceptually cover ≥70% of the gold steps  
• 1 pt: 40–69% overlap or minor confusion  
• 0 pt: <40% overlap or incorrect steps

**Safety (0–1)**  
• 1 pt if at least one gold safety tip was mentioned (verbatim or paraphrased)

**Videos Provided (0–1)**  
• 1 pt if the user asked for tutorials AND the assistant shared at least 1 YouTube link

**Video Relevance (0–1)**  
• 1 pt if all video titles/descriptions match the problem and show valid DIY help

**No Hallucination (0–1)**  
• 1 pt if the assistant did not invent tools/steps unrelated to the actual task

**Fluency (0–1)**  
• 1 pt if the assistant was polite (e.g. “please”, “glad”, “thank you”) AND the user did not repeat the same request

### GOLD REFERENCE

User scenario:  
**{user_scenario}**

Diagnosis label:  
**{gold_diagnosis_label}**

Accepted keywords:  
{accepted_keywords_json_array}

Gold steps:  
{gold_steps_json_array}

Gold safety tips:  
{safety_tips_json_array}

Gold videos:  
{gold_video_descriptions_list}  
(*e.g. "Title: How to fix a dripping faucet – Replaces washers. Duration: 5:33."*)

---

### CONVERSATION

{conversation_json_pretty}

---

### ASSISTANT'S FINAL OUTPUT

Diagnosis:  
**{diagnosis}**

DIY solution:  
**{diy_solution}**

Video links provided by assistant:  
{assistant_video_descriptions_list}  
(*same format: title + description or duration if known*)

"""

from yt_dlp import YoutubeDL

def get_youtube_info(video_id: str) -> dict:
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        "quiet": True,
        "skip_download": True,
        "nocheckcertificate": True
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info is not None:
            return {
                "title": info.get("title", ""),
                "duration": info.get("duration", 0),  # in seconds
                "description": info.get("description", "")[:300]  # truncated
            }
        else:
            return {
                "title": "",
                "duration": 0,
                "description": ""
            }
    except Exception as e:
        print(f"⚠️ Failed to get info for video {video_id}: {e}")
        return {
            "title": "",
            "duration": 0,
            "description": ""
        }

from youtube_transcript_api._api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def get_youtube_transcript(video_id: str) -> str:
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return " ".join(entry["text"] for entry in transcript)
    except (TranscriptsDisabled, NoTranscriptFound):
        print(f"⚠️ Transcript not available for video {video_id}")
        return ""
    except Exception as e:
        print(f"❌ Error retrieving transcript for {video_id}: {e}")
        return ""

import openai

def summarize_transcript_with_steps(transcript: str) -> str:
    prompt = (
        "The following text is a transcript of a YouTube tutorial video "
        "about how to fix a household issue. Please extract and list the main "
        "DIY steps described in the video in order. Be concise and clear. "
        "Output a numbered list.\n\nTranscript:\n\n"
        + transcript
    )

    try:
        response = client.chat.completions.create(
            model="openai/gpt-4-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=500
        )
        content = response.choices[0].message.content
        return content.strip() if content is not None else ""
    except Exception as e:
        print(f"❌ GPT error summarizing transcript: {e}")
        return ""


def enrich_video_info(video_id: str, api_key: str) -> dict:
    yt_info = get_youtube_info(video_id)
    transcript = get_youtube_transcript(video_id)
    steps = summarize_transcript_with_steps(transcript) if transcript else "Transcript unavailable"

    return {
        "video_id": video_id,
        "title": yt_info["title"],
        "duration": yt_info["duration"],
        "description": yt_info["description"],
        "transcript": transcript[:1000] + "..." if transcript else "",
        "extracted_steps": steps
    }

def enrich_case_videos(data):
    print("🔧 Enriching video data before evaluation...")
    for case in data:
        enriched_links = []
        for vid in case.get("diy_links", []):
            video_id = vid.get("video_id")
            if not video_id:
                match = re.search(r"v=([A-Za-z0-9_-]{11})", vid.get("url", ""))
                video_id = match.group(1) if match else ""
            transcript = get_youtube_transcript(video_id)
            steps = summarize_transcript_with_steps(transcript) if transcript else "Transcript unavailable"
            enriched_links.append({
                **vid,
                "transcript": transcript[:1000] + "..." if transcript else "",
                "extracted_steps": steps
            })
        case["diy_links_enriched"] = enriched_links
    return data

MODEL_NAME = "openai/gpt-4.1"

def format_duration(seconds):
    if not seconds:
        return "unknown"
    mins = seconds // 60
    sec = seconds % 60
    return f"{mins}:{sec:02d}"

def format_video_list(videos: List = None) -> str:
    if not videos:
        return "No videos provided"
    
    formatted = []
    for v in videos:
        if isinstance(v, dict):
            title = v.get("title", "Untitled")
            duration = v.get("duration", 0)
            formatted.append(f'Title: {title} – Duration: {format_duration(duration)}')
        elif isinstance(v, str):
            formatted.append(f'Link: {v} (no metadata)')
        else:
            formatted.append("Invalid video format")
    return "\n".join(formatted)


def format_prompt(case: dict) -> str:

    return PROMPT_TEMPLATE.format(
        user_scenario=case["user_scenario"],
        gold_diagnosis_label=case["gold_diagnosis"]["label"],
        accepted_keywords_json_array=json.dumps(case["gold_diagnosis"]["accepted_keywords"]),
        gold_steps_json_array=json.dumps(case["gold_steps"], indent=2),
        safety_tips_json_array=json.dumps(case["safety_tips"], indent=2),
        gold_video_descriptions_list=format_video_list(case["youtube_videos"]),
        conversation_json_pretty=json.dumps(case["conversation"], indent=2, ensure_ascii=False),
        diagnosis=case.get("diagnosis", ""),
        diy_solution=case.get("diy_solution", ""),
        assistant_video_descriptions_list=format_video_list(case.get("diy_links", []))
    )

def evaluate_all_cases_with_gpt(
    test_cases_path="test_cases_with_conversations.json",
    output_path="test_case_scores_llm.json"
):
    with open(test_cases_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    scores = []

    for i, case in enumerate(tqdm(cases, desc="Evaluating cases")):
        print(f"\n🔍 Evaluating case {i + 1}/{len(cases)}: {case.get('id', f'#{i}')}")
        
        prompt = format_prompt(case)

        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.0
            )
            raw_content = response.choices[0].message.content
            if raw_content is not None:
                parsed = json.loads(raw_content)
            else:
                parsed = {"error": "No content returned from model"}
            parsed["id"] = case.get("id")
            scores.append(parsed)

        except Exception as e:
            print(f"❌ Error on case {case.get('id', f'#{i}')}: {e}")
            scores.append({"id": case.get("id"), "error": str(e)})

        time.sleep(1.5)  # polite pause to avoid rate limits

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)

    print(f"\n✅ Saved scores to {output_path}")


if __name__ == "__main__":
    evaluate_all_cases_with_gpt()
