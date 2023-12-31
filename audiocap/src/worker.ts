/**
* Welcome to Cloudflare Workers! This is your first worker.
*
* - Run `npm run dev` in your terminal to start a development server
* - Open a browser tab at http://localhost:8787/ to see your worker in action
* - Run `npm run deploy` to publish your worker
*
* Learn more at https://developers.cloudflare.com/workers/
*/
import { Configuration, OpenAIApi } from "openai";
import fetchAdapter from "@haverstack/axios-fetch-adapter";

export interface Env {
    OPENAI_API_KEY: string,
    // Example binding to KV. Learn more at https://developers.cloudflare.com/workers/runtime-apis/kv/
    // MY_KV_NAMESPACE: KVNamespace;
    //
    // Example binding to Durable Object. Learn more at https://developers.cloudflare.com/workers/runtime-apis/durable-objects/
    // MY_DURABLE_OBJECT: DurableObjectNamespace;
    //
    // Example binding to R2. Learn more at https://developers.cloudflare.com/workers/runtime-apis/r2/
    // MY_BUCKET: R2Bucket;
    //
    // Example binding to a Service. Learn more at https://developers.cloudflare.com/workers/runtime-apis/service-bindings/
    // MY_SERVICE: Fetcher;
    //
    // Example binding to a Queue. Learn more at https://developers.cloudflare.com/queues/javascript-apis/
    // MY_QUEUE: Queue;
}

const project_names = ['Gamut', 'Suyan', 'Valuenex', 'Wavetable', 'Burrows', 'USACO', 'X-camp']

// const postprocessing_prompt = `
// You are a helpful assistant tasked with correcting mistakes in, removing filler words from, and organizing a transcription. Use these steps:

// STEP 1 - cleaning:
// Correct transcription mistakes by ensuring the names of the following projects are spelled correctly: ${project_names.join(', ')}. Remove filler words.

// STEP 2 - organizing:
// Make a bullet list of quotes from the transcript, exactly preserving the structure and voice of the original speaker. Always quote the transcript exactly. Keep all reflections, opinions, and feelings. Indent subpoints under headers and topic descriptions. Above all, capture all comments and emotions provided and use only the context provided.
// `

const postprocessing_prompt = `
You are a helpful assistant tasked with correcting mistakes in, removing filler words from, and organizing a transcription. Use these steps:

STEP 1 - cleaning:
Correct transcription mistakes by ensuring the names of the following projects are spelled correctly: ${project_names.join(', ')}. Remove filler words.

STEP 2 - organizing:
Make a bullet list of quotes from the transcript, exactly preserving the structure and voice of the original speaker. Always quote the transcript exactly. Keep all reflections, opinions, and feelings. Indent subpoints under headers and topic descriptions. Above all, capture all comments and emotions provided and use only the context provided.

Here is an example of the format you must follow:

EXAMPLE INPUT:
You are um, you're an agent that, like. An agent that transcribes audio. Because audio is, like, good at capturing, and whisper, um, and it turns out to be cheap.

EXAMPLE OUTPUT:
---
STEP 1:
You're an agent that transcribes audio. Because audio is good at capturing, and whisper turns out to be cheap.
---
STEP 2:
- "You're an agent that transcribes audio."
- "Becuase audio is good at capturing,"
- "and whisper turns out to be cheap."
---
`, parser = /(?:---\nSTEP 2:\n((?:.|\s)+)\n---)/

