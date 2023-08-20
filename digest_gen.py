import argparse
import os
import openai
from youtube_transcript_api import YouTubeTranscriptApi

openai.api_key = "your_key"

def get_subtitles(youtube_url):
    try:
        # Get video id from url
        video_id = youtube_url.split("v=")[1]
        captions = YouTubeTranscriptApi.get_transcript(video_id)
        subtitle_text = "\n".join([caption['text'] for caption in captions])
        return subtitle_text
    except Exception as e:
        print("Error:", e)
        return None

def create_digest(subtitles):
    prompt = f"Summarize the following subtitles:\n{subtitles}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant that summarizes subtitles."},
                  {"role": "user", "content": prompt}],
        max_tokens=150
    )
    digest = response.choices[0].message["content"].strip()
    return digest


def main():
    parser = argparse.ArgumentParser(description="Generate a digest from YouTube video subtitles")
    parser.add_argument("youtube_url", type=str, help="URL of the YouTube video")
    args = parser.parse_args()

    youtube_url = args.youtube_url
    subtitles = get_subtitles(youtube_url)


    if subtitles:
        digest = create_digest(subtitles)
        print("Generated Digest:\n", digest)

        # Save digest to a text file
        output_filename = "digest.txt"
        with open(output_filename, "w") as file:
            file.write(digest)
        print(f"Digest saved to {output_filename}")
    else:
        print("No subtitles available for the provided YouTube video.")

if __name__ == "__main__":
    main()