import argparse
import os
import openai
from youtube_transcript_api import YouTubeTranscriptApi
import tiktoken

enc = tiktoken.get_encoding("cl100k_base") # this is the tokenizer used by gpt-3.5-turbo
openai.api_key = "your_key"
max_tokens_risposta = 1000

def get_subtitles(youtube_url):
    try:
        # Get video id from url
        video_id = youtube_url.split("v=")[1]
        
        
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        transcript = transcript_list.find_transcript(['en', 'it'])

        captions = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'it'])
        subtitle_text = "\n".join([caption['text'] for caption in captions])
        return subtitle_text, transcript.language
    except Exception as e:
        print("Error:", e)
        return None

def create_digest(subtitles,current_model,language):
    if 'Italian' in language:
        prompt = f"Riassumi i seguenti sottotitoli:\n{subtitles}"
    else:
        prompt = f"Summarize the following subtitles:\n{subtitles}"
    response = openai.ChatCompletion.create(
        model=current_model,
        messages=[{"role": "system", "content": "You are a helpful assistant that summarizes subtitles."},
                  {"role": "user", "content": prompt}],
        max_tokens=max_tokens_risposta
    )
    digest = response.choices[0].message["content"].strip()
    return digest


def main():
    parser = argparse.ArgumentParser(description="Generate a digest from YouTube video subtitles")
    parser.add_argument("youtube_url", type=str, help="URL of the YouTube video")
    args = parser.parse_args()

    youtube_url = args.youtube_url
    subtitles, language = get_subtitles(youtube_url)
    # print(subtitles)
    
    
    
    

    
    if not subtitles:
        print('No subtitles available for the provided YouTube video')
        exit()
    
    
    token_number = len(enc.encode(subtitles))
    
    if token_number + max_tokens_risposta > 4000:
        current_model = "gpt-3.5-turbo-16k"
    else:
        current_model = "gpt-3.5-turbo"
    print(f"You are about to send a {current_model} API request with {len(enc.encode(subtitles))} tokens, press enter to proceed")
    input()
    
    digest = create_digest(subtitles,current_model,language)
    print("Generated Digest:\n", digest)

    # Save digest to a text file
    output_filename = "digest.txt"
    with open(output_filename, "a") as file:
        file.write('\n\n'+digest)
    print(f"Digest saved to {output_filename}")

if __name__ == "__main__":
    main()