async function main(audio_file: File, req_metadata: any, env: Env) {
    // transcribe audio
    const [ transcript_res, audio_filesize ] = await (async () => {
        const transcription_fd = new FormData();
        const audio_as_blob = new Blob([audio_file], { type: audio_file.type });
        transcription_fd.append('file', audio_as_blob);
        transcription_fd.append('model', 'whisper-1');
        transcription_fd.append('prompt', '[PAUSE] ');

        const whisperResponse = await fetch('https://api.openai.com/v1/audio/transcriptions', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${env.OPENAI_API_KEY}`,
            },
            body: transcription_fd
        })
        // optm: give it pause tags to have it try to output pause tags?
        // optm: give it a list of names or toggl project names?
        return [ (await whisperResponse.json() as { text: string }).text, audio_as_blob.size ]
    })();


    // organize transcript
    const postprocess_res = await ( async() => {
        const configuration = new Configuration({
            apiKey: env.OPENAI_API_KEY,
            baseOptions: {
                adapter: fetchAdapter
            }
        });
        const openai = new OpenAIApi(configuration);
        const completion = await openai.createChatCompletion({
            // messages: [{ role: "system", content: "please say hello" }],
            messages: [
                { role: "system", content: postprocessing_prompt },
                { role: "user", content: transcript_res }
            ],
            model: "gpt-3.5-turbo",
            temperature: 0,
        });
        return completion.data;
    })();

    // parse the llm output
    // const postprocess_parsed = postprocess_res.choices[0].message?.content?.match(parser)?.[1]
    const postprocess_parsed: string | null = (() => {
        const SEARCH_FOR = '---\nSTEP 2:\n';
        let msg = postprocess_res.choices[0].message?.content?.trim()
        if (msg === undefined) return null;
        if (msg?.endsWith('---')) msg = msg.slice(0, -3)
        const beg_idx = msg?.indexOf(SEARCH_FOR);
        if (beg_idx !== undefined && beg_idx > 0) return msg?.slice(beg_idx + SEARCH_FOR.length)
        return null;
    })();

    const res = {
        final_answer: postprocess_parsed,
        input_stats: {
            filesize_mb: audio_filesize/1024/1024,
            metadata: req_metadata,
        },
        raw_transcript: transcript_res,
        postprocess_msg: postprocess_res,
    }
    return res;
}

async function sendEmail(destination_email: string, content_md: string) {
    // to set this up, you must create an spf 'record' on ur domain and a TXT record for mailchannels auth (https://support.mailchannels.com/hc/en-us/articles/16918954360845)
    return await fetch(new Request('https://api.mailchannels.net/tx/v1/send', {
        method: 'POST',
        headers: {
            'content-type': 'application/json',
        },
        body: JSON.stringify({
            personalizations: [
                {
                    to: [{ email: destination_email, name: 'Audiocap Burrows Inbox'}],
                },
            ],
            from: {
                email: 'noreply-audiocap@exr0n.com',
                name: 'Burrows Audiocap',
            },
            subject: 'Burrows Audiocap Transcript',
            content: [  // todo: render as markdown. but probs exceeds 10ms
                {
                    type: 'text/plain',
                    value: content_md,
                },
            ],
        }),
    }));
}

//optm: Replace partial thoughts with their completed successors.?
// todo: do filler word and repetition removal w/ linguistics?

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {
        if( request.method !== "POST" ) return new Response('Hi there!');

        const req_formdata = await request.formData();
        const keys = [ 'location', 'loc-long', 'loc-lat', 'loc-alt' ]
        const req_metadata = Object.fromEntries(keys.map(k => [k, req_formdata.get(k)]))
        const audio_file = (req_formdata.get('file')! as unknown as File);

        const start_time = Date.now()

        const destination_email = req_formdata.get('destination_email');
        if (audio_file.size < Math.pow(1024, 2) && destination_email !== null) {  // short enough that we can probably return early
            ctx.waitUntil((async () => {
                const res = await main(audio_file, req_metadata, env);
                const backup = res.postprocess_msg.choices[0].message?.content ?? res.raw_transcript
                const got = await sendEmail(destination_email, res.final_answer ?? backup);
                console.log('full email sent successfully', (Date.now()-start_time)/1000)
                console.log(await got.text(), got.statusText);
            })());
            return new Response("Please expect an email shortly.");
        }

        console.log("long file detected. beginning processing...")
        const res = await main(audio_file, req_metadata, env);
        if (destination_email !== null) await sendEmail(destination_email, JSON.stringify(res, null, 4));
        return new Response(JSON.stringify(res, null, 4), { status: 200 })
    },
};
