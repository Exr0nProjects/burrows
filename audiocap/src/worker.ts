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

const postprocessing_prompt = `
You are a helpful assistant tasked with correcting mistakes in, removing filler words from, and organizing a transcription. Use these steps:

STEP 1 - cleaning:
Correct transcription mistakes by ensuring the names of the following projects are spelled correctly: ${project_names.join(', ')}.  Remove filler words.

STEP 2 - organizing:
Convert the transcript to bullet point form, exactly preserving the structure and voice of the original speaker. Always quote the transcript exactly. Keep all reflections, opinions, and feelings. Indent subpoints under headers and topic descriptions. Above all, capture all comments and emotions provided and use only the context provided.
`
//optm: Replace partial thoughts with their completed successors.?

export default {
    async fetch(request: Request, env: Env, ctx: ExecutionContext): Promise<Response> {

        const req_formdata = await request.formData();
        const keys = [ 'location', 'loc-long', 'loc-lat', 'loc-alt' ]
        const req_metadata = Object.fromEntries(keys.map(k => [k, req_formdata.get(k)]))

        // transcribe audio
        const [ transcript_res, audio_filesize ] = await (async () => {
            const transcription_fd = new FormData();
            const audio_file = (req_formdata.get('file')! as unknown as File);
            const audio_as_blob = new Blob([audio_file], { type: audio_file.type });
            transcription_fd.append('file', audio_as_blob);
            transcription_fd.append('model', 'whisper-1');

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


        // Return the response
        const res = {
            input_stats: {
                filesize_kb: audio_filesize/1024,
                metadata: req_metadata,
            },
            raw_transcript: transcript_res,
            postprocess_msg: postprocess_res
        }
        return new Response(JSON.stringify(res, null, 4), { status: 200 })
    },
};
